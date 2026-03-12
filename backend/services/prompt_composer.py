"""
Prompt组合器服务

核心设计原则:
1. 简单直接 - 只组合基础prompt,能力包由 SDK plugins 参数处理
2. 完整的默认配置体系 - 零配置可用,默认系统prompt
3. 渐进式配置 - Layer 0(默认) → Layer 1(用户) → Layer 2(会话)

职责:
1. 组合各层级的prompt(系统默认 + 用户自定义 + 会话自定义)
2. 能力包通过 SDK plugins 参数传递,不在 prompt 中处理
"""
from typing import List, Dict, Optional
import json
import logging

from services.database import DatabaseService
from services.default_config import DefaultConfig
from services.preference_learner import PreferenceLearner
from services.prompt_evolver import PromptEvolver
from models.database import (
    UserScenarioConfigDB,
    SessionScenarioConfigDB,
)
from sqlalchemy import select
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.agent_service import AgentService

logger = logging.getLogger(__name__)


class PromptComposer:
    """Prompt组合器 - 简单直接的prompt组合"""

    def __init__(self, db_service: DatabaseService):
        """
        初始化Prompt组合器

        Args:
            db_service: 数据库服务实例
        """
        self.db_service = db_service
        self.preference_learner = PreferenceLearner(db_service)
        self.prompt_evolver = PromptEvolver()

    async def compose_base_prompt(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        组合基础prompt(系统默认 + 用户自定义 + 会话自定义)

        注意: 能力包相关的内容通过 SDK plugins 参数传递,不在 prompt 中处理

        Args:
            user_id: 用户ID(可选)
            session_id: 会话ID(可选)

        Returns:
            str: 组合后的系统prompt
        """
        # 1. 获取默认系统prompt
        base_prompt = await DefaultConfig.get_default_system_prompt_with_db(
            available_scenarios=[],
            db_service=self.db_service
        )

        # 2. 添加用户自定义prompt
        user_custom_prompt = await self._get_user_custom_prompt(user_id)
        if user_custom_prompt:
            base_prompt = f"{base_prompt}\n\n## 用户自定义规则\n\n{user_custom_prompt}"

        # 3. 添加会话自定义prompt
        session_custom_prompt = await self._get_session_custom_prompt(session_id)
        if session_custom_prompt:
            base_prompt = f"{base_prompt}\n\n## 会话级调整\n\n{session_custom_prompt}"

        logger.debug(
            f"[PromptComposer] 组合基础prompt完成: user_id={user_id}, session_id={session_id}"
        )

        return base_prompt

    async def compose_evolved_prompt(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        agent_service: Optional["AgentService"] = None,
        include_evolution: bool = True,
    ) -> str:
        """
        组合包含进化层的完整prompt(基础prompt + 用户偏好 + 会话偏好)

        Args:
            user_id: 用户ID(可选)
            session_id: 会话ID(可选)
            agent_service: Agent服务(用于调用模型分析偏好,可选)
            include_evolution: 是否包含进化层(默认True)

        Returns:
            str: 组合后的完整系统prompt(包含进化层)
        """
        # 1. 组合基础prompt
        base_prompt = await self.compose_base_prompt(
            user_id=user_id,
            session_id=session_id,
        )

        # 2. 如果不包含进化层,直接返回基础prompt
        if not include_evolution:
            return base_prompt

        # 3. 加载用户偏好(如果提供了agent_service)
        user_preferences = None
        if user_id and agent_service:
            try:
                user_preferences = await self.preference_learner.get_user_preferences(
                    user_id=user_id,
                    agent_service=agent_service,
                    force_refresh=False
                )
            except Exception as e:
                logger.warning(f"[PromptComposer] 加载用户偏好失败: {e}")

        # 4. 加载会话偏好
        session_preferences = None
        if session_id:
            try:
                session_preferences = await self.preference_learner.get_session_preferences(
                    session_id=session_id
                )
            except Exception as e:
                logger.warning(f"[PromptComposer] 加载会话偏好失败: {e}")

        # 5. 进化prompt(融入偏好)
        evolved_prompt = self.prompt_evolver.evolve_prompt(
            base_prompt=base_prompt,
            user_preferences=user_preferences,
            session_preferences=session_preferences
        )

        return evolved_prompt

    async def _get_user_scenario_config(
        self,
        user_id: int
    ) -> Optional[UserScenarioConfigDB]:
        """获取用户配置"""
        try:
            async with self.db_service.async_session() as session:
                stmt = select(UserScenarioConfigDB).where(
                    UserScenarioConfigDB.user_id == user_id
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"[PromptComposer] 获取用户配置失败: {e}")
            return None

    async def _get_session_scenario_config(
        self,
        session_id: str
    ) -> Optional[SessionScenarioConfigDB]:
        """获取会话配置"""
        try:
            async with self.db_service.async_session() as session:
                stmt = select(SessionScenarioConfigDB).where(
                    SessionScenarioConfigDB.session_id == session_id
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"[PromptComposer] 获取会话配置失败: {e}")
            return None

    async def _get_user_custom_prompt(self, user_id: Optional[int]) -> Optional[str]:
        """获取用户自定义prompt"""
        if not user_id:
            return None

        user_config = await self._get_user_scenario_config(user_id)
        if user_config and user_config.user_custom_prompt:
            return user_config.user_custom_prompt

        return None

    async def _get_session_custom_prompt(self, session_id: Optional[str]) -> Optional[str]:
        """获取会话自定义prompt"""
        if not session_id:
            return None

        session_config = await self._get_session_scenario_config(session_id)
        if session_config and session_config.session_custom_prompt:
            return session_config.session_custom_prompt

        return None
