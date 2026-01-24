"""
Configuration Manager - Platform configuration management service

This service manages user-level and scenario-based configurations,
implementing a priority hierarchy: Request > Session > User > Global
"""
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import joinedload

from models.database import UserConfigDB, BusinessScenarioDB, UserDB
from services.database import DatabaseService
from core.config import settings
from models.platform import AgentConfig


class ConfigurationManager:
    """
    Configuration Manager for platform customization
    
    Implements configuration priority:
    Request > Session > User > Global
    """
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def get_user_config(self, user_id: int) -> Optional[UserConfigDB]:
        """Get user configuration by user_id, eagerly loading associated scenario."""
        try:
            async with self.db_service.async_session() as session:
                from sqlalchemy import select
                # Eagerly load associated scenario relationship
                stmt = select(UserConfigDB).options(joinedload(UserConfigDB.associated_scenario)).where(UserConfigDB.user_id == user_id)
                result = await session.execute(stmt)
                user_config = result.scalar_one_or_none()
                if user_config:
                    logger.debug(f"[ConfigManager] Loaded user config for user_id={user_id}, associated_scenario_id={user_config.associated_scenario_id}")
                return user_config
        except Exception as e:
            logger.error(f"Error getting user config for user_id={user_id}: {e}", exc_info=True)
            return None
    
    async def get_business_scenario(self, scenario_id: int) -> Optional[BusinessScenarioDB]:
        """Get business scenario by id (integer)"""
        try:
            async with self.db_service.async_session() as session:
                from sqlalchemy import select
                stmt = select(BusinessScenarioDB).where(
                    BusinessScenarioDB.id == scenario_id  # 使用整数ID查询
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting business scenario id={scenario_id}: {e}")
            return None
    
    async def list_public_scenarios(self, limit: int = 50) -> List[BusinessScenarioDB]:
        """List public business scenarios"""
        try:
            async with self.db_service.async_session() as session:
                from sqlalchemy import select
                stmt = (
                    select(BusinessScenarioDB)
                    .where(BusinessScenarioDB.is_public == True)
                    .order_by(BusinessScenarioDB.created_at.desc())
                    .limit(limit)
                )
                result = await session.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing public scenarios: {e}")
            return []
    
    async def list_user_scenarios(self, user_id: int, limit: int = 50) -> List[BusinessScenarioDB]:
        """List business scenarios created by user"""
        try:
            async with self.db_service.async_session() as session:
                from sqlalchemy import select
                stmt = (
                    select(BusinessScenarioDB)
                    .where(BusinessScenarioDB.created_by == user_id)
                    .order_by(BusinessScenarioDB.created_at.desc())
                    .limit(limit)
                )
                result = await session.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing user scenarios for user_id={user_id}: {e}")
            return []
    
    def merge_agent_config(
        self,
        request_config: Optional[Dict[str, Any]] = None,
        session_config: Optional[Dict[str, Any]] = None,
        user_config: Optional[UserConfigDB] = None,
        scenario_config: Optional[BusinessScenarioDB] = None,
        global_config: Optional[Dict[str, Any]] = None,
    ) -> AgentConfig:
        """
        Merge agent configuration with priority:
        Request > Session > User > Scenario > Global
        
        Args:
            request_config: Request-level configuration (highest priority)
            session_config: Session-level configuration
            user_config: User-level configuration
            scenario_config: Business scenario configuration
            global_config: Global configuration (lowest priority)
        
        Returns:
            Merged AgentConfig
        """
        # Start with global defaults
        # Note: system_prompt will be set by AgentService if not provided
        # Note: setting_sources controls skill loading - default to None (no skills) for security
        merged = {
            "system_prompt": None,  # Will use AgentService default if None
            "allowed_tools": settings.allowed_tools_list,
            "model": settings.default_model,
            "permission_mode": settings.permission_mode,
            "max_turns": settings.max_turns,
            "cwd": str(settings.work_dir.parent),  # 🔧 修复：使用项目根目录 aigc/ 而不是 aigc/work_dir
            "custom_tools": None,
            "setting_sources": None,  # 默认不加载 skill，需要用户明确配置
            "enabled_skill_ids": None,  # 指定要启用的技能ID列表（用于精细控制）
        }
        
        # Track source of each config item for logging
        config_sources = {
            "system_prompt": "GLOBAL",
            "allowed_tools": "GLOBAL",
            "model": "GLOBAL",
            "permission_mode": "GLOBAL",
            "max_turns": "GLOBAL",
            "cwd": "GLOBAL",
            "custom_tools": "GLOBAL",
            "setting_sources": "GLOBAL",
            "enabled_skill_ids": "GLOBAL",
        }
        
        # Apply global config if provided
        if global_config:
            for k, v in global_config.items():
                if v is not None:
                    merged[k] = v
                    config_sources[k] = "GLOBAL"
        
        # Apply scenario config (if exists) - lower priority than user
        if scenario_config:
            logger.info(f"[ConfigManager] Applying scenario config for id={scenario_config.id}")
            logger.info(f"[ConfigManager] Scenario config - allowed_tools: {scenario_config.allowed_tools}")
            if scenario_config.system_prompt:
                merged["system_prompt"] = scenario_config.system_prompt
                config_sources["system_prompt"] = "SCENARIO"
                logger.info(f"[ConfigManager] ✅ Set system_prompt from SCENARIO config (length: {len(scenario_config.system_prompt)})")
            if scenario_config.allowed_tools:
                try:
                    scenario_tools = json.loads(scenario_config.allowed_tools)
                    merged["allowed_tools"] = scenario_tools
                    config_sources["allowed_tools"] = "SCENARIO"
                    logger.info(f"[ConfigManager] ✅ Set allowed_tools from SCENARIO config: {len(scenario_tools)} tools - {scenario_tools}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Invalid JSON in scenario_config.allowed_tools for id={scenario_config.id}: {e}")
            if scenario_config.recommended_model:
                merged["model"] = scenario_config.recommended_model
                config_sources["model"] = "SCENARIO"
            if scenario_config.permission_mode:
                merged["permission_mode"] = scenario_config.permission_mode
                config_sources["permission_mode"] = "SCENARIO"
                logger.info(f"[ConfigManager] ✅ Set permission_mode from SCENARIO config: {scenario_config.permission_mode}")
            if scenario_config.max_turns:
                merged["max_turns"] = scenario_config.max_turns
                config_sources["max_turns"] = "SCENARIO"
                logger.info(f"[ConfigManager] ✅ Set max_turns from SCENARIO config: {scenario_config.max_turns}")
            # 🚫 移除场景配置的 work_dir 覆盖，统一使用全局 work_dir
            # if scenario_config.work_dir:
            #     merged["cwd"] = scenario_config.work_dir
            #     config_sources["cwd"] = "SCENARIO"
            #     logger.info(f"[ConfigManager] ✅ Set work_dir from SCENARIO config: {scenario_config.work_dir}")
            if scenario_config.custom_tools:
                # Scenario config custom_tools (will be overridden by user config if exists)
                merged["custom_tools"] = scenario_config.custom_tools
                config_sources["custom_tools"] = "SCENARIO"
                logger.info(f"[ConfigManager] ✅ Set custom_tools from SCENARIO config: {list(scenario_config.custom_tools.keys()) if isinstance(scenario_config.custom_tools, dict) else 'N/A'}")
            # 检查场景配置的 skills 字段（存储在数据库中为 dict/JSON）
            if scenario_config.skills:
                try:
                    # skills 可能是 dict（JSON）或列表
                    if isinstance(scenario_config.skills, dict):
                        # 如果是 dict，尝试提取 skills 列表
                        skills_list = scenario_config.skills.get("skills", []) if isinstance(scenario_config.skills.get("skills"), list) else []
                    elif isinstance(scenario_config.skills, list):
                        skills_list = scenario_config.skills
                    elif isinstance(scenario_config.skills, str):
                        # 如果是字符串，尝试解析 JSON
                        skills_data = json.loads(scenario_config.skills)
                        if isinstance(skills_data, dict):
                            skills_list = skills_data.get("skills", [])
                        elif isinstance(skills_data, list):
                            skills_list = skills_data
                        else:
                            skills_list = []
                    else:
                        skills_list = []
                    
                    if len(skills_list) > 0:
                        # 场景级别的配置（会被用户配置覆盖）
                        merged["setting_sources"] = ["project"]  # 只加载项目级别的 skill
                        # 存储指定的技能名称列表，用于精细控制
                        # 注意：skills_list 现在是技能名称数组，不是ID数组
                        merged["enabled_skill_ids"] = skills_list
                        config_sources["setting_sources"] = "SCENARIO"
                        config_sources["enabled_skill_ids"] = "SCENARIO"
                        logger.info(f"[ConfigManager] ✅ Scenario {scenario_config.id} has {len(skills_list)} skills: {skills_list}, enabling skill loading from SCENARIO")
                        logger.info(f"[ConfigManager] ✅ Enabled specific skills (names): {skills_list}")
                    else:
                        logger.info(f"[ConfigManager] Scenario {scenario_config.id} has empty/invalid skills, skill loading DISABLED")
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    logger.warning(f"[ConfigManager] Invalid skills format in scenario {scenario_config.id}: {e}")  # 使用整数ID
        
        # Apply user config (if exists) - higher priority than scenario
        if user_config:
            logger.info(f"[ConfigManager] Applying user config for user_id={user_config.user_id}")
            logger.info(f"[ConfigManager] User config - system_prompt: {user_config.default_system_prompt[:100] if user_config.default_system_prompt else None}...")
            logger.info(f"[ConfigManager] User config - custom_skills: {user_config.custom_skills} (type: {type(user_config.custom_skills).__name__})")
            if user_config.default_system_prompt:
                merged["system_prompt"] = user_config.default_system_prompt
                config_sources["system_prompt"] = "USER"
                logger.info(f"[ConfigManager] ✅ Set system_prompt from USER config (length: {len(user_config.default_system_prompt)})")
            if user_config.default_allowed_tools:
                try:
                    # default_allowed_tools 可能是 JSON 字符串或已经是列表
                    if isinstance(user_config.default_allowed_tools, str):
                        parsed_tools = json.loads(user_config.default_allowed_tools)
                    elif isinstance(user_config.default_allowed_tools, list):
                        parsed_tools = user_config.default_allowed_tools
                    else:
                        logger.warning(f"[ConfigManager] Unexpected default_allowed_tools type: {type(user_config.default_allowed_tools)}")
                        parsed_tools = []
                    
                    if isinstance(parsed_tools, list) and len(parsed_tools) > 0:
                        merged["allowed_tools"] = parsed_tools
                        config_sources["allowed_tools"] = "USER"
                        logger.info(f"[ConfigManager] ✅ Set allowed_tools from USER config: {len(parsed_tools)} tools - {parsed_tools}")
                    elif isinstance(parsed_tools, list) and len(parsed_tools) == 0:
                        logger.info(f"[ConfigManager] User {user_config.user_id} has empty allowed_tools list, keeping {config_sources['allowed_tools']}")
                    else:
                        logger.warning(f"[ConfigManager] Invalid allowed_tools format for user_id={user_config.user_id}: {parsed_tools}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"[ConfigManager] Invalid JSON in user_config.default_allowed_tools for user_id={user_config.user_id}: {e}")
            if user_config.default_model:
                merged["model"] = user_config.default_model
                config_sources["model"] = "USER"
            if user_config.permission_mode:
                merged["permission_mode"] = user_config.permission_mode
                config_sources["permission_mode"] = "USER"
            if user_config.max_turns:
                merged["max_turns"] = user_config.max_turns
                config_sources["max_turns"] = "USER"
            # 🚫 移除用户配置的 work_dir 覆盖，统一使用全局 work_dir
            # if user_config.work_dir:
            #     merged["cwd"] = user_config.work_dir
            #     config_sources["cwd"] = "USER"
            if user_config.custom_tools:
                # 用户配置的 custom_tools (MCP servers) - 会覆盖场景配置
                merged["custom_tools"] = user_config.custom_tools
                config_sources["custom_tools"] = "USER"
                logger.info(f"[ConfigManager] ✅ Set custom_tools from USER config (overrides SCENARIO): {list(user_config.custom_tools.keys()) if isinstance(user_config.custom_tools, dict) else 'N/A'}")
            # 处理 custom_skills：决定是否启用 skill 加载
            # custom_skills 在数据库中存储为 dict（JSON），可能是 {"skills": [...]} 或直接是 list
            # 注意：json 模块已在文件顶部导入，不需要在条件内导入
            if user_config.custom_skills:
                try:
                    # custom_skills 在数据库中存储为 dict（JSON），需要解析
                    # 如果已经是 dict，直接使用；如果是字符串，需要解析
                    logger.debug(f"[ConfigManager] Processing custom_skills for user {user_config.user_id}: type={type(user_config.custom_skills)}, value={user_config.custom_skills}")
                    
                    if isinstance(user_config.custom_skills, str):
                        # 如果是字符串，尝试解析 JSON
                        skills_data = json.loads(user_config.custom_skills)
                    elif isinstance(user_config.custom_skills, dict):
                        # 如果已经是 dict，直接使用
                        skills_data = user_config.custom_skills
                    elif isinstance(user_config.custom_skills, list):
                        # 如果已经是 list，直接使用
                        skills_data = user_config.custom_skills
                    else:
                        logger.warning(f"[ConfigManager] Unexpected custom_skills type: {type(user_config.custom_skills)}")
                        skills_data = None
                    
                    # skills_data 可能是 dict 或 list
                    # 如果是 dict，可能是 {"skills": [...]} 格式
                    # 如果是 list，直接使用
                    if skills_data is None:
                        skills_list = []
                    elif isinstance(skills_data, dict):
                        # 如果是 dict，尝试提取 skills 列表
                        skills_list = skills_data.get("skills", []) if isinstance(skills_data.get("skills"), list) else []
                    elif isinstance(skills_data, list):
                        skills_list = skills_data
                    else:
                        skills_list = []
                    
                    if len(skills_list) > 0:
                        # 用户配置了非空的 skill 列表，启用 skill 加载
                        merged["setting_sources"] = ["project"]  # 只加载项目级别的 skill
                        # 存储指定的技能ID列表，用于精细控制
                        merged["enabled_skill_ids"] = skills_list
                        config_sources["setting_sources"] = "USER"
                        config_sources["enabled_skill_ids"] = "USER"
                        logger.info(f"[ConfigManager] ✅ User {user_config.user_id} has {len(skills_list)} custom_skills: {skills_list}, enabling skill loading from USER")
                        logger.info(f"[ConfigManager] ✅ Enabled specific skill IDs: {skills_list}")
                    else:
                        # 用户配置了空列表或无效格式，不加载 skill
                        logger.info(f"[ConfigManager] User {user_config.user_id} has empty/invalid custom_skills (parsed as: {skills_list}), skill loading DISABLED")
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    # 解析失败，保持默认（不加载）
                    logger.warning(f"[ConfigManager] User {user_config.user_id} custom_skills parse error: {e}, skill loading DISABLED", exc_info=True)
            else:
                # 用户没有配置 custom_skills，不加载 skill
                logger.info(f"[ConfigManager] User {user_config.user_id} has no custom_skills configured, skill loading DISABLED")
        
        # Apply session config (if exists)
        if session_config:
            if session_config.get("system_prompt"):
                merged["system_prompt"] = session_config["system_prompt"]
                config_sources["system_prompt"] = "SESSION"
                logger.info(f"[ConfigManager] ✅ Override system_prompt from SESSION config")
            if session_config.get("allowed_tools"):
                merged["allowed_tools"] = session_config["allowed_tools"]
                config_sources["allowed_tools"] = "SESSION"
                logger.info(f"[ConfigManager] ✅ Override allowed_tools from SESSION config")
            if session_config.get("model"):
                merged["model"] = session_config["model"]
                config_sources["model"] = "SESSION"
            if session_config.get("permission_mode"):
                merged["permission_mode"] = session_config["permission_mode"]
                config_sources["permission_mode"] = "SESSION"
            if session_config.get("max_turns"):
                merged["max_turns"] = session_config["max_turns"]
                config_sources["max_turns"] = "SESSION"
        
        # Apply request config (highest priority)
        if request_config:
            if request_config.get("system_prompt"):
                merged["system_prompt"] = request_config["system_prompt"]
                config_sources["system_prompt"] = "REQUEST"
                logger.info(f"[ConfigManager] ✅ Override system_prompt from REQUEST config")
            if request_config.get("allowed_tools"):
                merged["allowed_tools"] = request_config["allowed_tools"]
                config_sources["allowed_tools"] = "REQUEST"
                logger.info(f"[ConfigManager] ✅ Override allowed_tools from REQUEST config")
            if request_config.get("model"):
                merged["model"] = request_config["model"]
                config_sources["model"] = "REQUEST"
            if request_config.get("permission_mode"):
                merged["permission_mode"] = request_config["permission_mode"]
                config_sources["permission_mode"] = "REQUEST"
            if request_config.get("max_turns"):
                merged["max_turns"] = request_config["max_turns"]
                config_sources["max_turns"] = "REQUEST"
            if request_config.get("cwd"):
                merged["cwd"] = request_config["cwd"]
                config_sources["cwd"] = "REQUEST"
        
        # Log final merged configuration with source information
        allowed_tools = merged.get('allowed_tools', [])
        custom_tools = merged.get('custom_tools')
        setting_sources = merged.get('setting_sources')
        
        logger.info(f"[ConfigManager] ========== Final merged config (with sources) ==========")
        logger.info(f"  - system_prompt: {'SET' if merged.get('system_prompt') else 'NOT SET'} (length: {len(merged.get('system_prompt', ''))} if set) [SOURCE: {config_sources.get('system_prompt', 'GLOBAL')}]")
        logger.info(f"  - model: {merged.get('model')} [SOURCE: {config_sources.get('model', 'GLOBAL')}]")
        logger.info(f"  - allowed_tools: {len(allowed_tools)} tools - {allowed_tools} [SOURCE: {config_sources.get('allowed_tools', 'GLOBAL')}]")
        logger.info(f"  - permission_mode: {merged.get('permission_mode')} [SOURCE: {config_sources.get('permission_mode', 'GLOBAL')}]")
        logger.info(f"  - max_turns: {merged.get('max_turns')} [SOURCE: {config_sources.get('max_turns', 'GLOBAL')}]")
        logger.info(f"  - cwd: {merged.get('cwd')} [SOURCE: {config_sources.get('cwd', 'GLOBAL')}]")
        logger.info(f"  - setting_sources: {setting_sources} (skills: {'ENABLED' if setting_sources else 'DISABLED'}) [SOURCE: {config_sources.get('setting_sources', 'GLOBAL')}]")
        enabled_skill_ids = merged.get('enabled_skill_ids')
        logger.info(f"  - enabled_skill_ids: {enabled_skill_ids} (specific skills to enable) [SOURCE: {config_sources.get('enabled_skill_ids', 'GLOBAL')}]")
        logger.info(f"  - custom_tools (MCP servers): {list(custom_tools.keys()) if custom_tools and isinstance(custom_tools, dict) else 'None'} [SOURCE: {config_sources.get('custom_tools', 'GLOBAL')}]")
        logger.info(f"[ConfigManager] ==========================================================")
        
        return AgentConfig(**merged), config_sources
    
    async def get_user_work_dir(self, user_id: int) -> Path:
        """
        Get user's working directory with isolation
        
        If user has custom work_dir in config, use it.
        Otherwise, use global work_dir with user subdirectory.
        
        Args:
            user_id: User ID
        
        Returns:
            Path to user's isolated working directory
        """
        user_config = await self.get_user_config(user_id)
        
        if user_config and user_config.work_dir:
            work_dir = Path(user_config.work_dir)
        else:
            # Use global work_dir with user isolation
            work_dir = settings.work_dir / f"user_{user_id}"
        
        # Ensure directory exists
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
