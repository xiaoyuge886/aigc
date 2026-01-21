"""
Platform configuration API endpoints

Provides user-level and scenario-based configuration management
"""
from typing import List, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from services.database import get_database_service, DatabaseService
from services.configuration_manager import ConfigurationManager
from services.scenario_provider import ScenarioProvider
from services.default_config import DefaultConfig
from models.database import SystemDefaultConfigDB
from sqlalchemy import select, text
from datetime import datetime
from services.default_config import DefaultConfig
from models.database import SystemDefaultConfigDB
from sqlalchemy import select, text
from models.platform import (
    UserConfigCreate,
    UserConfigUpdate,
    UserConfigResponse,
    BusinessScenarioCreate,
    BusinessScenarioUpdate,
    BusinessScenarioResponse,
    SystemPromptCreate,
    SystemPromptUpdate,
    SystemPromptResponse,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    ToolResponse,
    UserScenarioConfigUpdate,
)
from models.schemas import UserLogResponse, SessionLogDetail, ConversationTurnDetail
from models.database import (
    UserConfigDB, BusinessScenarioDB, SystemPromptDB, SkillDB,
    UserScenarioConfigDB, SessionScenarioConfigDB
)
from api.v1.auth import get_current_user, get_current_user_optional
from models.database import UserDB

router = APIRouter(prefix="/platform", tags=["platform"])


def get_configuration_manager(
    db_service: DatabaseService = Depends(get_database_service)
) -> ConfigurationManager:
    """Dependency: Get configuration manager"""
    return ConfigurationManager(db_service)


def is_admin_user(user: UserDB) -> bool:
    """Check if user is admin"""
    return user.role is not None and user.role.name == "admin"


def check_user_permission(current_user: UserDB, target_user_id: int, action: str = "access") -> None:
    """Check if current user has permission to access target user's resources"""
    if current_user.id != target_user_id and not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You can only {action} your own resources"
        )


# =========================================================================
# User Configuration Endpoints
# =========================================================================

