"""
Authentication service for user management and JWT tokens
"""
from datetime import datetime, timedelta
from typing import Optional, List

from jose import JWTError, jwt
from loguru import logger
from sqlalchemy import select

from core.config import settings
from models.database import Base, UserDB, RoleDB, SessionDB
from services.database import DatabaseService


# JWT configuration from settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expire_minutes


class AuthService:
    """Service for user authentication and authorization"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role_id: Optional[int] = None,
    ) -> UserDB:
        """Create a new user"""
        logger.info(f"User registration attempt: username={username}, email={email}")

        async with self.db_service.async_session() as session:
            # Check if username exists
            stmt = select(UserDB).where(UserDB.username == username)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.warning(f"Registration failed: username '{username}' already exists")
                raise ValueError("Username already exists")

            # Check if email exists
            stmt = select(UserDB).where(UserDB.email == email)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.warning(f"Registration failed: email '{email}' already exists")
                raise ValueError("Email already exists")

            # Hash password
            hashed_password = UserDB.hash_password(password)

            # Create user
            user = UserDB(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role_id=role_id,
                is_active=True,
                is_verified=False,
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"User registered successfully: id={user.id}, username={username}, email={email}")
            return user

    async def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> Optional[UserDB]:
        """Authenticate user with username/password"""
        logger.info(f"Login attempt: username={username}")

        async with self.db_service.async_session() as session:
            # Try to find user by username or email
            stmt = select(UserDB).where(
                (UserDB.username == username) | (UserDB.email == username)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Login failed: user '{username}' not found")
                return None

            if not user.is_active:
                logger.warning(f"Login failed: user '{username}' account is disabled")
                raise ValueError("User account is disabled")

            # Verify password
            if not user.verify_password(password):
                logger.warning(f"Login failed: invalid password for user '{username}'")
                return None

            # Update last login
            user.last_login = datetime.utcnow()
            await session.commit()

            logger.info(f"User authenticated successfully: id={user.id}, username={user.username}")
            return user

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        logger.debug(f"JWT token created for user_id={data.get('sub')}, expires={expire}")
        return encoded_jwt

    async def get_user_by_id(self, user_id: int) -> Optional[UserDB]:
        """Get user by ID with role relationship loaded"""
        from sqlalchemy.orm import joinedload
        
        async with self.db_service.async_session() as session:
            stmt = select(UserDB).options(joinedload(UserDB.role)).where(UserDB.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_all_users(self, limit: Optional[int] = None, offset: int = 0) -> List[UserDB]:
        """Get all users with role relationship loaded"""
        from sqlalchemy.orm import joinedload
        
        async with self.db_service.async_session() as session:
            stmt = select(UserDB).options(joinedload(UserDB.role)).order_by(UserDB.created_at.desc())
            if limit:
                stmt = stmt.limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_user_by_username(self, username: str) -> Optional[UserDB]:
        """Get user by username"""
        async with self.db_service.async_session() as session:
            stmt = select(UserDB).where(UserDB.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_user(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        role_id: Optional[int] = None,
    ) -> Optional[UserDB]:
        """Update user information"""
        logger.info(f"User update attempt: user_id={user_id}")

        async with self.db_service.async_session() as session:
            stmt = select(UserDB).where(UserDB.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User update failed: user_id={user_id} not found")
                return None

            if full_name is not None:
                user.full_name = full_name
            if avatar_url is not None:
                user.avatar_url = avatar_url
            if role_id is not None:
                user.role_id = role_id

            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)

            logger.info(f"User updated successfully: id={user.id}, username={user.username}")
            return user

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Change user password"""
        logger.info(f"Password change attempt: user_id={user_id}")

        async with self.db_service.async_session() as session:
            stmt = select(UserDB).where(UserDB.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Password change failed: user_id={user_id} not found")
                return False

            # Verify old password
            if not user.verify_password(old_password):
                logger.warning(f"Password change failed: invalid old password for user '{user.username}'")
                return False

            # Set new password
            user.hashed_password = UserDB.hash_password(new_password)
            user.updated_at = datetime.utcnow()

            await session.commit()
            logger.info(f"Password changed successfully for user: {user.username}")
            return True

    async def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[dict] = None,
    ) -> RoleDB:
        """Create a new role"""
        logger.info(f"Role creation attempt: name={name}")

        async with self.db_service.async_session() as session:
            # Check if role exists
            stmt = select(RoleDB).where(RoleDB.name == name)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.warning(f"Role creation failed: role '{name}' already exists")
                raise ValueError("Role already exists")

            role = RoleDB(
                name=name,
                description=description,
                permissions=permissions or {},
            )

            session.add(role)
            await session.commit()
            await session.refresh(role)

            logger.info(f"Role created successfully: id={role.id}, name={name}")
            return role

    async def get_roles(self) -> list[RoleDB]:
        """Get all roles"""
        async with self.db_service.async_session() as session:
            stmt = select(RoleDB)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_role_by_id(self, role_id: int) -> Optional[RoleDB]:
        """Get role by ID"""
        async with self.db_service.async_session() as session:
            stmt = select(RoleDB).where(RoleDB.id == role_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


# Global auth service instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create global auth service"""
    global _auth_service
    if _auth_service is None:
        from services.database import get_database_service
        _auth_service = AuthService(get_database_service())
    return _auth_service
