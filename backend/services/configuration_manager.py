"""
Configuration Manager - Platform configuration management service

核心设计:
1. 用户配置管理 (system_prompt, allowed_tools, model 等)
2. 能力包解析 → 返回 SDK plugins 参数
3. SDK 会自动处理 plugins 中的 skills/tools/MCP/prompt 融合

配置优先级: Request > Session > User > Global
"""
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger
from sqlalchemy import select

from models.database import UserConfigDB
from services.database import DatabaseService
from core.config import settings
from models.platform import AgentConfig


class ConfigurationManager:
    """
    Configuration Manager for platform customization

    核心职责:
    1. 管理用户级配置 (system_prompt, allowed_tools, model 等)
    2. 解析能力包 → 返回 SDK plugins 参数
    3. SDK 会自动处理 plugins 的能力融合
    """

    def __init__(self, db_service: DatabaseService, package_service=None):
        self.db_service = db_service
        self._package_service = package_service

    @property
    def package_service(self):
        """Lazy load PackageService"""
        if self._package_service is None:
            from services.package_service import PackageService
            self._package_service = PackageService(self.db_service)
        return self._package_service

    async def get_user_config(self, user_id: int) -> Optional[UserConfigDB]:
        """Get user configuration by user_id"""
        try:
            async with self.db_service.async_session() as session:
                stmt = select(UserConfigDB).where(UserConfigDB.user_id == user_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user config for user_id={user_id}: {e}")
            return None

    async def resolve_user_plugins(
        self,
        user_id: int,
        plugin_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, str]]:
        """
        解析用户的能力包,返回 SDK plugins 参数

        Args:
            user_id: 用户ID
            plugin_ids: 可选,指定的能力包ID列表

        Returns:
            SDK plugins 参数格式: [{"type": "local", "path": "..."}, ...]
        """
        # 获取用户绑定的能力包
        if plugin_ids:
            # 请求级指定,需要校验权限
            is_valid, invalid_ids = await self.package_service.validate_plugin_access(
                user_id, plugin_ids
            )
            if not is_valid:
                raise PermissionError(f"用户无权使用能力包: {invalid_ids}")
            use_ids = plugin_ids
        else:
            # 使用用户所有已绑定的能力包
            use_ids = await self.package_service.get_user_bound_package_ids(user_id)

        if not use_ids:
            return []

        # 获取能力包详情,提取 plugin_path
        plugins = []
        async with self.db_service.async_session() as session:
            from models.database import CapabilityPackageDB
            stmt = select(CapabilityPackageDB).where(CapabilityPackageDB.id.in_(use_ids))
            result = await session.execute(stmt)
            packages = list(result.scalars().all())

            for pkg in packages:
                if pkg.plugin_path:
                    plugins.append({
                        "type": "local",
                        "path": pkg.plugin_path
                    })
                    logger.info(f"[ConfigManager] 📦 加载能力包: {pkg.name} -> {pkg.plugin_path}")

        logger.info(f"[ConfigManager] 📦 共加载 {len(plugins)} 个能力包")
        return plugins

    async def merge_agent_config(
        self,
        request_config: Optional[Dict[str, Any]] = None,
        session_config: Optional[Dict[str, Any]] = None,
        user_config: Optional[UserConfigDB] = None,
        global_config: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        plugin_ids: Optional[List[int]] = None,
    ) -> AgentConfig:
        """
        Merge agent configuration with priority:
        Request > Session > User > Global

        Args:
            request_config: Request-level configuration (highest priority)
            session_config: Session-level configuration
            user_config: User-level configuration
            global_config: Global configuration (lowest priority)
            user_id: User ID for plugin resolution
            plugin_ids: Request-level specified package IDs

        Returns:
            Merged AgentConfig with sdk_plugins field
        """
        # Start with global defaults
        merged = {
            "system_prompt": None,
            "allowed_tools": settings.allowed_tools_list,
            "model": settings.default_model,
            "permission_mode": settings.permission_mode,
            "max_turns": settings.max_turns,
            "cwd": str(settings.work_dir.parent),
            "custom_tools": None,
            "setting_sources": None,
            "enabled_skill_ids": None,
            "sdk_plugins": None,  # SDK plugins 参数
        }

        config_sources = {
            "system_prompt": "GLOBAL",
            "allowed_tools": "GLOBAL",
            "model": "GLOBAL",
            "permission_mode": "GLOBAL",
            "max_turns": "GLOBAL",
            "cwd": "GLOBAL",
            "sdk_plugins": "GLOBAL",
        }

        # Apply global config
        if global_config:
            for k, v in global_config.items():
                if v is not None:
                    merged[k] = v
                    config_sources[k] = "GLOBAL"

        # =========================================================================
        # 能力包解析 → SDK plugins 参数
        # =========================================================================
        if user_id:
            try:
                plugins = await self.resolve_user_plugins(user_id, plugin_ids)
                if plugins:
                    merged["sdk_plugins"] = plugins
                    config_sources["sdk_plugins"] = "REQUEST" if plugin_ids else "USER_BINDINGS"
                    logger.info(f"[ConfigManager] 📦 SDK plugins: {plugins}")
            except PermissionError as e:
                logger.warning(f"[ConfigManager] 能力包权限校验失败: {e}")
            except Exception as e:
                logger.warning(f"[ConfigManager] 解析能力包失败: {e}")

        # =========================================================================
        # 用户配置
        # =========================================================================
        if user_config:
            logger.info(f"[ConfigManager] Applying user config for user_id={user_config.user_id}")
            if user_config.default_system_prompt:
                merged["system_prompt"] = user_config.default_system_prompt
                config_sources["system_prompt"] = "USER"
            if user_config.default_allowed_tools:
                try:
                    if isinstance(user_config.default_allowed_tools, str):
                        parsed_tools = json.loads(user_config.default_allowed_tools)
                    elif isinstance(user_config.default_allowed_tools, list):
                        parsed_tools = user_config.default_allowed_tools
                    else:
                        parsed_tools = []
                    if isinstance(parsed_tools, list) and len(parsed_tools) > 0:
                        merged["allowed_tools"] = parsed_tools
                        config_sources["allowed_tools"] = "USER"
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"[ConfigManager] Invalid JSON in user_config.allowed_tools: {e}")
            if user_config.default_model:
                merged["model"] = user_config.default_model
                config_sources["model"] = "USER"
            if user_config.permission_mode:
                merged["permission_mode"] = user_config.permission_mode
                config_sources["permission_mode"] = "USER"
            if user_config.max_turns:
                merged["max_turns"] = user_config.max_turns
                config_sources["max_turns"] = "USER"

        # =========================================================================
        # 会话配置
        # =========================================================================
        if session_config:
            if session_config.get("system_prompt"):
                merged["system_prompt"] = session_config["system_prompt"]
                config_sources["system_prompt"] = "SESSION"
            if session_config.get("allowed_tools"):
                merged["allowed_tools"] = session_config["allowed_tools"]
                config_sources["allowed_tools"] = "SESSION"
            if session_config.get("model"):
                merged["model"] = session_config["model"]
                config_sources["model"] = "SESSION"
            if session_config.get("permission_mode"):
                merged["permission_mode"] = session_config["permission_mode"]
                config_sources["permission_mode"] = "SESSION"
            if session_config.get("max_turns"):
                merged["max_turns"] = session_config["max_turns"]
                config_sources["max_turns"] = "SESSION"

        # =========================================================================
        # 请求配置(最高优先级)
        # =========================================================================
        if request_config:
            if request_config.get("system_prompt"):
                merged["system_prompt"] = request_config["system_prompt"]
                config_sources["system_prompt"] = "REQUEST"
            if request_config.get("allowed_tools"):
                merged["allowed_tools"] = request_config["allowed_tools"]
                config_sources["allowed_tools"] = "REQUEST"
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

        # Log final config
        logger.info(f"[ConfigManager] Final config: model={merged.get('model')}, "
                    f"plugins={len(merged.get('sdk_plugins', []))}, "
                    f"tools={len(merged.get('allowed_tools', []))}")

        return AgentConfig(**merged), config_sources

    async def get_user_work_dir(self, user_id: int) -> Path:
        """Get user's working directory with isolation"""
        user_config = await self.get_user_config(user_id)

        if user_config and user_config.work_dir:
            work_dir = Path(user_config.work_dir)
        else:
            work_dir = settings.work_dir / f"user_{user_id}"

        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
