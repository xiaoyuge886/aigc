"""
Package Service - 能力包管理服务

核心功能：
1. 能力包 CRUD 操作
2. 用户能力绑定管理
3. 插件解析（将能力包ID解析为SDK可用的配置）

关键设计：
- 用户只能使用已绑定的能力包
- 请求级校验 plugin_ids 必须在用户绑定范围内
- 管理员可以绑定时授权
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from loguru import logger

from models.database import (
    CapabilityPackageDB,
    UserCapabilityBindingDB,
    UserDB,
)
from services.database import DatabaseService


class PackageService:
    """能力包管理服务"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    # =========================================================================
    # 能力包 CRUD
    # =========================================================================

    async def list_packages(
        self,
        public_only: bool = True,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        include_bindings: bool = False,
    ) -> List[CapabilityPackageDB]:
        """
        列出能力包

        Args:
            public_only: 只显示公开的能力包
            category: 按分类过滤
            user_id: 如果提供，同时包含用户私有的能力包
            include_bindings: 是否预加载绑定关系
        """
        async with self.db_service.async_session() as session:
            query = select(CapabilityPackageDB)

            if include_bindings:
                query = query.options(joinedload(CapabilityPackageDB.user_bindings))

            conditions = []

            if public_only:
                conditions.append(CapabilityPackageDB.is_public == True)

            if user_id is not None:
                # 包含用户创建的私有能力包
                conditions.append(CapabilityPackageDB.author_id == user_id)

            if category:
                conditions.append(CapabilityPackageDB.category == category)

            if conditions:
                if public_only and user_id is not None:
                    # 公开 OR 用户私有
                    query = query.where(
                        or_(CapabilityPackageDB.is_public == True, CapabilityPackageDB.author_id == user_id)
                    )
                    if category:
                        query = query.where(CapabilityPackageDB.category == category)
                else:
                    for condition in conditions:
                        query = query.where(condition)

            query = query.order_by(CapabilityPackageDB.created_at.desc())

            result = await session.execute(query)
            return list(result.unique().scalars().all())

    async def get_package(self, package_id: int) -> Optional[CapabilityPackageDB]:
        """获取单个能力包"""
        async with self.db_service.async_session() as session:
            stmt = select(CapabilityPackageDB).where(CapabilityPackageDB.id == package_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_package_by_name(self, name: str) -> Optional[CapabilityPackageDB]:
        """根据名称获取能力包"""
        async with self.db_service.async_session() as session:
            stmt = select(CapabilityPackageDB).where(CapabilityPackageDB.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_package(
        self,
        name: str,
        display_name: str,
        author_id: Optional[int] = None,
        **kwargs,
    ) -> CapabilityPackageDB:
        """创建能力包"""
        async with self.db_service.async_session() as session:
            package = CapabilityPackageDB(
                name=name,
                display_name=display_name,
                author_id=author_id,
                **kwargs,
            )
            session.add(package)
            await session.commit()
            await session.refresh(package)
            logger.info(f"[PackageService] Created package: {name} (id={package.id})")
            return package

    async def update_package(
        self,
        package_id: int,
        **kwargs,
    ) -> Optional[CapabilityPackageDB]:
        """更新能力包"""
        async with self.db_service.async_session() as session:
            stmt = select(CapabilityPackageDB).where(CapabilityPackageDB.id == package_id)
            result = await session.execute(stmt)
            package = result.scalar_one_or_none()

            if not package:
                return None

            for key, value in kwargs.items():
                if hasattr(package, key) and value is not None:
                    setattr(package, key, value)

            package.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(package)
            logger.info(f"[PackageService] Updated package: {package.name} (id={package.id})")
            return package

    async def delete_package(self, package_id: int) -> bool:
        """删除能力包（同时删除所有绑定）"""
        async with self.db_service.async_session() as session:
            stmt = select(CapabilityPackageDB).where(CapabilityPackageDB.id == package_id)
            result = await session.execute(stmt)
            package = result.scalar_one_or_none()

            if not package:
                return False

            await session.delete(package)
            await session.commit()
            logger.info(f"[PackageService] Deleted package: {package.name} (id={package_id})")
            return True

    # =========================================================================
    # 用户能力绑定
    # =========================================================================

    async def get_user_bindings(
        self,
        user_id: int,
        enabled_only: bool = True,
    ) -> List[Tuple[CapabilityPackageDB, UserCapabilityBindingDB]]:
        """
        获取用户的能力包绑定

        Returns:
            List of (package, binding) tuples
        """
        async with self.db_service.async_session() as session:
            query = (
                select(CapabilityPackageDB, UserCapabilityBindingDB)
                .join(UserCapabilityBindingDB)
                .where(UserCapabilityBindingDB.user_id == user_id)
            )

            if enabled_only:
                query = query.where(UserCapabilityBindingDB.is_enabled == True)

            query = query.order_by(UserCapabilityBindingDB.granted_at.desc())

            result = await session.execute(query)
            return list(result.all())

    async def get_user_bound_package_ids(self, user_id: int) -> List[int]:
        """获取用户已绑定的能力包ID列表"""
        bindings = await self.get_user_bindings(user_id, enabled_only=True)
        return [pkg.id for pkg, _ in bindings]

    async def bind_package_to_user(
        self,
        user_id: int,
        package_id: int,
        granted_by: Optional[int] = None,
        is_enabled: bool = True,
    ) -> UserCapabilityBindingDB:
        """
        绑定能力包到用户

        Args:
            user_id: 用户ID
            package_id: 能力包ID
            granted_by: 授权管理员ID
            is_enabled: 是否启用
        """
        async with self.db_service.async_session() as session:
            # 检查是否已存在绑定
            stmt = select(UserCapabilityBindingDB).where(
                and_(
                    UserCapabilityBindingDB.user_id == user_id,
                    UserCapabilityBindingDB.package_id == package_id,
                )
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # 更新现有绑定
                existing.is_enabled = is_enabled
                existing.granted_by = granted_by
                existing.granted_at = datetime.utcnow()
                await session.commit()
                await session.refresh(existing)
                logger.info(f"[PackageService] Updated binding: user={user_id}, package={package_id}")
                return existing

            # 创建新绑定
            binding = UserCapabilityBindingDB(
                user_id=user_id,
                package_id=package_id,
                granted_by=granted_by,
                is_enabled=is_enabled,
            )
            session.add(binding)
            await session.commit()
            await session.refresh(binding)
            logger.info(f"[PackageService] Created binding: user={user_id}, package={package_id}")
            return binding

    async def unbind_package_from_user(
        self,
        user_id: int,
        package_id: int,
    ) -> bool:
        """解绑用户的能力包"""
        async with self.db_service.async_session() as session:
            stmt = select(UserCapabilityBindingDB).where(
                and_(
                    UserCapabilityBindingDB.user_id == user_id,
                    UserCapabilityBindingDB.package_id == package_id,
                )
            )
            result = await session.execute(stmt)
            binding = result.scalar_one_or_none()

            if not binding:
                return False

            await session.delete(binding)
            await session.commit()
            logger.info(f"[PackageService] Deleted binding: user={user_id}, package={package_id}")
            return True

    async def update_binding(
        self,
        user_id: int,
        package_id: int,
        is_enabled: Optional[bool] = None,
    ) -> Optional[UserCapabilityBindingDB]:
        """更新绑定状态"""
        async with self.db_service.async_session() as session:
            stmt = select(UserCapabilityBindingDB).where(
                and_(
                    UserCapabilityBindingDB.user_id == user_id,
                    UserCapabilityBindingDB.package_id == package_id,
                )
            )
            result = await session.execute(stmt)
            binding = result.scalar_one_or_none()

            if not binding:
                return None

            if is_enabled is not None:
                binding.is_enabled = is_enabled

            binding.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(binding)
            return binding

    async def increment_usage_count(self, user_id: int, package_id: int) -> None:
        """增加使用次数"""
        async with self.db_service.async_session() as session:
            stmt = select(UserCapabilityBindingDB).where(
                and_(
                    UserCapabilityBindingDB.user_id == user_id,
                    UserCapabilityBindingDB.package_id == package_id,
                )
            )
            result = await session.execute(stmt)
            binding = result.scalar_one_or_none()

            if binding:
                binding.usage_count += 1
                binding.last_used_at = datetime.utcnow()
                await session.commit()

    # =========================================================================
    # 权限校验
    # =========================================================================

    async def validate_plugin_access(
        self,
        user_id: int,
        plugin_ids: List[int],
    ) -> Tuple[bool, List[int]]:
        """
        校验用户是否有权限使用指定的能力包

        Args:
            user_id: 用户ID
            plugin_ids: 请求的能力包ID列表

        Returns:
            (is_valid, invalid_ids): 是否全部有效，无效的ID列表
        """
        if not plugin_ids:
            return True, []

        bound_ids = await self.get_user_bound_package_ids(user_id)
        invalid_ids = [pid for pid in plugin_ids if pid not in bound_ids]

        return len(invalid_ids) == 0, invalid_ids

    # =========================================================================
    # 插件解析
    # =========================================================================

    async def resolve_plugins(
        self,
        plugin_ids: List[int],
    ) -> Dict[str, Any]:
        """
        解析多个能力包并合并其能力配置

        Args:
            plugin_ids: 能力包ID列表

        Returns:
            {
                "skills": [...],
                "allowed_tools": [...],
                "mcp_servers": {...},
                "custom_prompt_extension": "...",
                "plugins": [{"type": "local", "path": "..."}]
            }
        """
        async with self.db_service.async_session() as session:
            stmt = select(CapabilityPackageDB).where(CapabilityPackageDB.id.in_(plugin_ids))
            result = await session.execute(stmt)
            packages = list(result.scalars().all())

        merged = {
            "skills": [],
            "allowed_tools": [],
            "mcp_servers": {},
            "custom_prompt_extension": "",
            "plugins": [],
        }

        for pkg in packages:
            # 合并 skills
            if pkg.skills:
                skills_list = pkg.skills.get("skills", []) if isinstance(pkg.skills, dict) else []
                if isinstance(pkg.skills, list):
                    skills_list = pkg.skills
                merged["skills"].extend(skills_list)

            # 合并 allowed_tools
            if pkg.allowed_tools:
                tools_list = pkg.allowed_tools if isinstance(pkg.allowed_tools, list) else []
                if isinstance(pkg.allowed_tools, dict):
                    tools_list = pkg.allowed_tools.get("tools", [])
                merged["allowed_tools"].extend(tools_list)

            # 合并 MCP servers
            if pkg.mcp_servers and isinstance(pkg.mcp_servers, dict):
                merged["mcp_servers"].update(pkg.mcp_servers)

            # 追加 prompt extension
            if pkg.custom_prompt_extension:
                merged["custom_prompt_extension"] += "\n\n" + pkg.custom_prompt_extension

            # 添加 plugin path for SDK
            if pkg.plugin_path:
                merged["plugins"].append({
                    "type": "local",
                    "path": pkg.plugin_path
                })

        # 去重
        merged["skills"] = list(set(merged["skills"]))
        merged["allowed_tools"] = list(set(merged["allowed_tools"]))

        logger.info(
            f"[PackageService] Resolved {len(plugin_ids)} packages: "
            f"{len(merged['skills'])} skills, {len(merged['allowed_tools'])} tools, "
            f"{len(merged['mcp_servers'])} mcp servers, {len(merged['plugins'])} plugins"
        )

        return merged

    async def get_user_plugins_config(
        self,
        user_id: int,
        plugin_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        获取用户的插件配置

        如果指定 plugin_ids，则使用指定的（需要校验权限）
        否则使用用户所有已绑定的能力包

        Args:
            user_id: 用户ID
            plugin_ids: 可选，指定的能力包ID列表

        Returns:
            合并后的插件配置
        """
        if plugin_ids:
            # 校验权限
            is_valid, invalid_ids = await self.validate_plugin_access(user_id, plugin_ids)
            if not is_valid:
                raise PermissionError(f"用户无权使用能力包: {invalid_ids}")
            use_ids = plugin_ids
        else:
            # 使用用户所有已绑定的能力包
            use_ids = await self.get_user_bound_package_ids(user_id)

        if not use_ids:
            return {
                "skills": [],
                "allowed_tools": [],
                "mcp_servers": {},
                "custom_prompt_extension": "",
                "plugins": [],
            }

        return await self.resolve_plugins(use_ids)
