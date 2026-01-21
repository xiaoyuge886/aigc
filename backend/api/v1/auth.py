"""
Authentication API endpoints
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from loguru import logger


# 可选的 Bearer 认证（不自动抛出错误）
optional_security = HTTPBearer(auto_error=False)

from models.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    RoleCreate,
    RoleResponse,
    UserUpdate,
    PasswordChange,
)
from models.database import UserDB
from services.auth import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserDB:
    """Get current authenticated user from JWT token"""
    from services.auth import SECRET_KEY, ALGORITHM
    from jose import jwt

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        # JWT sub field must be a string, convert to int
        sub_value = payload.get("sub")
        if sub_value is None:
            logger.warning("Token validation failed: no user_id in token")
            raise credentials_exception
        
        # Convert sub to int (it might be string or int)
        try:
            user_id: int = int(sub_value) if isinstance(sub_value, str) else sub_value
        except (ValueError, TypeError):
            logger.warning(f"Token validation failed: invalid user_id format: {sub_value}")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise credentials_exception

    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        logger.warning(f"Token validation failed: user_id={user_id} not found")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"Access denied: user '{user.username}' account is disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    logger.debug(f"User authenticated via token: {user.username}")
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[UserDB]:
    """
    可选的用户认证 - 如果有 token 就验证，没有就返回 None

    用于需要支持匿名和认证用户的场景
    """
    if credentials is None:
        logger.debug("No authentication token provided - anonymous access")
        return None

    try:
        # 尝试获取用户
        return await get_current_user(credentials, auth_service)
    except HTTPException:
        # Token 无效，返回 None 而不是抛出错误
        logger.warning("Invalid authentication token - treating as anonymous")
        return None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user"""
    try:
        user = await auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role_id=user.role_id,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login user and return JWT token"""
    user = await auth_service.authenticate_user(
        username=user_data.username,
        password=user_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    # JWT sub field must be a string according to JWT spec
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}  # Convert to string for JWT compliance
    )

    logger.info(f"User logged in successfully: id={user.id}, username={user.username}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role_id=user.role_id,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserDB = Depends(get_current_user),
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        role_id=current_user.role_id,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserDB = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Update current user information"""
    updated_user = await auth_service.update_user(
        user_id=current_user.id,
        full_name=user_update.full_name,
        avatar_url=user_update.avatar_url,
        role_id=user_update.role_id,
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        avatar_url=updated_user.avatar_url,
        role_id=updated_user.role_id,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at.isoformat(),
        last_login=updated_user.last_login.isoformat() if updated_user.last_login else None,
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserDB = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change current user password"""
    success = await auth_service.change_password(
        user_id=current_user.id,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    return {"message": "Password changed successfully"}


# Role management endpoints (admin only)
@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a new role"""
    try:
        role = await auth_service.create_role(
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
        )
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=role.permissions,
            created_at=role.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/roles", response_model=list[RoleResponse])
async def get_roles(
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get all roles"""
    roles = await auth_service.get_roles()
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=role.permissions,
            created_at=role.created_at.isoformat(),
        )
        for role in roles
    ]


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get role by ID"""
    role = await auth_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        created_at=role.created_at.isoformat(),
    )


# =========================================================================
# Admin User Management Endpoints
# =========================================================================

def is_admin_user(user: UserDB) -> bool:
    """Check if user is admin"""
    return user.role is not None and user.role.name == "admin"


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    limit: Optional[int] = None,
    offset: int = 0,
    current_user: UserDB = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get all users (Admin only)"""
    # Check if current user is admin
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access user list"
        )
    
    users = await auth_service.get_all_users(limit=limit, offset=offset)
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role_id=user.role_id,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat() + "Z",
            last_login=user.last_login.isoformat() + "Z" if user.last_login else None,
        )
        for user in users
    ]
