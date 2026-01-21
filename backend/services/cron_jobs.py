"""
定时任务服务

核心职责：
1. 用户级别偏好学习（定时任务，批量分析）
2. 定期清理过期数据
3. 定期更新用户行为统计
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from services.database import DatabaseService
from services.preference_learner import PreferenceLearner
from services.agent_service import AgentService
from models.database import UserDB, UserFeedbackDB
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class CronJobs:
    """定时任务管理器"""
    
    def __init__(self, db_service: DatabaseService):
        """
        初始化定时任务管理器
        
        Args:
            db_service: 数据库服务实例
        """
        self.db_service = db_service
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self):
        """启动所有定时任务"""
        if self._running:
            logger.warning("[CronJobs] 定时任务已经在运行")
            return
        
        self._running = True
        
        # 启动用户偏好学习定时任务（每小时运行一次）
        task1 = asyncio.create_task(self._user_preference_learning_loop())
        self._tasks.append(task1)
        
        logger.info("[CronJobs] 定时任务已启动")
    
    async def stop(self):
        """停止所有定时任务"""
        self._running = False
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("[CronJobs] 定时任务已停止")
    
    async def _user_preference_learning_loop(self):
        """
        用户偏好学习定时任务循环
        
        每小时运行一次，批量分析用户偏好
        """
        interval_seconds = 3600  # 1小时
        
        while self._running:
            try:
                await self.batch_learn_user_preferences()
                logger.info(f"[CronJobs] 用户偏好学习任务完成，下次运行时间: {datetime.utcnow() + timedelta(seconds=interval_seconds)}")
            except Exception as e:
                logger.error(f"[CronJobs] 用户偏好学习任务失败: {e}", exc_info=True)
            
            # 等待指定时间
            await asyncio.sleep(interval_seconds)
    
    async def batch_learn_user_preferences(
        self,
        min_feedback_count: int = 5,
        max_users_per_batch: int = 10,
        agent_service: Optional[AgentService] = None
    ):
        """
        批量学习用户偏好
        
        只分析有足够反馈数据的用户（避免浪费资源）
        
        Args:
            min_feedback_count: 最小反馈数量（只有反馈数>=此值的用户才会被分析）
            max_users_per_batch: 每批最多分析的用户数（避免一次性处理太多）
            agent_service: Agent服务（用于调用模型分析，可选）
        """
        if not agent_service:
            logger.warning("[CronJobs] 未提供agent_service，跳过用户偏好学习")
            return
        
        try:
            preference_learner = PreferenceLearner(self.db_service)
            
            # 1. 获取需要分析的用户列表（有足够反馈数据的用户）
            async with self.db_service.async_session() as session:
                # 查询有足够反馈的用户
                stmt = (
                    select(UserDB.id, func.count(UserFeedbackDB.id).label('feedback_count'))
                    .join(UserFeedbackDB, UserDB.id == UserFeedbackDB.user_id)
                    .group_by(UserDB.id)
                    .having(func.count(UserFeedbackDB.id) >= min_feedback_count)
                    .limit(max_users_per_batch)
                )
                result = await session.execute(stmt)
                users_to_analyze = result.all()
            
            if not users_to_analyze:
                logger.debug("[CronJobs] 没有需要分析的用户（反馈数据不足）")
                return
            
            logger.info(
                f"[CronJobs] 开始批量分析用户偏好: "
                f"用户数={len(users_to_analyze)}, "
                f"最小反馈数={min_feedback_count}"
            )
            
            # 2. 批量分析用户偏好
            success_count = 0
            fail_count = 0
            
            for user_id, feedback_count in users_to_analyze:
                try:
                    # 强制刷新偏好（忽略缓存）
                    preferences = await preference_learner.get_user_preferences(
                        user_id=user_id,
                        agent_service=agent_service,
                        force_refresh=True
                    )
                    
                    if preferences:
                        success_count += 1
                        logger.debug(
                            f"[CronJobs] 用户 {user_id} 偏好分析成功 "
                            f"(反馈数: {feedback_count})"
                        )
                    else:
                        fail_count += 1
                        logger.warning(
                            f"[CronJobs] 用户 {user_id} 偏好分析失败 "
                            f"(反馈数: {feedback_count})"
                        )
                    
                    # 避免频繁调用模型，每个用户之间稍作延迟
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(
                        f"[CronJobs] 用户 {user_id} 偏好分析异常: {e}",
                        exc_info=True
                    )
                    # 继续处理下一个用户
                    continue
            
            logger.info(
                f"[CronJobs] 批量用户偏好学习完成: "
                f"成功={success_count}, 失败={fail_count}, "
                f"总计={len(users_to_analyze)}"
            )
            
        except Exception as e:
            logger.error(f"[CronJobs] 批量用户偏好学习失败: {e}", exc_info=True)
            raise
    
    async def run_user_preference_learning_now(
        self,
        user_ids: Optional[List[int]] = None,
        agent_service: Optional[AgentService] = None
    ):
        """
        立即运行用户偏好学习（手动触发）
        
        Args:
            user_ids: 要分析的用户ID列表（如果为None，则分析所有符合条件的用户）
            agent_service: Agent服务
        """
        if not agent_service:
            logger.warning("[CronJobs] 未提供agent_service，无法运行用户偏好学习")
            return
        
        try:
            preference_learner = PreferenceLearner(self.db_service)
            
            if user_ids:
                # 分析指定用户
                for user_id in user_ids:
                    try:
                        await preference_learner.get_user_preferences(
                            user_id=user_id,
                            agent_service=agent_service,
                            force_refresh=True
                        )
                        logger.info(f"[CronJobs] 用户 {user_id} 偏好学习完成")
                    except Exception as e:
                        logger.error(f"[CronJobs] 用户 {user_id} 偏好学习失败: {e}")
            else:
                # 批量分析所有符合条件的用户
                await self.batch_learn_user_preferences(agent_service=agent_service)
                
        except Exception as e:
            logger.error(f"[CronJobs] 立即运行用户偏好学习失败: {e}", exc_info=True)
            raise
