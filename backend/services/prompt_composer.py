"""
Prompt组合器服务

核心设计原则：
1. 充分依赖模型规划能力 - 组合prompt，让模型自主选择和组合场景
2. 完整的默认配置体系 - 零配置可用，默认场景和默认系统prompt
3. 渐进式配置 - Layer 0（默认）→ Layer 1（场景）→ Layer 2（用户）→ Layer 3（会话）

职责：
1. 组合各层级的prompt（系统默认 + 场景层 + 用户层 + 会话层）
2. 处理场景prompt的组合（多个场景prompt合并）
3. 确定使用的场景（优先级：会话层 > 用户层 > 默认）
"""
from typing import List, Dict, Optional
import json
import logging

from services.database import DatabaseService
from services.default_config import DefaultConfig
from services.scenario_provider import ScenarioProvider
from services.preference_learner import PreferenceLearner
from services.prompt_evolver import PromptEvolver
from models.database import (
    UserScenarioConfigDB, 
    SessionScenarioConfigDB,
    BusinessScenarioDB
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.agent_service import AgentService

logger = logging.getLogger(__name__)


class PromptComposer:
    """Prompt组合器"""
    
    def __init__(self, db_service: DatabaseService):
        """
        初始化Prompt组合器
        
        Args:
            db_service: 数据库服务实例
        """
        self.db_service = db_service
        self.scenario_provider = ScenarioProvider(db_service)
        self.preference_learner = PreferenceLearner(db_service)
        self.prompt_evolver = PromptEvolver()
    
    async def compose_base_prompt(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        user_query: Optional[str] = None,
        auto_match_scenario: bool = True,
        agent_service: Optional["AgentService"] = None,
    ) -> str:
        """
        组合基础prompt（系统默认 + 场景层 + 用户层 + 会话层）
        
        核心设计原则：
        - 模型驱动：在系统prompt中包含场景列表，让模型自主选择
        - 零配置可用：用户不配置任何场景时使用默认场景
        - 渐进式配置：各层级配置逐步叠加
        
        优先级：
        - 场景选择：自动匹配 > 会话层 > 用户层 > 默认
        - Prompt组合：系统默认 + 场景prompt + 用户自定义 + 会话自定义
        
        Args:
            user_id: 用户ID（可选）
            session_id: 会话ID（可选）
            user_query: 用户输入（可选，用于自动匹配场景）
            auto_match_scenario: 是否自动匹配场景（默认 True）
            agent_service: Agent服务（可选，用于模型匹配场景）
            
        Returns:
            str: 组合后的系统prompt
        """
        # 1. 获取用户可用的场景列表（用于系统prompt中的场景列表）
        available_scenarios = await self.scenario_provider.get_available_scenarios(user_id=user_id)
        
        # 2. 确定使用的场景
        scenario_ids = None
        
        # 优先级1：自动匹配场景（如果提供了用户输入且启用自动匹配）
        if auto_match_scenario and user_query and agent_service:
            try:
                from services.scenario_matcher import ScenarioMatcher
                matcher = ScenarioMatcher(self.db_service, agent_service)
                matched_scenario = await matcher.match_scenario(
                    user_query, 
                    user_id,
                    agent_service=agent_service
                )
                if matched_scenario:
                    scenario_ids = [matched_scenario.get("scenario_id")]
                    logger.info(
                        f"[PromptComposer] ✅ 自动匹配到场景: {matched_scenario.get('name')} "
                        f"(scenario_id: {matched_scenario.get('scenario_id')})"
                    )
            except Exception as e:
                logger.warning(f"[PromptComposer] 自动匹配场景失败: {e}，继续使用其他方式")
        
        # 优先级2：会话层/用户层配置的场景（如果自动匹配未成功）
        if not scenario_ids:
            scenario_ids = await self._determine_scenarios(user_id, session_id)
        
        # 3. 获取默认系统prompt（包含场景列表，优先从数据库读取）
        base_prompt = await DefaultConfig.get_default_system_prompt_with_db(
            available_scenarios=available_scenarios,
            db_service=self.db_service
        )
        
        # 4. 组合场景prompt（如果用户选择了场景）
        if scenario_ids and len(scenario_ids) > 0:
            scenario_prompts = await self._combine_scenarios(scenario_ids)
            if scenario_prompts:
                # 在系统prompt之后添加场景prompt
                base_prompt = f"{base_prompt}\n\n## 场景能力详情\n\n{scenario_prompts}"
        
        # 5. 添加用户自定义prompt（如果存在）
        user_custom_prompt = await self._get_user_custom_prompt(user_id)
        if user_custom_prompt:
            base_prompt = f"{base_prompt}\n\n## 用户自定义规则\n\n{user_custom_prompt}"
        
        # 6. 添加会话自定义prompt（如果存在）
        session_custom_prompt = await self._get_session_custom_prompt(session_id)
        if session_custom_prompt:
            base_prompt = f"{base_prompt}\n\n## 会话级调整\n\n{session_custom_prompt}"
        
        logger.debug(
            f"[PromptComposer] 组合基础prompt完成: user_id={user_id}, "
            f"session_id={session_id}, scenario_ids={scenario_ids}"
        )
        
        return base_prompt
    
    async def compose_evolved_prompt(
        self,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        agent_service: Optional["AgentService"] = None,
        include_evolution: bool = True
    ) -> str:
        """
        组合包含进化层的完整prompt（基础prompt + 用户偏好 + 会话偏好）
        
        核心设计原则：
        - 渐进式配置：基础层 → 场景层 → 用户层 → 会话层 → 进化层
        - 模型驱动：使用模型智能提取用户偏好
        - 简洁高效：只包含关键偏好信息，不冗长
        
        优先级：
        - 偏好优先级：会话偏好 > 用户偏好
        - 缓存机制：使用数据摘要hash判断是否需要重新分析
        
        Args:
            user_id: 用户ID（可选）
            session_id: 会话ID（可选）
            agent_service: Agent服务（用于调用模型分析偏好，可选）
            include_evolution: 是否包含进化层（默认True）
            
        Returns:
            str: 组合后的完整系统prompt（包含进化层）
        """
        # 1. 组合基础prompt（系统默认 + 场景层 + 用户层 + 会话层）
        base_prompt = await self.compose_base_prompt(
            user_id=user_id,
            session_id=session_id
        )
        
        # 2. 如果不包含进化层，直接返回基础prompt
        if not include_evolution:
            return base_prompt
        
        # 3. 加载用户偏好（如果提供了agent_service）
        user_preferences = None
        if user_id and agent_service:
            try:
                user_preferences = await self.preference_learner.get_user_preferences(
                    user_id=user_id,
                    agent_service=agent_service,
                    force_refresh=False
                )
                logger.debug(
                    f"[PromptComposer] 加载用户偏好: user_id={user_id}, "
                    f"has_preferences={user_preferences is not None}"
                )
            except Exception as e:
                logger.warning(f"[PromptComposer] 加载用户偏好失败: {e}")
                # 不影响主流程，继续执行
        
        # 4. 加载会话偏好
        session_preferences = None
        if session_id:
            try:
                session_preferences = await self.preference_learner.get_session_preferences(
                    session_id=session_id
                )
                logger.debug(
                    f"[PromptComposer] 加载会话偏好: session_id={session_id}, "
                    f"has_preferences={session_preferences is not None}"
                )
            except Exception as e:
                logger.warning(f"[PromptComposer] 加载会话偏好失败: {e}")
                # 不影响主流程，继续执行
        
        # 5. 进化prompt（融入偏好）
        evolved_prompt = self.prompt_evolver.evolve_prompt(
            base_prompt=base_prompt,
            user_preferences=user_preferences,
            session_preferences=session_preferences
        )
        
        logger.debug(
            f"[PromptComposer] 组合进化prompt完成: user_id={user_id}, "
            f"session_id={session_id}, "
            f"base_length={len(base_prompt)}, "
            f"evolved_length={len(evolved_prompt)}"
        )
        
        return evolved_prompt
    
    async def _determine_scenarios(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
    ) -> Optional[List[str]]:
        """
        确定使用的场景（优先级：会话层 > 用户层 > 默认）
        
        核心设计原则：
        - 渐进式配置：会话层覆盖用户层，用户层覆盖默认
        - 零配置可用：如果都没有配置，返回None（使用默认场景）
        - 模型驱动：场景列表提供给模型，让模型自主选择
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Optional[List[str]]: 场景ID列表，None表示使用默认场景
        """
        # 优先级1：会话层配置
        if session_id:
            session_config = await self._get_session_scenario_config(session_id)
            if session_config and session_config.scenario_ids:
                try:
                    scenario_ids = json.loads(session_config.scenario_ids)
                    if scenario_ids:
                        logger.debug(f"[PromptComposer] 使用会话层场景配置: {scenario_ids}")
                        return scenario_ids
                except json.JSONDecodeError:
                    logger.warning(f"[PromptComposer] 会话场景配置JSON解析失败: {session_config.scenario_ids}")
        
        # 优先级2：用户层配置
        if user_id:
            user_config = await self._get_user_scenario_config(user_id)
            if user_config and user_config.scenario_ids:
                try:
                    scenario_ids = json.loads(user_config.scenario_ids)
                    if scenario_ids:
                        logger.debug(f"[PromptComposer] 使用用户层场景配置: {scenario_ids}")
                        return scenario_ids
                except json.JSONDecodeError:
                    logger.warning(f"[PromptComposer] 用户场景配置JSON解析失败: {user_config.scenario_ids}")
            
            # 向后兼容：如果 UserScenarioConfigDB 不存在或为空，检查 UserConfigDB.associated_scenario_id
            if not user_config or not user_config.scenario_ids:
                try:
                    from services.configuration_manager import ConfigurationManager
                    config_manager = ConfigurationManager(self.db_service)
                    user_config_old = await config_manager.get_user_config(user_id)
                    if user_config_old and user_config_old.associated_scenario_id:
                        # 将旧的单选场景转换为数组格式（向后兼容）
                        scenario_ids = [user_config_old.associated_scenario_id]
                        logger.debug(f"[PromptComposer] 使用旧版用户配置 associated_scenario_id (向后兼容): {scenario_ids}")
                        return scenario_ids
                except Exception as e:
                    logger.warning(f"[PromptComposer] 检查旧版用户配置失败: {e}")
        
        # 优先级3：默认（返回None，表示使用默认场景）
        logger.debug(f"[PromptComposer] 使用默认场景配置")
        return None
    
    async def _combine_scenarios(self, scenario_ids: List[str]) -> str:
        """
        组合场景prompt（简单合并）
        
        核心设计原则：
        - 模型驱动：代码只做简单合并，不判断场景兼容性
        - 简单合并：多个场景prompt用分隔符连接
        
        Args:
            scenario_ids: 场景ID列表
            
        Returns:
            str: 组合后的场景prompt
        """
        if not scenario_ids:
            return ""
        
        prompts = []
        
        async with self.db_service.async_session() as session:
            for i, scenario_id in enumerate(scenario_ids):
                # 如果是默认场景，跳过（默认场景不添加额外prompt）
                if scenario_id == DefaultConfig.get_default_scenario_id():
                    continue
                
                # 从数据库获取场景
                stmt = select(BusinessScenarioDB).where(
                    BusinessScenarioDB.scenario_id == scenario_id
                )
                result = await session.execute(stmt)
                scenario = result.scalar_one_or_none()
                
                if scenario and scenario.system_prompt:
                    prompts.append(
                        f"### 场景能力 {i+1}: {scenario.name}\n{scenario.system_prompt}"
                    )
        
        return "\n\n".join(prompts)
    
    async def _get_user_scenario_config(
        self, 
        user_id: int
    ) -> Optional[UserScenarioConfigDB]:
        """获取用户场景配置"""
        try:
            async with self.db_service.async_session() as session:
                stmt = select(UserScenarioConfigDB).where(
                    UserScenarioConfigDB.user_id == user_id
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"[PromptComposer] 获取用户场景配置失败: {e}")
            return None
    
    async def _get_session_scenario_config(
        self, 
        session_id: str
    ) -> Optional[SessionScenarioConfigDB]:
        """获取会话场景配置"""
        try:
            async with self.db_service.async_session() as session:
                stmt = select(SessionScenarioConfigDB).where(
                    SessionScenarioConfigDB.session_id == session_id
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"[PromptComposer] 获取会话场景配置失败: {e}")
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