@router.post("/users/{user_id}/config", response_model=UserConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_user_config(
    user_id: int,
    config: UserConfigCreate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """
    Create user configuration
    
    Only the user themselves or admin can create their config
    """
    # Check permission
    check_user_permission(current_user, user_id, "create")
    
    # Check if config already exists
    existing = await config_manager.get_user_config(user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User configuration for user_id={user_id} already exists. Use PUT to update."
        )
    
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            # Verify user exists
            stmt = select(UserDB).where(UserDB.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id={user_id} not found"
                )
            
            # Create user config
            user_config = UserConfigDB(
                user_id=user_id,
                default_system_prompt=config.default_system_prompt,
                default_allowed_tools=json.dumps(config.default_allowed_tools) if config.default_allowed_tools else None,
                default_model=config.default_model,
                permission_mode=config.permission_mode,
                max_turns=config.max_turns,
                work_dir=config.work_dir,
                custom_tools=config.custom_tools,
                custom_skills=json.dumps(config.custom_skills) if config.custom_skills else None,
                associated_scenario_id=config.associated_scenario_id,
            )
            session.add(user_config)
            await session.commit()
            await session.refresh(user_config)
            
            logger.info(f"Created user config for user_id={user_id}, associated_scenario_id={config.associated_scenario_id}")
            
            # Convert to response
            return UserConfigResponse(
                user_id=user_config.user_id,
                default_system_prompt=user_config.default_system_prompt,
                default_allowed_tools=json.loads(user_config.default_allowed_tools) if user_config.default_allowed_tools else None,
                default_model=user_config.default_model,
                permission_mode=user_config.permission_mode,
                max_turns=user_config.max_turns,
                work_dir=user_config.work_dir,
                custom_tools=user_config.custom_tools,
                custom_skills=json.loads(user_config.custom_skills) if user_config.custom_skills else None,
                associated_scenario_id=user_config.associated_scenario_id,
                created_at=user_config.created_at.isoformat() + "Z",
                updated_at=user_config.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user config for user_id={user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user configuration: {str(e)}"
        )


@router.get("/users/{user_id}/config", response_model=UserConfigResponse)
async def get_user_config(
    user_id: int,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get user configuration

    Returns default empty configuration if user config doesn't exist.
    This allows frontend to always get a valid response.

    Priority: user_scenario_configs.scenario_ids > user_configs.associated_scenario_id
    """
    from datetime import datetime
    from sqlalchemy import select

    # Check permission
    check_user_permission(current_user, user_id, "view")

    # Step 1: Load user scenario config (优先使用新表)
    scenario_ids = None
    user_custom_prompt = None

    try:
        stmt = select(UserScenarioConfigDB).where(UserScenarioConfigDB.user_id == user_id)
        async with db_service.async_session() as session:
            result = await session.execute(stmt)
            user_scenario_config = result.scalar_one_or_none()

            if user_scenario_config and user_scenario_config.scenario_ids:
                scenario_ids = json.loads(user_scenario_config.scenario_ids)
                user_custom_prompt = user_scenario_config.user_custom_prompt
                logger.info(f"[getUserConfig] User {user_id} has scenario_ids in user_scenario_configs: {scenario_ids}")
    except Exception as e:
        logger.warning(f"[getUserConfig] Failed to load user_scenario_configs for user_id={user_id}: {e}")

    # Step 2: Load user config (用于其他配置项)
    user_config = await config_manager.get_user_config(user_id)

    # Step 3: 如果 user_scenario_configs 没有数据，fallback 到 user_configs.associated_scenario_id
    if scenario_ids is None and user_config and user_config.associated_scenario_id is not None:
        scenario_ids = [user_config.associated_scenario_id]
        logger.info(f"[getUserConfig] User {user_id} fallback to user_configs.associated_scenario_id: {scenario_ids}")

    if not user_config:
        # Return default empty configuration instead of 404
        # This makes it easier for frontend to handle
        now = datetime.utcnow().isoformat() + "Z"
        return UserConfigResponse(
            user_id=user_id,
            default_system_prompt=None,
            default_allowed_tools=None,
            default_model=None,
            permission_mode=None,
            max_turns=None,
            work_dir=None,
            custom_tools=None,
            custom_skills=None,
            associated_scenario_id=scenario_ids[0] if scenario_ids and len(scenario_ids) > 0 else None,  # 向后兼容：返回第一个场景ID
            created_at=now,
            updated_at=now,
        )

    return UserConfigResponse(
        user_id=user_config.user_id,
        default_system_prompt=user_config.default_system_prompt,
        default_allowed_tools=json.loads(user_config.default_allowed_tools) if user_config.default_allowed_tools else None,
        default_model=user_config.default_model,
        permission_mode=user_config.permission_mode,
        max_turns=user_config.max_turns,
        work_dir=user_config.work_dir,
        custom_tools=user_config.custom_tools,
        custom_skills=json.loads(user_config.custom_skills) if user_config.custom_skills else None,
        associated_scenario_id=scenario_ids[0] if scenario_ids and len(scenario_ids) > 0 else None,  # 向后兼容：返回第一个场景ID
        created_at=user_config.created_at.isoformat() + "Z",
        updated_at=user_config.updated_at.isoformat() + "Z",
    )


@router.put("/users/{user_id}/config", response_model=UserConfigResponse)
async def update_user_config(
    user_id: int,
    config: UserConfigUpdate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Update user configuration"""
    # Check permission
    check_user_permission(current_user, user_id, "update")
    
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(UserConfigDB).where(UserConfigDB.user_id == user_id)
            result = await session.execute(stmt)
            user_config = result.scalar_one_or_none()
            
            if not user_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User configuration for user_id={user_id} not found"
                )
            
            # Update fields
            if config.default_system_prompt is not None:
                user_config.default_system_prompt = config.default_system_prompt
            if config.default_allowed_tools is not None:
                user_config.default_allowed_tools = json.dumps(config.default_allowed_tools)
            if config.default_model is not None:
                user_config.default_model = config.default_model
            if config.permission_mode is not None:
                user_config.permission_mode = config.permission_mode
            if config.max_turns is not None:
                user_config.max_turns = config.max_turns
            if config.work_dir is not None:
                user_config.work_dir = config.work_dir
            if config.custom_tools is not None:
                user_config.custom_tools = config.custom_tools
            if config.custom_skills is not None:
                user_config.custom_skills = json.dumps(config.custom_skills)
            # 处理 associated_scenario_id：如果提供了值（包括 None），则更新
            if hasattr(config, 'associated_scenario_id'):
                user_config.associated_scenario_id = config.associated_scenario_id
            
            await session.commit()
            await session.refresh(user_config)
            
            logger.info(f"Updated user config for user_id={user_id}, associated_scenario_id={user_config.associated_scenario_id}")
            
            return UserConfigResponse(
                user_id=user_config.user_id,
                default_system_prompt=user_config.default_system_prompt,
                default_allowed_tools=json.loads(user_config.default_allowed_tools) if user_config.default_allowed_tools else None,
                default_model=user_config.default_model,
                permission_mode=user_config.permission_mode,
                max_turns=user_config.max_turns,
                work_dir=user_config.work_dir,
                custom_tools=user_config.custom_tools,
                custom_skills=json.loads(user_config.custom_skills) if user_config.custom_skills else None,
                associated_scenario_id=user_config.associated_scenario_id,
                created_at=user_config.created_at.isoformat() + "Z",
                updated_at=user_config.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user config for user_id={user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user configuration: {str(e)}"
        )


@router.delete("/users/{user_id}/config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_config(
    user_id: int,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Delete user configuration"""
    # Check permission
    check_user_permission(current_user, user_id, "delete")
    
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(UserConfigDB).where(UserConfigDB.user_id == user_id)
            result = await session.execute(stmt)
            user_config = result.scalar_one_or_none()
            
            if not user_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User configuration for user_id={user_id} not found"
                )
            
            await session.delete(user_config)
            await session.commit()
            
            logger.info(f"Deleted user config for user_id={user_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user config for user_id={user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user configuration: {str(e)}"
        )


# =========================================================================
# Business Scenario Endpoints
# =========================================================================

@router.post("/scenarios", response_model=BusinessScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_business_scenario(
    scenario: BusinessScenarioCreate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Create a business scenario template"""
    try:
        async with config_manager.db_service.async_session() as session:
            # 不再检查 scenario_id，因为使用自增整数 id
            # Create scenario
            # is_default 只能由管理员设置
            is_admin = is_admin_user(current_user)
            is_default_value = scenario.is_default if is_admin else False
            
            business_scenario = BusinessScenarioDB(
                name=scenario.name,
                description=scenario.description,
                category=scenario.category,
                meta=scenario.meta,
                system_prompt=scenario.system_prompt,
                allowed_tools=json.dumps(scenario.allowed_tools) if scenario.allowed_tools else None,
                recommended_model=scenario.recommended_model,
                custom_tools=scenario.custom_tools,
                skills=json.dumps(scenario.skills) if scenario.skills else None,
                workflow=scenario.workflow,
                created_by=current_user.id,
                is_public=scenario.is_public,
                is_default=is_default_value,
            )
            session.add(business_scenario)
            await session.commit()
            await session.refresh(business_scenario)
            
            logger.info(f"Created business scenario id={business_scenario.id} by user_id={current_user.id}")
            
            return BusinessScenarioResponse(
                id=business_scenario.id,
                name=business_scenario.name,
                description=business_scenario.description,
                category=business_scenario.category,
                meta=business_scenario.meta,
                system_prompt=business_scenario.system_prompt,
                allowed_tools=json.loads(business_scenario.allowed_tools) if business_scenario.allowed_tools else None,
                recommended_model=business_scenario.recommended_model,
                custom_tools=business_scenario.custom_tools,
                skills=json.loads(business_scenario.skills) if business_scenario.skills else None,
                workflow=business_scenario.workflow,
                created_by=business_scenario.created_by,
                is_public=business_scenario.is_public,
                is_default=bool(business_scenario.is_default) if hasattr(business_scenario, 'is_default') and business_scenario.is_default is not None else False,
                created_at=business_scenario.created_at.isoformat() + "Z",
                updated_at=business_scenario.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating business scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create business scenario: {str(e)}"
        )


@router.get("/scenarios", response_model=List[BusinessScenarioResponse])
async def list_business_scenarios(
    public_only: bool = False,
    limit: int = 50,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """List business scenarios"""
    try:
        if public_only:
            scenarios = await config_manager.list_public_scenarios(limit=limit)
        else:
            # List user's scenarios if authenticated, otherwise public only
            if current_user:
                scenarios = await config_manager.list_user_scenarios(current_user.id, limit=limit)
                # Also include public scenarios
                public_scenarios = await config_manager.list_public_scenarios(limit=limit)
                # Merge and deduplicate (使用整数ID)
                scenario_ids = {s.id for s in scenarios}
                scenarios.extend([s for s in public_scenarios if s.id not in scenario_ids])
            else:
                scenarios = await config_manager.list_public_scenarios(limit=limit)
        
        return [
            BusinessScenarioResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                category=s.category,
                meta=s.meta,
                system_prompt=s.system_prompt,
                allowed_tools=json.loads(s.allowed_tools) if isinstance(s.allowed_tools, str) else s.allowed_tools,
                recommended_model=s.recommended_model,
                custom_tools=s.custom_tools,
                skills=json.loads(s.skills) if isinstance(s.skills, str) else (s.skills.get("skills") if isinstance(s.skills, dict) else s.skills),
                workflow=s.workflow,
                created_by=s.created_by,
                is_public=s.is_public,
                is_default=bool(s.is_default) if hasattr(s, 'is_default') and s.is_default is not None else False,
                created_at=s.created_at.isoformat() + "Z",
                updated_at=s.updated_at.isoformat() + "Z",
            )
            for s in scenarios
        ]
    except Exception as e:
        logger.error(f"Error listing business scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list business scenarios: {str(e)}"
        )


@router.get("/scenarios/available", response_model=List[dict])
async def get_available_scenarios(
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    获取用户可用的场景列表（用于前端场景选择器）
    
    核心设计原则：
    - 模型驱动：提供场景列表，让模型自主选择和组合
    - 默认场景必须：所有用户都有默认场景
    - 渐进式配置：默认场景 + 公开场景 + 用户私有场景
    
    返回的场景列表包括：
    1. 默认场景（必须，所有用户都有）
    2. 公开场景（is_public=True）
    3. 用户创建的私有场景（如果已登录）
    
    这个接口主要用于前端场景选择器，让用户选择要使用的场景。
    """
    try:
        user_id = current_user.id if current_user else None
        scenario_provider = ScenarioProvider(db_service)
        scenarios = await scenario_provider.get_available_scenarios(user_id=user_id)
        
        logger.info(f"[get_available_scenarios] 用户 {user_id} 可用场景数: {len(scenarios)}")
        
        return scenarios
    except Exception as e:
        logger.error(f"Error getting available scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available scenarios: {str(e)}"
        )


# =========================================================================
# System Default Configuration Endpoints (Admin Only)
# =========================================================================

@router.get("/system-default-config", response_model=dict)
async def get_system_default_config(
    config_key: Optional[str] = None,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    获取系统默认配置（管理员专用）
    
    Args:
        config_key: 配置键（可选），如果不提供则返回所有配置
        current_user: 当前用户（必须是管理员）
        db_service: 数据库服务
        
    Returns:
        dict: 配置信息
    """
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access system default configuration"
        )
    
    try:
        async with db_service.async_session() as session:
            if config_key:
                stmt = select(SystemDefaultConfigDB).where(
                    SystemDefaultConfigDB.config_key == config_key
                )
                result = await session.execute(stmt)
                config = result.scalar_one_or_none()
                if not config:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Configuration key '{config_key}' not found"
                    )
                return {
                    "config_key": config.config_key,
                    "config_value": config.config_value,
                    "description": config.description,
                    "updated_at": config.updated_at.isoformat() + "Z"
                }
            else:
                stmt = select(SystemDefaultConfigDB)
                result = await session.execute(stmt)
                configs = result.scalars().all()
                return {
                    "configs": [
                        {
                            "config_key": c.config_key,
                            "config_value": c.config_value,
                            "description": c.description,
                            "updated_at": c.updated_at.isoformat() + "Z"
                        }
                        for c in configs
                    ]
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system default config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system default config: {str(e)}"
        )


@router.put("/system-default-config/{config_key}", response_model=dict)
async def update_system_default_config(
    config_key: str,
    config_value: str,
    description: Optional[str] = None,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    更新系统默认配置（管理员专用）
    
    Args:
        config_key: 配置键
        config_value: 配置值
        description: 配置描述（可选）
        current_user: 当前用户（必须是管理员）
        db_service: 数据库服务
        
    Returns:
        dict: 更新后的配置信息
    """
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update system default configuration"
        )
    
    try:
        async with db_service.async_session() as session:
            stmt = select(SystemDefaultConfigDB).where(
                SystemDefaultConfigDB.config_key == config_key
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                # 更新现有配置
                config.config_value = config_value
                if description is not None:
                    config.description = description
                config.updated_at = datetime.utcnow()
            else:
                # 创建新配置
                config = SystemDefaultConfigDB(
                    config_key=config_key,
                    config_value=config_value,
                    description=description,
                    updated_at=datetime.utcnow()
                )
                session.add(config)
            
            await session.commit()
            await session.refresh(config)
            
            logger.info(f"[update_system_default_config] Admin {current_user.username} updated system default config: {config_key}")
            
            return {
                "config_key": config.config_key,
                "config_value": config.config_value,
                "description": config.description,
                "updated_at": config.updated_at.isoformat() + "Z"
            }
    except Exception as e:
        logger.error(f"Error updating system default config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system default config: {str(e)}"
        )


# =========================================================================
# User Scenario Configuration Endpoints
# =========================================================================

@router.get("/users/{user_id}/scenario-config", response_model=dict)
async def get_user_scenario_config(
    user_id: int,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """获取用户场景配置"""
    check_user_permission(current_user, user_id, "access")
    
    try:
        async with db_service.async_session() as session:
            stmt = select(UserScenarioConfigDB).where(
                UserScenarioConfigDB.user_id == user_id
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if not config:
                return {
                    "user_id": user_id,
                    "scenario_ids": None,
                    "user_custom_prompt": None,
                    "created_at": None,
                    "updated_at": None
                }
            
            scenario_ids = json.loads(config.scenario_ids) if config.scenario_ids else None
            
            return {
                "user_id": config.user_id,
                "scenario_ids": scenario_ids,
                "user_custom_prompt": config.user_custom_prompt,
                "created_at": config.created_at.isoformat() + "Z",
                "updated_at": config.updated_at.isoformat() + "Z"
            }
    except Exception as e:
        logger.error(f"Error getting user scenario config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user scenario config: {str(e)}"
        )


@router.put("/users/{user_id}/scenario-config", response_model=dict)
async def update_user_scenario_config(
    user_id: int,
    config: UserScenarioConfigUpdate,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """更新用户场景配置（支持多场景选择和自定义prompt）"""
    check_user_permission(current_user, user_id, "update")
    
    try:
        async with db_service.async_session() as session:
            stmt = select(UserScenarioConfigDB).where(
                UserScenarioConfigDB.user_id == user_id
            )
            result = await session.execute(stmt)
            db_config = result.scalar_one_or_none()
            
            if db_config:
                # 更新现有配置
                if config.scenario_ids is not None:
                    db_config.scenario_ids = json.dumps(config.scenario_ids) if config.scenario_ids else None
                if config.user_custom_prompt is not None:
                    db_config.user_custom_prompt = config.user_custom_prompt
                db_config.updated_at = datetime.utcnow()
                logger.info(f"Updated user scenario config for user_id={user_id}, scenario_ids={config.scenario_ids}")
            else:
                # 创建新配置
                db_config = UserScenarioConfigDB(
                    user_id=user_id,
                    scenario_ids=json.dumps(config.scenario_ids) if config.scenario_ids else None,
                    user_custom_prompt=config.user_custom_prompt,
                    updated_at=datetime.utcnow()
                )
                session.add(db_config)
                logger.info(f"Created user scenario config for user_id={user_id}, scenario_ids={config.scenario_ids}")
            
            await session.commit()
            await session.refresh(db_config)
            
            scenario_ids_parsed = json.loads(db_config.scenario_ids) if db_config.scenario_ids else None
            
            logger.info(f"User scenario config saved: user_id={user_id}, scenario_ids={scenario_ids_parsed}, count={len(scenario_ids_parsed) if scenario_ids_parsed else 0}")
            
            return {
                "user_id": db_config.user_id,
                "scenario_ids": scenario_ids_parsed,
                "user_custom_prompt": db_config.user_custom_prompt,
                "created_at": db_config.created_at.isoformat() + "Z",
                "updated_at": db_config.updated_at.isoformat() + "Z"
            }
    except Exception as e:
        logger.error(f"Error updating user scenario config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user scenario config: {str(e)}"
        )


# =========================================================================
# Session Scenario Configuration Endpoints
# =========================================================================

@router.get("/sessions/{session_id}/scenario-config", response_model=dict)
async def get_session_scenario_config(
    session_id: str,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """获取会话场景配置"""
    try:
        async with db_service.async_session() as session:
            from models.database import SessionDB
            stmt = select(SessionDB).where(SessionDB.session_id == session_id)
            result = await session.execute(stmt)
            db_session = result.scalar_one_or_none()
            
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {session_id} not found"
                )
            
            if db_session.user_id and db_session.user_id != current_user.id and not is_admin_user(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access your own sessions"
                )
            
            stmt = select(SessionScenarioConfigDB).where(
                SessionScenarioConfigDB.session_id == session_id
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if not config:
                return {
                    "session_id": session_id,
                    "scenario_ids": None,
                    "session_custom_prompt": None,
                    "created_at": None,
                    "updated_at": None
                }
            
            scenario_ids = json.loads(config.scenario_ids) if config.scenario_ids else None
            
            return {
                "session_id": config.session_id,
                "scenario_ids": scenario_ids,
                "session_custom_prompt": config.session_custom_prompt,
                "created_at": config.created_at.isoformat() + "Z",
                "updated_at": config.updated_at.isoformat() + "Z"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session scenario config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session scenario config: {str(e)}"
        )


@router.put("/sessions/{session_id}/scenario-config", response_model=dict)
async def update_session_scenario_config(
    session_id: str,
    scenario_ids: Optional[List[str]] = None,
    session_custom_prompt: Optional[str] = None,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """更新会话场景配置（支持多场景选择和自定义prompt，覆盖用户配置）"""
    try:
        async with db_service.async_session() as session:
            from models.database import SessionDB
            stmt = select(SessionDB).where(SessionDB.session_id == session_id)
            result = await session.execute(stmt)
            db_session = result.scalar_one_or_none()
            
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {session_id} not found"
                )
            
            if db_session.user_id and db_session.user_id != current_user.id and not is_admin_user(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update your own sessions"
                )
            
            stmt = select(SessionScenarioConfigDB).where(
                SessionScenarioConfigDB.session_id == session_id
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                if scenario_ids is not None:
                    config.scenario_ids = json.dumps(scenario_ids) if scenario_ids else None
                if session_custom_prompt is not None:
                    config.session_custom_prompt = session_custom_prompt
                config.updated_at = datetime.utcnow()
            else:
                config = SessionScenarioConfigDB(
                    session_id=session_id,
                    scenario_ids=json.dumps(scenario_ids) if scenario_ids else None,
                    session_custom_prompt=session_custom_prompt,
                    updated_at=datetime.utcnow()
                )
                session.add(config)
            
            await session.commit()
            await session.refresh(config)
            
            scenario_ids_parsed = json.loads(config.scenario_ids) if config.scenario_ids else None
            
            return {
                "session_id": config.session_id,
                "scenario_ids": scenario_ids_parsed,
                "session_custom_prompt": config.session_custom_prompt,
                "created_at": config.created_at.isoformat() + "Z",
                "updated_at": config.updated_at.isoformat() + "Z"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session scenario config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session scenario config: {str(e)}"
        )


# =========================================================================
# Phase 3: 定时任务管理 API
# =========================================================================

@router.post("/cron/batch-learn-preferences")
async def batch_learn_user_preferences(
    user_ids: Optional[List[int]] = None,
    min_feedback_count: int = 5,
    max_users_per_batch: int = 10,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    手动触发批量用户偏好学习（管理员功能）
    
    用于批量分析用户偏好，更新用户偏好缓存
    """
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can trigger batch preference learning"
        )
    
    try:
        from services.cron_jobs import CronJobs
        from services.agent_service import get_agent_service
        
        cron_jobs = CronJobs(db_service)
        agent_service = get_agent_service()
        
        await cron_jobs.run_user_preference_learning_now(
            user_ids=user_ids,
            agent_service=agent_service
        )
        
        return {
            "success": True,
            "message": "批量用户偏好学习任务已启动"
        }
        
    except Exception as e:
        logger.error(f"Error running batch preference learning: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run batch preference learning: {str(e)}"
        )


@router.get("/users/{user_id}/preferences")
async def get_user_preferences(
    user_id: int,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    获取用户偏好（用户只能查看自己的偏好）
    """
    if current_user.id != user_id and not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own preferences"
        )
    
    try:
        from services.preference_learner import PreferenceLearner
        
        preference_learner = PreferenceLearner(db_service)
        
        # 获取缓存的偏好（不强制刷新）
        preferences = await preference_learner.get_user_preferences(
            user_id=user_id,
            agent_service=None,  # 只返回缓存，不触发模型分析
            force_refresh=False
        )
        
        if preferences is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User preferences not found (user may not have enough feedback data)"
            )
        
        return {
            "preferences": preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user preferences: {str(e)}"
        )


@router.get("/sessions/{session_id}/preferences")
async def get_session_preferences(
    session_id: str,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    获取Session偏好
    """
    try:
        from services.preference_learner import PreferenceLearner

        preference_learner = PreferenceLearner(db_service)

        # 获取Session偏好（当前设计：由 FeedbackCollector 实时更新 SessionPreferencesDB）
        preferences = await preference_learner.get_session_preferences(session_id=session_id) or {}

        # 从基础结构中提取前端需要的字段：
        # - corrections: 从 recent_feedback 中整理出纠正文案（如果存在）
        # - context_preferences / feedback_summary: 目前暂无模型分析结果，先返回 None
        recent_feedback = preferences.get("recent_feedback", []) or []
        corrections = []
        for fb in recent_feedback:
            try:
                if not isinstance(fb, dict):
                    continue
                if fb.get("type") != "correct":
                    continue
                data = fb.get("data") or {}
                if isinstance(data, dict):
                    text = data.get("correct_text") or data.get("reason") or ""
                else:
                    text = str(data)
                text = (text or "").strip()
                if text:
                    corrections.append(text)
            except Exception:
                # 单条解析失败不影响整体
                continue

        return {
            "preferences": {
                "corrections": corrections,
                "context_preferences": None,
                "feedback_summary": None,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session preferences: {str(e)}"
        )


@router.post("/users/{user_id}/preferences/refresh")
async def refresh_user_preferences(
    user_id: int,
    current_user: UserDB = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    刷新用户偏好（强制重新分析）
    """
    if current_user.id != user_id and not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only refresh your own preferences"
        )
    
    try:
        from services.preference_learner import PreferenceLearner
        from services.agent_service import get_agent_service
        
        preference_learner = PreferenceLearner(db_service)
        agent_service = get_agent_service()
        
        # 强制刷新偏好
        preferences = await preference_learner.get_user_preferences(
            user_id=user_id,
            agent_service=agent_service,
            force_refresh=True
        )
        
        if preferences is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to analyze user preferences (may not have enough feedback data)"
            )
        
        return {
            "preferences": preferences,
            "message": "Preferences refreshed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing user preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh user preferences: {str(e)}"
        )


@router.get("/scenarios/{scenario_id}", response_model=BusinessScenarioResponse)
async def get_business_scenario(
    scenario_id: int,  # 改为整数ID
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Get business scenario by id"""
    scenario = await config_manager.get_business_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business scenario with id={scenario_id} not found"
        )
    
    return BusinessScenarioResponse(
        id=scenario.id,
        name=scenario.name,
                description=scenario.description,
                category=scenario.category,
                meta=scenario.meta,
                system_prompt=scenario.system_prompt,
        allowed_tools=json.loads(scenario.allowed_tools) if isinstance(scenario.allowed_tools, str) else scenario.allowed_tools,
        recommended_model=scenario.recommended_model,
        custom_tools=scenario.custom_tools,
        skills=json.loads(scenario.skills) if isinstance(scenario.skills, str) else (scenario.skills.get("skills") if isinstance(scenario.skills, dict) else scenario.skills),
        workflow=scenario.workflow,
        created_by=scenario.created_by,
        is_public=scenario.is_public,
        is_default=bool(scenario.is_default) if hasattr(scenario, 'is_default') and scenario.is_default is not None else False,
        created_at=scenario.created_at.isoformat() + "Z",
        updated_at=scenario.updated_at.isoformat() + "Z",
    )


@router.put("/scenarios/{scenario_id}", response_model=BusinessScenarioResponse)
async def update_business_scenario(
    scenario_id: int,  # 改为整数ID
    scenario: BusinessScenarioUpdate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Update business scenario (only creator or admin can update)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(BusinessScenarioDB).where(
                BusinessScenarioDB.id == scenario_id  # 使用整数ID查询
            )
            result = await session.execute(stmt)
            business_scenario = result.scalar_one_or_none()
            
            if not business_scenario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Business scenario with id={scenario_id} not found"
                )
            
            # Check permission
            is_admin = is_admin_user(current_user)
            is_creator = business_scenario.created_by == current_user.id
            if not (is_admin or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update scenarios you created"
                )
            
            # Update fields
            if scenario.name is not None:
                business_scenario.name = scenario.name
            if scenario.description is not None:
                business_scenario.description = scenario.description
            if scenario.category is not None:
                business_scenario.category = scenario.category
            if scenario.meta is not None:
                business_scenario.meta = scenario.meta
            if scenario.system_prompt is not None:
                business_scenario.system_prompt = scenario.system_prompt
            if scenario.allowed_tools is not None:
                business_scenario.allowed_tools = json.dumps(scenario.allowed_tools)
            if scenario.recommended_model is not None:
                business_scenario.recommended_model = scenario.recommended_model
            if scenario.custom_tools is not None:
                business_scenario.custom_tools = scenario.custom_tools
            if scenario.skills is not None:
                business_scenario.skills = json.dumps(scenario.skills)
            if scenario.workflow is not None:
                business_scenario.workflow = scenario.workflow
            if scenario.is_public is not None:
                business_scenario.is_public = scenario.is_public
            # is_default 只能由管理员设置
            if scenario.is_default is not None:
                if not is_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only admin can set is_default field"
                    )
                business_scenario.is_default = scenario.is_default
            
            await session.commit()
            await session.refresh(business_scenario)
            
            logger.info(f"Updated business scenario id={scenario_id} by user_id={current_user.id}")
            
            return BusinessScenarioResponse(
                id=business_scenario.id,
                name=business_scenario.name,
                description=business_scenario.description,
                category=business_scenario.category,
                meta=business_scenario.meta,
                system_prompt=business_scenario.system_prompt,
                allowed_tools=json.loads(business_scenario.allowed_tools) if business_scenario.allowed_tools else None,
                recommended_model=business_scenario.recommended_model,
                custom_tools=business_scenario.custom_tools,
                skills=json.loads(business_scenario.skills) if business_scenario.skills else None,
                workflow=business_scenario.workflow,
                created_by=business_scenario.created_by,
                is_public=business_scenario.is_public,
                is_default=bool(business_scenario.is_default) if hasattr(business_scenario, 'is_default') and business_scenario.is_default is not None else False,
                created_at=business_scenario.created_at.isoformat() + "Z",
                updated_at=business_scenario.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating business scenario scenario_id={scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update business scenario: {str(e)}"
        )


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_scenario(
    scenario_id: str,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Delete business scenario (only creator or admin can delete)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(BusinessScenarioDB).where(
                BusinessScenarioDB.scenario_id == scenario_id
            )
            result = await session.execute(stmt)
            business_scenario = result.scalar_one_or_none()
            
            if not business_scenario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Business scenario with id={scenario_id} not found"
                )
            
            # Check permission
            is_admin = is_admin_user(current_user)
            is_creator = business_scenario.created_by == current_user.id
            if not (is_admin or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete scenarios you created"
                )
            
            await session.delete(business_scenario)
            await session.commit()
            
            logger.info(f"Deleted business scenario id={scenario_id} by user_id={current_user.id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting business scenario scenario_id={scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete business scenario: {str(e)}"
        )
# =========================================================================
# System Prompt Endpoints
# =========================================================================

@router.post("/system-prompts", response_model=SystemPromptResponse, status_code=status.HTTP_201_CREATED)
async def create_system_prompt(
    prompt_data: SystemPromptCreate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Create a new system prompt (admin only)"""
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create system prompts"
        )
    
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            # 不再检查 prompt_id，因为使用自增整数 id
            system_prompt = SystemPromptDB(
                name=prompt_data.name,
                description=prompt_data.description,
                category=prompt_data.category,
                content=prompt_data.content,
                is_default=prompt_data.is_default or False,
                is_public=prompt_data.is_public or False,
                created_by=current_user.id,
            )
            
            session.add(system_prompt)
            await session.commit()
            await session.refresh(system_prompt)
            
            logger.info(f"Created system prompt id={system_prompt.id} by user_id={current_user.id}")
            
            return SystemPromptResponse(
                id=system_prompt.id,
                name=system_prompt.name,
                description=system_prompt.description,
                category=system_prompt.category,
                content=system_prompt.content,
                usage_count=system_prompt.usage_count,
                is_default=system_prompt.is_default,
                created_by=system_prompt.created_by,
                is_public=system_prompt.is_public,
                created_at=system_prompt.created_at.isoformat() + "Z",
                updated_at=system_prompt.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating system prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create system prompt: {str(e)}"
        )


@router.get("/system-prompts", response_model=List[SystemPromptResponse])
async def list_system_prompts(
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """List all system prompts (public ones or user's own)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text, or_
            stmt = select(SystemPromptDB)
            
            # Filter by category if provided
            if category:
                stmt = stmt.where(SystemPromptDB.category == category)
            
            # Filter by visibility
            if current_user and is_admin_user(current_user):
                # Admin can see all
                if is_public is not None:
                    stmt = stmt.where(SystemPromptDB.is_public == is_public)
            else:
                # Non-admin users can only see public prompts or their own
                if current_user:
                    stmt = stmt.where(
                        or_(
                            SystemPromptDB.is_public == True,
                            SystemPromptDB.created_by == current_user.id
                        )
                    )
                else:
                    # Anonymous users can only see public prompts
                    stmt = stmt.where(SystemPromptDB.is_public == True)
            
            stmt = stmt.order_by(SystemPromptDB.created_at.desc())
            result = await session.execute(stmt)
            prompts = result.scalars().all()
            
            return [
                SystemPromptResponse(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    category=p.category,
                    content=p.content,
                    usage_count=p.usage_count,
                    is_default=p.is_default,
                    created_by=p.created_by,
                    is_public=p.is_public,
                    created_at=p.created_at.isoformat() + "Z",
                    updated_at=p.updated_at.isoformat() + "Z",
                )
                for p in prompts
            ]
    except Exception as e:
        logger.error(f"Error listing system prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list system prompts: {str(e)}"
        )


@router.get("/system-prompts/{prompt_id}", response_model=SystemPromptResponse)
async def get_system_prompt(
    prompt_id: int,  # 改为整数ID
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Get a system prompt by id"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(SystemPromptDB).where(
                SystemPromptDB.id == prompt_id  # 使用整数ID查询
            )
            result = await session.execute(stmt)
            prompt = result.scalar_one_or_none()
            
            if not prompt:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"System prompt with id={prompt_id} not found"
                )
            
            # Check permission
            if not prompt.is_public:
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                if not is_admin_user(current_user) and prompt.created_by != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to access this prompt"
                    )
            
            return SystemPromptResponse(
                id=prompt.id,
                name=prompt.name,
                description=prompt.description,
                category=prompt.category,
                content=prompt.content,
                usage_count=prompt.usage_count,
                is_default=prompt.is_default,
                created_by=prompt.created_by,
                is_public=prompt.is_public,
                created_at=prompt.created_at.isoformat() + "Z",
                updated_at=prompt.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system prompt id={prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system prompt: {str(e)}"
        )


@router.put("/system-prompts/{prompt_id}", response_model=SystemPromptResponse)
async def update_system_prompt(
    prompt_id: int,  # 改为整数ID
    prompt_data: SystemPromptUpdate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Update a system prompt (only creator or admin can update)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(SystemPromptDB).where(
                SystemPromptDB.id == prompt_id  # 使用整数ID查询
            )
            result = await session.execute(stmt)
            prompt = result.scalar_one_or_none()
            
            if not prompt:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"System prompt with id={prompt_id} not found"
                )
            
            # Check permission
            is_admin = is_admin_user(current_user)
            is_creator = prompt.created_by == current_user.id
            if not (is_admin or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update prompts you created"
                )
            
            # Update fields
            if prompt_data.name is not None:
                prompt.name = prompt_data.name
            if prompt_data.description is not None:
                prompt.description = prompt_data.description
            if prompt_data.category is not None:
                prompt.category = prompt_data.category
            if prompt_data.content is not None:
                prompt.content = prompt_data.content
            if prompt_data.is_default is not None:
                prompt.is_default = prompt_data.is_default
            if prompt_data.is_public is not None:
                prompt.is_public = prompt_data.is_public
            
            await session.commit()
            await session.refresh(prompt)
            
            logger.info(f"Updated system prompt id={prompt_id} by user_id={current_user.id}")
            
            return SystemPromptResponse(
                id=prompt.id,
                name=prompt.name,
                description=prompt.description,
                category=prompt.category,
                content=prompt.content,
                usage_count=prompt.usage_count,
                is_default=prompt.is_default,
                created_by=prompt.created_by,
                is_public=prompt.is_public,
                created_at=prompt.created_at.isoformat() + "Z",
                updated_at=prompt.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating system prompt id={prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system prompt: {str(e)}"
        )


@router.delete("/system-prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system_prompt(
    prompt_id: int,  # 改为整数ID
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Delete a system prompt (only creator or admin can delete)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(SystemPromptDB).where(
                SystemPromptDB.id == prompt_id  # 使用整数ID查询
            )
            result = await session.execute(stmt)
            prompt = result.scalar_one_or_none()
            
            if not prompt:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"System prompt with id={prompt_id} not found"
                )
            
            # Check permission
            is_admin = is_admin_user(current_user)
            is_creator = prompt.created_by == current_user.id
            if not (is_admin or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete prompts you created"
                )
            
            await session.delete(prompt)
            await session.commit()
            
            logger.info(f"Deleted system prompt id={prompt_id} by user_id={current_user.id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting system prompt id={prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete system prompt: {str(e)}"
        )


# =========================================================================
# Skill Endpoints
# =========================================================================

@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Create a new skill (admin only)"""
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create skills"
        )
    
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            # 不再检查 skill_id，因为使用自增整数 id
            skill = SkillDB(
                name=skill_data.name,
                description=skill_data.description,
                category=skill_data.category,
                skill_content=skill_data.skill_content,
                skill_config=skill_data.skill_config,
                is_default=skill_data.is_default or False,
                is_public=skill_data.is_public or False,
                created_by=current_user.id,
            )
            
            session.add(skill)
            await session.commit()
            await session.refresh(skill)
            
            logger.info(f"Created skill id={skill.id} by user_id={current_user.id}")
            
            return SkillResponse(
                id=skill.id,
                name=skill.name,
                description=skill.description,
                category=skill.category,
                skill_content=skill.skill_content,
                skill_config=skill.skill_config,
                usage_count=skill.usage_count,
                is_default=skill.is_default,
                created_by=skill.created_by,
                is_public=skill.is_public,
                created_at=skill.created_at.isoformat() + "Z",
                updated_at=skill.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating skill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(e)}"
        )


@router.get("/skills", response_model=List[SkillResponse])
async def list_skills(
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """List all skills (public ones or user's own)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text, or_, func
            stmt = select(SkillDB)
            
            # Count total skills in database (for debugging)
            total_count_stmt = select(func.count(SkillDB.id))
            total_count_result = await session.execute(total_count_stmt)
            total_skills_count = total_count_result.scalar()
            logger.info(f"[list_skills] Total skills in database: {total_skills_count}")
            
            # Filter by category if provided
            if category:
                stmt = stmt.where(SkillDB.category == category)
            
            # Filter by visibility
            is_admin = current_user and is_admin_user(current_user) if current_user else False
            logger.info(f"[list_skills] User: {current_user.id if current_user else 'anonymous'}, is_admin: {is_admin}, is_public param: {is_public}")
            
            if is_admin:
                # Admin can see all skills (unless is_public filter is explicitly set)
                if is_public is not None:
                    stmt = stmt.where(SkillDB.is_public == is_public)
                    logger.info(f"[list_skills] Admin user with is_public filter: {is_public}")
                else:
                    logger.info(f"[list_skills] Admin user - showing all skills (no filter)")
            else:
                # Non-admin users can only see public skills or their own
                if current_user:
                    stmt = stmt.where(
                        or_(
                            SkillDB.is_public == True,
                            SkillDB.created_by == current_user.id
                        )
                    )
                    logger.info(f"[list_skills] Non-admin user {current_user.id} - showing public skills or own skills")
                else:
                    # Anonymous users can only see public skills
                    stmt = stmt.where(SkillDB.is_public == True)
                    logger.info(f"[list_skills] Anonymous user - showing only public skills")
            
            # Count total skills before filtering (for debugging)
            count_stmt = select(func.count(SkillDB.id))
            if category:
                count_stmt = count_stmt.where(SkillDB.category == category)
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()
            logger.info(f"[list_skills] Total skills in database (category={category}): {total_count}")
            
            stmt = stmt.order_by(SkillDB.created_at.desc())
            result = await session.execute(stmt)
            skills = result.scalars().all()
            logger.info(f"[list_skills] Found {len(skills)} skills after filtering")
            
            # Log skill details for debugging
            for s in skills:
                logger.info(f"[list_skills] Skill: id={s.id}, name={s.name}, is_public={s.is_public}, created_by={s.created_by}")
            
        return [
            SkillResponse(
                id=s.id,
                name=s.name,
                    description=s.description,
                    category=s.category,
                    skill_content=s.skill_content,
                    skill_config=s.skill_config,
                    usage_count=s.usage_count,
                    is_default=s.is_default,
                    created_by=s.created_by,
                    is_public=s.is_public,
                    created_at=s.created_at.isoformat() + "Z",
                    updated_at=s.updated_at.isoformat() + "Z",
                )
                for s in skills
            ]
    except Exception as e:
        logger.error(f"Error listing skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {str(e)}"
        )


@router.get("/skills/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,  # 改为整数ID
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Get a skill by id"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(SkillDB).where(
                SkillDB.id == skill_id  # 使用整数ID查询
            )
            result = await session.execute(stmt)
            skill = result.scalar_one_or_none()
            
            if not skill:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Skill with id={skill_id} not found"
                )
            
            # Check permission
            if not skill.is_public:
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                if not is_admin_user(current_user) and skill.created_by != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to access this skill"
                    )
            
            return SkillResponse(
                id=skill.id,
                name=skill.name,
                description=skill.description,
                category=skill.category,
                skill_content=skill.skill_content,
                skill_config=skill.skill_config,
                usage_count=skill.usage_count,
                is_default=skill.is_default,
                created_by=skill.created_by,
                is_public=skill.is_public,
                created_at=skill.created_at.isoformat() + "Z",
                updated_at=skill.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill id={skill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill: {str(e)}"
        )


@router.put("/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,  # 改为整数ID
    skill_data: SkillUpdate,
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Update a skill (only creator or admin can update)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(SkillDB).where(
                SkillDB.id == skill_id  # 使用整数ID查询
            )
            result = await session.execute(stmt)
            skill = result.scalar_one_or_none()
            
            if not skill:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Skill with id={skill_id} not found"
                )
            
            # Check permission
            is_admin = is_admin_user(current_user)
            is_creator = skill.created_by == current_user.id
            if not (is_admin or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update skills you created"
                )
            
            # Update fields
            if skill_data.name is not None:
                skill.name = skill_data.name
            if skill_data.description is not None:
                skill.description = skill_data.description
            if skill_data.category is not None:
                skill.category = skill_data.category
            if skill_data.skill_content is not None:
                skill.skill_content = skill_data.skill_content
            if skill_data.skill_config is not None:
                skill.skill_config = skill_data.skill_config
            if skill_data.is_default is not None:
                skill.is_default = skill_data.is_default
            if skill_data.is_public is not None:
                skill.is_public = skill_data.is_public
            
            await session.commit()
            await session.refresh(skill)
            
            logger.info(f"Updated skill id={skill_id} by user_id={current_user.id}")
            
            return SkillResponse(
                id=skill.id,
                name=skill.name,
                description=skill.description,
                category=skill.category,
                skill_content=skill.skill_content,
                skill_config=skill.skill_config,
                usage_count=skill.usage_count,
                is_default=skill.is_default,
                created_by=skill.created_by,
                is_public=skill.is_public,
                created_at=skill.created_at.isoformat() + "Z",
                updated_at=skill.updated_at.isoformat() + "Z",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating skill id={skill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(e)}"
        )


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,  # 改为整数ID
    current_user: UserDB = Depends(get_current_user),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Delete a skill (only creator or admin can delete)"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text
            stmt = select(SkillDB).where(
                SkillDB.id == skill_id  # 使用整数ID查询
            )
            result = await session.execute(stmt)
            skill = result.scalar_one_or_none()
            
            if not skill:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Skill with id={skill_id} not found"
                )
            
            # Check permission
            is_admin = is_admin_user(current_user)
            is_creator = skill.created_by == current_user.id
            if not (is_admin or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete skills you created"
                )
            
            await session.delete(skill)
            await session.commit()
            
            logger.info(f"Deleted skill id={skill_id} by user_id={current_user.id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting skill id={skill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill: {str(e)}"
        )


# ============================================================================
# Tools Management API
# ============================================================================

@router.get("/tools", response_model=List[ToolResponse])
async def list_tools(
    category: Optional[str] = None,  # standard, custom, user_defined
    tool_type: Optional[str] = None,  # builtin, mcp, skill
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """List all available tools"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text

            # Build base query
            stmt = select(text("*")).select_from(text("tools"))

            # Build conditions
            conditions = []
            params = {}

            if category:
                conditions.append("category = :category")
                params["category"] = category

            if tool_type:
                conditions.append("tool_type = :tool_type")
                params["tool_type"] = tool_type

            # Only show enabled and public tools for non-admin users
            is_admin = current_user and is_admin_user(current_user) if current_user else False
            if not is_admin:
                conditions.append("is_enabled = 1")
                conditions.append("is_public = 1")

            # Apply conditions
            if conditions:
                stmt = stmt.where(text(" AND ".join(conditions)))

            stmt = stmt.order_by(text("category, name"))

            # Execute query
            result = await session.execute(stmt, params)

            tools = []
            for row in result:
                # Format datetime fields
                created_at = row[12]
                updated_at = row[13]

                # Convert to ISO format string if not already
                if isinstance(created_at, datetime):
                    created_at = created_at.isoformat() + "Z"
                elif not isinstance(created_at, str):
                    created_at = str(created_at)

                if isinstance(updated_at, datetime):
                    updated_at = updated_at.isoformat() + "Z"
                elif not isinstance(updated_at, str):
                    updated_at = str(updated_at)

                tools.append(ToolResponse(
                    id=row[0],          # id
                    name=row[1],         # name
                    display_name=row[2], # display_name
                    description=row[3],  # description
                    category=row[4],     # category
                    tool_type=row[5],    # tool_type
                    mcp_server=row[6],   # mcp_server
                    is_enabled=bool(row[8]),   # is_enabled (input_schema is at 7)
                    is_public=bool(row[9]),    # is_public
                    usage_count=row[11], # usage_count
                    created_at=created_at,  # created_at
                    updated_at=updated_at,  # updated_at
                ))

            logger.info(f"[list_tools] Retrieved {len(tools)} tools (category={category}, type={tool_type})")
            return tools

    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/tools/categories")
async def get_tool_categories(
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Get tool categories and statistics"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text

            # Get category statistics
            stmt = select(text("category, COUNT(*) as count, SUM(usage_count) as total_usage")).select_from(text("tools"))

            # Only show enabled and public tools for non-admin users
            is_admin = current_user and is_admin_user(current_user) if current_user else False
            if not is_admin:
                stmt = stmt.where(text("is_enabled = 1 AND is_public = 1"))

            stmt = stmt.group_by(text("category"))

            result = await session.execute(stmt)

            categories = []
            for row in result:
                categories.append({
                    "category": row[0],
                    "count": row[1],
                    "total_usage": row[2] or 0
                })

            return {
                "categories": categories,
                "total_categories": len(categories)
            }

    except Exception as e:
        logger.error(f"Error getting tool categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool categories: {str(e)}"
        )


@router.get("/tools/{tool_name}", response_model=ToolResponse)
async def get_tool(
    tool_name: str,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    config_manager: ConfigurationManager = Depends(get_configuration_manager),
):
    """Get a specific tool by name"""
    try:
        async with config_manager.db_service.async_session() as session:
            from sqlalchemy import select, text

            stmt = select(text("*")).select_from(text("tools")).where(text("name = :tool_name"))
            result = await session.execute(stmt, {"tool_name": tool_name})
            row = result.fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tool '{tool_name}' not found"
                )

            # Check permission for non-public tools
            is_admin = current_user and is_admin_user(current_user) if current_user else False
            if not is_admin and not bool(row[9]):  # is_public (input_schema is at 7)
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

            # Format datetime fields
            created_at = row[12]
            updated_at = row[13]

            # Convert to ISO format string if not already
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat() + "Z"
            elif not isinstance(created_at, str):
                created_at = str(created_at)

            if isinstance(updated_at, datetime):
                updated_at = updated_at.isoformat() + "Z"
            elif not isinstance(updated_at, str):
                updated_at = str(updated_at)

            return ToolResponse(
                id=row[0],
                name=row[1],
                display_name=row[2],
                description=row[3],
                category=row[4],
                tool_type=row[5],
                mcp_server=row[6],
                is_enabled=bool(row[8]),   # is_enabled (input_schema is at 7)
                is_public=bool(row[9]),    # is_public
                usage_count=row[11],
                created_at=created_at,
                updated_at=updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool '{tool_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool: {str(e)}"
        )


@router.get("/users/{user_id}/logs", response_model=UserLogResponse)
async def get_user_logs(
    user_id: int,
    limit: Optional[int] = 50,
    offset: int = 0,
    db_service: DatabaseService = Depends(get_database_service),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Get detailed logs for a user including all sessions and conversation turns.
    
    This endpoint provides a complete audit trail:
    - All sessions for the user
    - All conversation turns in each session
    - All messages, tool calls, and tool results for each turn
    - Configuration used for each turn
    - Cost and token usage
    
    Designed to be compatible with future Elasticsearch migration.
    """
    # Check permissions
    check_user_permission(current_user, user_id, "view logs")
    
    try:
        # Get user info
        from sqlalchemy import select, text
        async with db_service.async_session() as session:
            stmt = select(UserDB).where(UserDB.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found"
                )
            
            # Get all sessions for the user
            from models.database import SessionDB, MessageDB, ConversationTurnConfigDB
            from sqlalchemy import func
            
            # Get total count first
            count_stmt = select(func.count(SessionDB.id)).where(SessionDB.user_id == user_id)
            count_result = await session.execute(count_stmt)
            total_sessions = count_result.scalar() or 0
            
            
            # Get total count first
            count_stmt = select(func.count(SessionDB.id)).where(SessionDB.user_id == user_id)
            count_result = await session.execute(count_stmt)
            if offset > 0:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = await session.execute(stmt)
            db_sessions = list(result.scalars().all())
            
            # Build session details with conversation turns
            sessions_detail = []
            total_turns = 0
            total_cost = 0.0
            total_tokens = 0
            
            for db_session in db_sessions:
                # Get all conversation turn IDs for this session
                stmt = (
                    select(MessageDB.conversation_turn_id)
                    .where(
                        MessageDB.session_id == db_session.session_id,
                        MessageDB.conversation_turn_id.isnot(None)
                    )
                    .distinct()
                )
                result = await session.execute(stmt)
                turn_ids = [row[0] for row in result.all() if row[0]]
                
                # Build conversation turns
                conversation_turns = []
                session_cost = 0.0
                session_tokens = 0
                
                for turn_id in turn_ids:
                    # Get all messages for this turn
                    stmt = select(MessageDB).where(
                        MessageDB.conversation_turn_id == turn_id
                    ).order_by(MessageDB.created_at)
                    result = await session.execute(stmt)
                    messages = list(result.scalars().all())
                    
                    # Get config for this turn
                    stmt = select(ConversationTurnConfigDB).where(
                        ConversationTurnConfigDB.conversation_turn_id == turn_id
                    )
                    result = await session.execute(stmt)
                    turn_config = result.scalar_one_or_none()
                    
                    # Organize messages
                    user_message = None
                    assistant_messages = []
                    tool_calls = []
                    tool_results = []
                    result_info = None
                    turn_cost = 0.0
                    turn_tokens = 0
                    duration_ms = None
                    
                    for msg in messages:
                        msg_dict = {
                            "id": msg.id,
                            "role": msg.role,
                            "message_type": msg.message_type,
                            "content": msg.content,
                            "extra_data": msg.extra_data,
                            "created_at": msg.created_at.isoformat() if msg.created_at else None,
                        }
                        
                        if msg.role == "user":
                            user_message = msg_dict
                        elif msg.role == "assistant":
                            assistant_messages.append(msg_dict)
                            
                            # Extract tool calls from extra_data
                            if msg.extra_data and isinstance(msg.extra_data, dict):
                                if "tool_uses" in msg.extra_data:
                                    tool_calls.extend(msg.extra_data["tool_uses"])
                            
                            # Extract result info
                            if msg.result_info:
                                result_info = msg.result_info
                                if isinstance(result_info, dict):
                                    cost = result_info.get("total_cost_usd") or 0.0
                                    if isinstance(cost, (int, float)):
                                        turn_cost += float(cost)
                                    if "usage" in result_info and isinstance(result_info["usage"], dict):
                                        tokens = result_info["usage"].get("total_tokens") or 0
                                        if isinstance(tokens, (int, float)):
                                            turn_tokens += int(tokens)
                                    if "duration_ms" in result_info:
                                        duration_ms = result_info["duration_ms"]
                        elif msg.message_type == "tool_result":
                            tool_results.append(msg_dict)
                    
                    # Create conversation turn detail
                    turn_detail = ConversationTurnDetail(
                        conversation_turn_id=turn_id,
                        session_id=db_session.session_id,
                        created_at=messages[0].created_at.isoformat() if messages else "",
                        user_message=user_message,
                        assistant_messages=assistant_messages,
                        tool_calls=tool_calls,
                        tool_results=tool_results,
                        config_used=turn_config.final_config if turn_config else None,
                        config_sources=turn_config.config_sources if turn_config else None,
                        result_info=result_info,
                        total_cost_usd=turn_cost if turn_cost > 0 else None,
                        total_tokens=turn_tokens if turn_tokens > 0 else None,
                        duration_ms=duration_ms,
                    )
                    
                    conversation_turns.append(turn_detail)
                    session_cost += turn_cost
                    session_tokens += turn_tokens
                    total_turns += 1
                
                # Create session detail
                session_detail = SessionLogDetail(
                    session_id=db_session.session_id,
                    user_id=db_session.user_id,
                    created_at=db_session.created_at.isoformat() if db_session.created_at else "",
                    last_activity=db_session.last_activity.isoformat() if db_session.last_activity else "",
                    model=db_session.model,
                    system_prompt=db_session.system_prompt,
                    conversation_turns=conversation_turns,
                    total_turns=len(conversation_turns),
                    total_cost_usd=session_cost,
                    total_tokens=session_tokens,
                )
                
                sessions_detail.append(session_detail)
                total_cost += session_cost
                total_tokens += session_tokens
            
            return UserLogResponse(
                user_id=user.id,
                username=user.username,
                total_sessions=total_sessions,
                total_conversation_turns=total_turns,
                total_cost_usd=total_cost,
                sessions=sessions_detail,
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user logs: {str(e)}"
        )

@router.get("/users/{user_id}/sessions")
async def get_user_sessions(
    user_id: int,
    limit: Optional[int] = 50,
    offset: int = 0,
    db_service: DatabaseService = Depends(get_database_service),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Get sessions list for a specific user (admin only or self).
    
    Returns format compatible with /api/v1/sessions endpoint.
    """
    # Check permissions
    check_user_permission(current_user, user_id, "view logs")
    
    try:
        from sqlalchemy import select, text, func
        from models.database import SessionDB
        
        async with db_service.async_session() as session:
            # Get total count
            count_stmt = select(func.count(SessionDB.id)).where(SessionDB.user_id == user_id)
            count_result = await session.execute(count_stmt)
            total_sessions = count_result.scalar() or 0
            
            # Get paginated sessions
            stmt = (
                select(SessionDB)
                .where(SessionDB.user_id == user_id)
                .order_by(SessionDB.created_at.desc())
            )
            if offset > 0:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = await session.execute(stmt)
            db_sessions = list(result.scalars().all())
            
            # Convert to response format
            sessions = []
            for db_session in db_sessions:
                sessions.append({
                    "session_id": db_session.session_id,
                    "created_at": db_session.created_at.isoformat() if db_session.created_at else "",
                    "last_activity": db_session.last_activity.isoformat() if db_session.last_activity else "",
                    "is_connected": False,  # All sessions are disconnected when viewing as admin
                    "model": db_session.model,
                })
            
            # Calculate if there are more sessions
            has_more = total_sessions > (offset + len(sessions))
            
            # Calculate stats directly from database
            from models.database import MessageDB
            
            # Count distinct conversation_turn_ids for this user
            turn_count_stmt = (
                select(func.count(func.distinct(MessageDB.conversation_turn_id)))
                .join(SessionDB, MessageDB.session_id == SessionDB.session_id)
                .where(
                    SessionDB.user_id == user_id,
                    MessageDB.conversation_turn_id.isnot(None)
                )
            )
            turn_result = await session.execute(turn_count_stmt)
            total_turns = turn_result.scalar() or 0
            
            # Calculate total cost from result_info
            cost_stmt = (
                select(MessageDB.result_info)
                .join(SessionDB, MessageDB.session_id == SessionDB.session_id)
                .where(
                    SessionDB.user_id == user_id,
                    MessageDB.result_info.isnot(None)
                )
            )
            cost_result = await session.execute(cost_stmt)
            messages_with_result = cost_result.scalars().all()
            
            total_cost = 0.0
            for result_info in messages_with_result:
                if isinstance(result_info, dict):
                    cost = result_info.get("total_cost_usd")
                    if isinstance(cost, (int, float)) and cost > 0:
                        total_cost += float(cost)
            
            stats = {
                "total_sessions": total_sessions,
                "total_messages": total_turns,  # conversation_turns count
                "total_cost_usd": total_cost,
            }
            
            return {
                "total": total_sessions,
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
                "sessions": sessions,
                "stats": stats,
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user sessions: {str(e)}"
        )