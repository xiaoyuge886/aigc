"""
反馈收集器服务

核心职责：
1. 收集用户反馈（显式反馈：点赞/点踩/纠正/重新生成）
2. 收集隐式反馈（重新提问、修改问题等）
3. 更新会话级别偏好
4. 触发用户级别偏好更新（异步批量处理）
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from services.database import DatabaseService
from models.database import (
    UserFeedbackDB, SessionPreferencesDB, UserBehaviorStatsDB
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """反馈收集器"""
    
    def __init__(self, db_service: DatabaseService):
        """
        初始化反馈收集器
        
        Args:
            db_service: 数据库服务实例
        """
        self.db_service = db_service
    
    async def collect_feedback(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        message_id: Optional[int] = None,
        conversation_turn_id: Optional[str] = None,
        feedback_type: str = "like",  # 'like' | 'dislike' | 'correct' | 'regenerate' | 'implicit_retry' | 'implicit_modify'
        feedback_data: Optional[Dict[str, Any]] = None,
        user_prompt: Optional[str] = None,
        assistant_response: Optional[str] = None,
        scenario_ids: Optional[list] = None,
    ) -> UserFeedbackDB:
        """
        收集用户反馈
        
        Args:
            user_id: 用户ID（可选，匿名用户可以为None）
            session_id: 会话ID（可选）
            message_id: 消息ID（可选）
            conversation_turn_id: 对话轮次ID（可选）
            feedback_type: 反馈类型
            feedback_data: 反馈数据（如纠正内容、原因等）
            user_prompt: 用户问题（可选，用于上下文）
            assistant_response: AI回答（可选，用于上下文）
            scenario_ids: 使用的场景ID列表（可选）
            
        Returns:
            UserFeedbackDB: 创建的反馈记录
        """
        try:
            async with self.db_service.async_session() as session:
                # 创建反馈记录
                feedback = UserFeedbackDB(
                    user_id=user_id,
                    session_id=session_id,
                    message_id=message_id,
                    conversation_turn_id=conversation_turn_id,
                    feedback_type=feedback_type,
                    feedback_data=feedback_data or {},
                    user_prompt=user_prompt,
                    assistant_response=assistant_response,
                    scenario_ids=json.dumps(scenario_ids) if scenario_ids else None,
                    created_at=datetime.utcnow()
                )
                
                session.add(feedback)
                await session.commit()
                await session.refresh(feedback)
                
                logger.info(
                    f"[FeedbackCollector] 收集反馈成功: user_id={user_id}, "
                    f"session_id={session_id}, type={feedback_type}"
                )
                
                # 实时更新会话级别偏好
                if session_id:
                    await self._update_session_preferences(
                        session, session_id, feedback_type, feedback_data
                    )
                
                # 更新用户行为统计
                if user_id:
                    await self._update_user_behavior_stats(
                        session, user_id, feedback_type
                    )
                
                await session.commit()
                
                return feedback
                
        except Exception as e:
            logger.error(f"[FeedbackCollector] 收集反馈失败: {e}", exc_info=True)
            raise
    
    async def _update_session_preferences(
        self,
        session: AsyncSession,
        session_id: str,
        feedback_type: str,
        feedback_data: Optional[Dict[str, Any]] = None
    ):
        """
        实时更新会话级别偏好
        
        Args:
            session: 数据库会话
            session_id: 会话ID
            feedback_type: 反馈类型
            feedback_data: 反馈数据
        """
        try:
            # 获取或创建会话偏好记录
            stmt = select(SessionPreferencesDB).where(
                SessionPreferencesDB.session_id == session_id
            )
            result = await session.execute(stmt)
            session_pref = result.scalar_one_or_none()
            
            if not session_pref:
                session_pref = SessionPreferencesDB(
                    session_id=session_id,
                    preferences={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(session_pref)
            
            # 更新偏好（简单累加统计）
            prefs = session_pref.preferences if isinstance(session_pref.preferences, dict) else {}
            
            # 更新反馈统计
            if "feedback_stats" not in prefs:
                prefs["feedback_stats"] = {}
            
            stats = prefs["feedback_stats"]
            stats[feedback_type] = stats.get(feedback_type, 0) + 1
            stats["total"] = stats.get("total", 0) + 1
            
            # 如果有反馈数据，保存关键信息
            if feedback_data:
                if "recent_feedback" not in prefs:
                    prefs["recent_feedback"] = []
                
                prefs["recent_feedback"].append({
                    "type": feedback_type,
                    "data": feedback_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # 只保留最近10条反馈
                if len(prefs["recent_feedback"]) > 10:
                    prefs["recent_feedback"] = prefs["recent_feedback"][-10:]
            
            session_pref.preferences = prefs
            session_pref.updated_at = datetime.utcnow()
            
            logger.debug(
                f"[FeedbackCollector] 更新会话偏好: session_id={session_id}, "
                f"type={feedback_type}"
            )
            
        except Exception as e:
            logger.warning(f"[FeedbackCollector] 更新会话偏好失败: {e}")
            # 不影响主流程，继续执行
    
    async def _update_user_behavior_stats(
        self,
        session: AsyncSession,
        user_id: int,
        feedback_type: str
    ):
        """
        更新用户行为统计
        
        Args:
            session: 数据库会话
            user_id: 用户ID
            feedback_type: 反馈类型
        """
        try:
            # 获取或创建用户行为统计记录
            stmt = select(UserBehaviorStatsDB).where(
                UserBehaviorStatsDB.user_id == user_id
            )
            result = await session.execute(stmt)
            stats = result.scalar_one_or_none()
            
            if not stats:
                stats = UserBehaviorStatsDB(
                    user_id=user_id,
                    total_sessions=0,
                    total_messages=0,
                    total_feedback=0,
                    like_count=0,
                    dislike_count=0,
                    scenario_usage={},
                    question_types={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(stats)
            
            # 更新统计
            stats.total_feedback = (stats.total_feedback or 0) + 1
            
            if feedback_type == "like":
                stats.like_count = (stats.like_count or 0) + 1
            elif feedback_type == "dislike":
                stats.dislike_count = (stats.dislike_count or 0) + 1
            
            stats.updated_at = datetime.utcnow()
            
            logger.debug(
                f"[FeedbackCollector] 更新用户行为统计: user_id={user_id}, "
                f"type={feedback_type}"
            )
            
        except Exception as e:
            logger.warning(f"[FeedbackCollector] 更新用户行为统计失败: {e}")
            # 不影响主流程，继续执行
    
    async def collect_implicit_feedback(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        implicit_type: str,  # 'retry' | 'modify' | 'regenerate'
        original_prompt: Optional[str] = None,
        modified_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        收集隐式反馈（用户重新提问、修改问题等）
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            implicit_type: 隐式反馈类型
            original_prompt: 原始问题
            modified_prompt: 修改后的问题
            context: 上下文信息
        """
        feedback_type = f"implicit_{implicit_type}"
        feedback_data = {
            "original_prompt": original_prompt,
            "modified_prompt": modified_prompt,
            "context": context or {}
        }
        
        return await self.collect_feedback(
            user_id=user_id,
            session_id=session_id,
            feedback_type=feedback_type,
            feedback_data=feedback_data,
            user_prompt=original_prompt
        )
