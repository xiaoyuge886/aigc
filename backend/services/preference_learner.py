"""
智能偏好学习引擎

核心设计原则：
1. 模型驱动：使用模型智能提取用户偏好，不依赖硬编码规则
2. 数据摘要：只加载关键数据，不加载所有历史数据
3. 缓存机制：使用数据摘要hash判断是否需要重新分析
4. 分级学习：用户级别（长期偏好）+ Session级别（临时偏好）
"""
import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from services.database import DatabaseService
from models.database import (
    UserFeedbackDB, UserPreferencesCacheDB, SessionPreferencesDB,
    UserBehaviorStatsDB, MessageDB, SessionDB
)
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.agent_service import AgentService

logger = logging.getLogger(__name__)


class PreferenceLearner:
    """智能偏好学习引擎 - 使用模型智能提取"""
    
    def __init__(self, db_service: DatabaseService):
        """
        初始化偏好学习器
        
        Args:
            db_service: 数据库服务实例
        """
        self.db_service = db_service
    
    async def get_user_data_summary(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户数据摘要（只加载关键信息，不是所有数据）
        
        只加载：
        - 最近N条反馈（如最近50条）
        - 场景使用统计（聚合数据）
        - 最近N个问题类型（如最近100个问题的类型）
        - 反馈关键词（从反馈中提取的关键词）
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户数据摘要
        """
        try:
            async with self.db_service.async_session() as session:
                # 1. 获取最近50条反馈
                stmt = select(UserFeedbackDB).where(
                    UserFeedbackDB.user_id == user_id
                ).order_by(desc(UserFeedbackDB.created_at)).limit(50)
                result = await session.execute(stmt)
                recent_feedback = result.scalars().all()
                
                feedback_list = []
                for fb in recent_feedback:
                    feedback_list.append({
                        "type": fb.feedback_type,
                        "data": fb.feedback_data or {},
                        "created_at": fb.created_at.isoformat() if fb.created_at else None
                    })
                
                # 2. 获取场景使用统计
                stats_stmt = select(UserBehaviorStatsDB).where(
                    UserBehaviorStatsDB.user_id == user_id
                )
                stats_result = await session.execute(stats_stmt)
                stats = stats_result.scalar_one_or_none()
                
                scenario_stats = {}
                if stats and stats.scenario_usage:
                    scenario_stats = stats.scenario_usage if isinstance(stats.scenario_usage, dict) else {}
                
                # 3. 获取问题类型统计
                question_types = {}
                if stats and stats.question_types:
                    question_types = stats.question_types if isinstance(stats.question_types, dict) else {}
                
                # 4. 获取用户消息统计（用于问题类型分析）
                message_stmt = select(func.count(MessageDB.id)).where(
                    MessageDB.session_id.in_(
                        select(SessionDB.session_id).where(SessionDB.user_id == user_id)
                    ),
                    MessageDB.role == "user"
                )
                message_result = await session.execute(message_stmt)
                total_messages = message_result.scalar() or 0
                
                # 5. 获取会话统计
                session_stmt = select(func.count(SessionDB.id)).where(
                    SessionDB.user_id == user_id
                )
                session_result = await session.execute(session_stmt)
                total_sessions = session_result.scalar() or 0
                
                # 6. 提取反馈关键词（从反馈数据中提取）
                feedback_keywords = self._extract_feedback_keywords(recent_feedback)
                
                summary = {
                    'recent_feedback': feedback_list,
                    'scenario_stats': scenario_stats,
                    'question_types': question_types,
                    'feedback_keywords': feedback_keywords,
                    'total_sessions': total_sessions,
                    'total_messages': total_messages,
                    'like_count': stats.like_count if stats else 0,
                    'dislike_count': stats.dislike_count if stats else 0,
                }
                
                logger.debug(
                    f"[PreferenceLearner] 获取用户数据摘要: user_id={user_id}, "
                    f"反馈数={len(feedback_list)}, 会话数={total_sessions}"
                )
                
                return summary
                
        except Exception as e:
            logger.error(f"[PreferenceLearner] 获取用户数据摘要失败: {e}", exc_info=True)
            # 返回空摘要，不影响主流程
            return {
                'recent_feedback': [],
                'scenario_stats': {},
                'question_types': {},
                'feedback_keywords': [],
                'total_sessions': 0,
                'total_messages': 0,
                'like_count': 0,
                'dislike_count': 0,
            }
    
    def _extract_feedback_keywords(self, feedback_list: List[UserFeedbackDB]) -> List[str]:
        """
        从反馈中提取关键词
        
        Args:
            feedback_list: 反馈列表
            
        Returns:
            List[str]: 关键词列表
        """
        keywords = []
        for fb in feedback_list:
            if fb.feedback_data and isinstance(fb.feedback_data, dict):
                # 从反馈数据中提取关键词
                if "reason" in fb.feedback_data:
                    reason = str(fb.feedback_data["reason"]).lower()
                    # 简单的关键词提取（可以根据需要改进）
                    if "详细" in reason or "详细" in reason:
                        keywords.append("偏好详细回答")
                    if "简洁" in reason or "简短" in reason:
                        keywords.append("偏好简洁回答")
                    if "专业" in reason:
                        keywords.append("偏好专业风格")
                    if "轻松" in reason or "友好" in reason:
                        keywords.append("偏好轻松风格")
        
        # 去重并返回
        return list(set(keywords))
    
    def _hash_summary(self, summary: Dict[str, Any]) -> str:
        """
        计算数据摘要的hash值
        
        Args:
            summary: 数据摘要
            
        Returns:
            str: hash值
        """
        # 将摘要转换为JSON字符串（排序以确保一致性）
        summary_str = json.dumps(summary, sort_keys=True, ensure_ascii=False)
        # 计算SHA256 hash
        return hashlib.sha256(summary_str.encode('utf-8')).hexdigest()
    
    async def get_user_preferences(
        self,
        user_id: int,
        agent_service: Optional["AgentService"] = None,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户偏好（带缓存）
        
        核心：检查缓存，如果数据摘要没变化，直接返回缓存结果
        
        Args:
            user_id: 用户ID
            agent_service: Agent服务（用于调用模型分析，可选）
            force_refresh: 是否强制刷新（忽略缓存）
            
        Returns:
            Optional[Dict[str, Any]]: 用户偏好，如果无法获取则返回None
        """
        try:
            # 1. 获取数据摘要
            summary = await self.get_user_data_summary(user_id)
            summary_hash = self._hash_summary(summary)
            
            # 2. 检查缓存（如果不强制刷新）
            if not force_refresh:
                async with self.db_service.async_session() as session:
                    stmt = select(UserPreferencesCacheDB).where(
                        UserPreferencesCacheDB.user_id == user_id
                    )
                    result = await session.execute(stmt)
                    cache = result.scalar_one_or_none()
                    
                    if cache and cache.data_summary_hash == summary_hash:
                        logger.debug(
                            f"[PreferenceLearner] 使用缓存偏好: user_id={user_id}"
                        )
                        return cache.preferences if isinstance(cache.preferences, dict) else {}
            
            # 3. 如果没有缓存或数据有变化，使用模型分析（如果提供了agent_service）
            if agent_service:
                preferences = await self._extract_preferences_with_model(
                    summary, agent_service
                )
                
                # 4. 保存到缓存
                await self._save_preferences_cache(user_id, summary_hash, preferences)
                
                return preferences
            else:
                # 如果没有提供agent_service，返回空偏好或缓存值
                logger.warning(
                    f"[PreferenceLearner] 未提供agent_service，无法分析用户偏好: user_id={user_id}"
                )
                return {}
                
        except Exception as e:
            logger.error(f"[PreferenceLearner] 获取用户偏好失败: {e}", exc_info=True)
            return None
    
    async def _extract_preferences_with_model(
        self,
        summary: Dict[str, Any],
        agent_service: "AgentService"
    ) -> Dict[str, Any]:
        """
        使用模型智能提取用户偏好
        
        让模型分析数据摘要，提取偏好和规则
        
        Args:
            summary: 用户数据摘要
            agent_service: Agent服务（用于调用模型）
            
        Returns:
            Dict[str, Any]: 用户偏好
        """
        try:
            # 构建分析prompt
            analysis_prompt = f"""请分析以下用户数据，提取用户的偏好和习惯：

## 用户数据摘要

### 反馈数据（最近{len(summary.get('recent_feedback', []))}条）
{self._format_feedback(summary.get('recent_feedback', []))}

### 场景使用统计
{self._format_scenario_stats(summary.get('scenario_stats', {}))}

### 问题类型统计
{self._format_question_types(summary.get('question_types', {}))}

### 反馈关键词
{', '.join(summary.get('feedback_keywords', []))}

### 总体统计
- 总会话数: {summary.get('total_sessions', 0)}
- 总消息数: {summary.get('total_messages', 0)}
- 点赞数: {summary.get('like_count', 0)}
- 点踩数: {summary.get('dislike_count', 0)}

## 分析任务

请从以上数据中提取：
1. **常用场景偏好**：用户最常用哪些场景？为什么？
2. **回答风格偏好**：用户偏好详细回答还是简洁回答？专业风格还是轻松风格？
3. **问题类型模式**：用户经常问什么类型的问题？
4. **从反馈中学习的规则**：从用户的反馈和纠正中，总结出哪些规则？（如：用户不喜欢过于详细的技术细节、用户偏好用图表展示数据等）
5. **工作模式**：用户的工作模式是什么？（如：经常做数据分析、经常做文本审校等）

请以JSON格式返回分析结果，格式如下：
{{
    "preferred_scenarios": ["场景1", "场景2"],
    "preferred_style": "detailed|concise|professional|casual",
    "common_question_types": ["类型1", "类型2"],
    "learned_rules": ["规则1", "规则2"],
    "work_pattern": "工作模式描述",
    "reasoning": "分析推理过程（简要）"
}}

如果数据不足，请返回合理的默认值。"""
            
            # 调用模型分析
            response_text = ""
            async for msg in agent_service.query_once(
                prompt=analysis_prompt,
                model="sonnet"  # 使用sonnet进行智能分析
            ):
                from models.schemas import AssistantMessage
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if block.type == "text":
                            response_text += block.text
            
            # 解析模型返回的JSON
            try:
                # 尝试提取JSON部分（模型可能返回markdown格式）
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                preferences_data = json.loads(response_text)
                
                logger.info(
                    f"[PreferenceLearner] 模型分析完成，提取到偏好: "
                    f"scenarios={len(preferences_data.get('preferred_scenarios', []))}, "
                    f"style={preferences_data.get('preferred_style', 'unknown')}"
                )
                
                return preferences_data
                
            except json.JSONDecodeError as e:
                logger.warning(
                    f"[PreferenceLearner] 模型返回的JSON解析失败: {e}, "
                    f"response: {response_text[:200]}"
                )
                # 返回默认偏好
                return {
                    "preferred_scenarios": [],
                    "preferred_style": "detailed",
                    "common_question_types": [],
                    "learned_rules": [],
                    "work_pattern": "",
                    "reasoning": "数据不足或解析失败"
                }
                
        except Exception as e:
            logger.error(f"[PreferenceLearner] 模型分析失败: {e}", exc_info=True)
            # 返回默认偏好
            return {
                "preferred_scenarios": [],
                "preferred_style": "detailed",
                "common_question_types": [],
                "learned_rules": [],
                "work_pattern": "",
                "reasoning": f"分析失败: {str(e)}"
            }
    
    def _format_feedback(self, feedback_list: List[Dict[str, Any]]) -> str:
        """格式化反馈数据"""
        if not feedback_list:
            return "暂无反馈数据"
        
        lines = []
        for i, fb in enumerate(feedback_list[:20], 1):  # 只显示最近20条
            fb_type = fb.get("type", "unknown")
            lines.append(f"{i}. {fb_type}: {json.dumps(fb.get('data', {}), ensure_ascii=False)}")
        
        return "\n".join(lines)
    
    def _format_scenario_stats(self, scenario_stats: Dict[str, int]) -> str:
        """格式化场景使用统计"""
        if not scenario_stats:
            return "暂无场景使用数据"
        
        lines = []
        sorted_stats = sorted(scenario_stats.items(), key=lambda x: x[1], reverse=True)
        for scenario_id, count in sorted_stats[:10]:  # 只显示前10个
            lines.append(f"- {scenario_id}: {count}次")
        
        return "\n".join(lines) if lines else "暂无场景使用数据"
    
    def _format_question_types(self, question_types: Dict[str, int]) -> str:
        """格式化问题类型统计"""
        if not question_types:
            return "暂无问题类型数据"
        
        lines = []
        sorted_types = sorted(question_types.items(), key=lambda x: x[1], reverse=True)
        for qtype, count in sorted_types[:10]:  # 只显示前10个
            lines.append(f"- {qtype}: {count}次")
        
        return "\n".join(lines) if lines else "暂无问题类型数据"
    
    async def _save_preferences_cache(
        self,
        user_id: int,
        summary_hash: str,
        preferences: Dict[str, Any]
    ):
        """
        保存偏好到缓存
        
        Args:
            user_id: 用户ID
            summary_hash: 数据摘要hash
            preferences: 用户偏好
        """
        try:
            async with self.db_service.async_session() as session:
                stmt = select(UserPreferencesCacheDB).where(
                    UserPreferencesCacheDB.user_id == user_id
                )
                result = await session.execute(stmt)
                cache = result.scalar_one_or_none()
                
                if cache:
                    cache.data_summary_hash = summary_hash
                    cache.preferences = preferences
                    cache.updated_at = datetime.utcnow()
                else:
                    cache = UserPreferencesCacheDB(
                        user_id=user_id,
                        data_summary_hash=summary_hash,
                        preferences=preferences,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(cache)
                
                await session.commit()
                logger.debug(f"[PreferenceLearner] 保存偏好缓存: user_id={user_id}")
                
        except Exception as e:
            logger.warning(f"[PreferenceLearner] 保存偏好缓存失败: {e}")
            # 不影响主流程
    
    async def get_session_preferences(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取会话偏好
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话偏好
        """
        try:
            async with self.db_service.async_session() as session:
                stmt = select(SessionPreferencesDB).where(
                    SessionPreferencesDB.session_id == session_id
                )
                result = await session.execute(stmt)
                session_pref = result.scalar_one_or_none()
                
                if session_pref:
                    return session_pref.preferences if isinstance(session_pref.preferences, dict) else {}
                else:
                    return {}
                    
        except Exception as e:
            logger.warning(f"[PreferenceLearner] 获取会话偏好失败: {e}")
            return {}
