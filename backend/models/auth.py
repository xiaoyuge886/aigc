"""
Pydantic models for authentication and authorization
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")


class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """User response"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role_id: Optional[int] = None
    is_active: bool
    is_verified: bool
    created_at: str
    last_login: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response after successful login"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RoleCreate(BaseModel):
    """Role creation request"""
    name: str = Field(..., min_length=2, max_length=50, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: Optional[dict] = Field(default_factory=dict, description="Role permissions")


class RoleResponse(BaseModel):
    """Role response"""
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[dict] = None
    created_at: str


class UserUpdate(BaseModel):
    """User update request"""
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None)
    role_id: Optional[int] = Field(None)


class PasswordChange(BaseModel):
    """Password change request"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")
