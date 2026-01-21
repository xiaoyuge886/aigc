"""
Database service for session persistence
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from loguru import logger

from models.database import Base, SessionDB, MessageDB, ConversationTurnConfigDB, UserFileRelationshipDB
from core.config import settings


class DatabaseService:
    """Service for database operations"""

    def __init__(self, db_path: str = None):
        """
        Initialize database service

        Args:
            db_path: Path to SQLite database file (default: data/sessions.db)
        """
        if db_path is None:
            # 优先使用环境变量指定的数据库路径（用于 Docker 容器）
            import os
            db_path = os.getenv("DB_PATH")

            if db_path is None:
                # 使用项目根目录下的 data/sessions.db（统一数据库位置）
                current_file = Path(__file__)  # backend/services/database.py
                backend_dir = current_file.parent.parent  # backend/
                project_root = backend_dir.parent  # aigc/
                data_dir = project_root / "data"
                data_dir.mkdir(exist_ok=True)
                db_path = str(data_dir / "sessions.db")

        self.db_path = db_path
        self.database_url = f"sqlite+aiosqlite:///{db_path}"

        self.engine = None
        self.async_session = None

    async def initialize(self):
        """Initialize database connection and create tables"""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL query logging
        )

        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info(f"Database initialized at {self.db_path}")

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    async def create_session(
        self,
        session_id: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        permission_mode: Optional[str] = None,
        max_turns: Optional[int] = None,
        timeout_seconds: int = 3600,
        user_id: Optional[int] = None,  # ← 新增：绑定到用户
    ) -> SessionDB:
        """Create a new session in database"""
        async with self.async_session() as session:
            db_session = SessionDB(
                session_id=session_id,
                user_id=user_id,  # ← 绑定到用户
                system_prompt=system_prompt,
                model=model,
                allowed_tools=json.dumps(allowed_tools) if allowed_tools else None,
                permission_mode=permission_mode,
                max_turns=max_turns,
                timeout_seconds=timeout_seconds,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_connected=False,
                is_active=True,
            )
            session.add(db_session)
            await session.commit()
            await session.refresh(db_session)
            return db_session

    async def get_session(self, session_id: str, include_inactive: bool = False) -> Optional[SessionDB]:
        """
        Get session from database
        
        Args:
            session_id: Session ID to look up
            include_inactive: If True, also return inactive sessions (for viewing history)
        """
        async with self.async_session() as session:
            stmt = select(SessionDB).where(SessionDB.session_id == session_id)
            if not include_inactive:
                stmt = stmt.where(SessionDB.is_active == True)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_sessions_by_user(
        self,
        user_id: int,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[SessionDB]:
        """Get all active sessions for a user with pagination"""
        async with self.async_session() as session:
            stmt = (
                select(SessionDB)
                .where(
                    SessionDB.user_id == user_id,
                    SessionDB.is_active == True
                )
                .order_by(SessionDB.last_activity.desc())
            )
            if offset > 0:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_session_activity(self, session_id: str):
        """Update session last activity timestamp"""
        async with self.async_session() as session:
            stmt = (
                update(SessionDB)
                .where(SessionDB.session_id == session_id)
                .values(last_activity=datetime.utcnow())
            )
            await session.execute(stmt)
            await session.commit()

    async def set_session_connected(self, session_id: str, is_connected: bool):
        """Update session connection status"""
        async with self.async_session() as session:
            stmt = (
                update(SessionDB)
                .where(SessionDB.session_id == session_id)
                .values(is_connected=is_connected)
            )
            await session.execute(stmt)
            await session.commit()

    async def update_session_user(self, session_id: str, user_id: int):
        """Update session user binding"""
        async with self.async_session() as session:
            stmt = (
                update(SessionDB)
                .where(SessionDB.session_id == session_id)
                .values(user_id=user_id)
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_session(self, session_id: str) -> bool:
        """Delete session (soft delete by setting is_active=False)"""
        async with self.async_session() as session:
            stmt = (
                update(SessionDB)
                .where(SessionDB.session_id == session_id)
                .values(is_active=False)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def create_message(
        self,
        session_id: str,
        role: str,
        message_type: str,
        content: Optional[str] = None,
        extra_data: Optional[dict] = None,
        result_info: Optional[dict] = None,
        turn_number: int = 1,
        conversation_turn_id: Optional[str] = None,
        parent_message_id: Optional[int] = None,
    ) -> MessageDB:
        """Create a new message in database"""
        async with self.async_session() as session:
            message = MessageDB(
                session_id=session_id,
                role=role,
                message_type=message_type,
                content=content,
                extra_data=extra_data,
                result_info=result_info,
                turn_number=turn_number,
                conversation_turn_id=conversation_turn_id,
                parent_message_id=parent_message_id,
                created_at=datetime.utcnow(),
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[MessageDB]:
        """Get messages for a session with pagination"""
        async with self.async_session() as session:
            stmt = (
                select(MessageDB)
                .where(MessageDB.session_id == session_id)
                .order_by(MessageDB.created_at)
            )
            if offset > 0:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_messages_count(self, session_id: str) -> int:
        """Get total count of messages for a session"""
        async with self.async_session() as session:
            from sqlalchemy import func
            stmt = select(func.count(MessageDB.id)).where(MessageDB.session_id == session_id)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_message_by_id(self, message_id: int) -> Optional[MessageDB]:
        """Get a message by its ID"""
        async with self.async_session() as session:
            stmt = select(MessageDB).where(MessageDB.id == message_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def delete_message(self, message_id: int) -> bool:
        """Delete a message by its ID"""
        async with self.async_session() as session:
            stmt = delete(MessageDB).where(MessageDB.id == message_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def delete_messages_by_session(self, session_id: str) -> int:
        """Delete all messages for a session"""
        async with self.async_session() as session:
            stmt = delete(MessageDB).where(MessageDB.session_id == session_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def cleanup_expired_sessions(self, timeout_seconds: int) -> int:
        """
        Mark sessions as inactive if they've expired

        Returns number of sessions marked inactive
        """
        async with self.async_session() as session:
            from datetime import timedelta

            expiry_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)

            stmt = (
                update(SessionDB)
                .where(
                    SessionDB.last_activity < expiry_time,
                    SessionDB.is_active == True
                )
                .values(is_active=False)
            )
            result = await session.execute(stmt)
            await session.commit()

            count = result.rowcount
            if count > 0:
                logger.info(f"Marked {count} sessions as expired")
            return count

    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        async with self.async_session() as session:
            from sqlalchemy import func
            stmt = select(func.count(SessionDB.session_id)).where(SessionDB.is_active == True)
            result = await session.execute(stmt)
            return result.scalar() or 0
    
    async def get_sessions_count_by_user(self, user_id: int, include_inactive: bool = True) -> int:
        """Get total count of sessions for a user (including inactive if specified)"""
        async with self.async_session() as session:
            from sqlalchemy import func
            stmt = select(func.count(SessionDB.session_id)).where(
                SessionDB.user_id == user_id
            )
            if not include_inactive:
                stmt = stmt.where(SessionDB.is_active == True)
            result = await session.execute(stmt)
            return result.scalar() or 0
    
    async def get_conversation_turns_by_user(
        self,
        user_id: int,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[dict]:
        """Get all conversation turns for a user with details"""
        async with self.async_session() as session:
            # Get all sessions for the user
            stmt = select(SessionDB).where(SessionDB.user_id == user_id)
            result = await session.execute(stmt)
            sessions = list(result.scalars().all())
            
            if not sessions:
                return []
            
            session_ids = [s.session_id for s in sessions]
            
            # Get all conversation turn IDs from messages
            from sqlalchemy import func, distinct
            stmt = (
                select(
                    distinct(MessageDB.conversation_turn_id),
                    MessageDB.session_id,
                    func.min(MessageDB.created_at).label('created_at')
                )
                .where(
                    MessageDB.session_id.in_(session_ids),
                    MessageDB.conversation_turn_id.isnot(None)
                )
                .group_by(MessageDB.conversation_turn_id, MessageDB.session_id)
                .order_by(func.min(MessageDB.created_at).desc())
            )
            if offset > 0:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = await session.execute(stmt)
            turns = result.all()
            
            return [
                {
                    "conversation_turn_id": turn.conversation_turn_id,
                    "session_id": turn.session_id,
                    "created_at": turn.created_at.isoformat() if turn.created_at else None,
                }
                for turn in turns
            ]
    
    async def get_messages_by_conversation_turn(
        self,
        conversation_turn_id: str,
    ) -> List[MessageDB]:
        """Get all messages for a conversation turn"""
        async with self.async_session() as session:
            stmt = (
                select(MessageDB)
                .where(MessageDB.conversation_turn_id == conversation_turn_id)
                .order_by(MessageDB.created_at)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_conversation_turn_config(
        self,
        conversation_turn_id: str,
    ) -> Optional[ConversationTurnConfigDB]:
        """Get configuration used for a conversation turn"""
        async with self.async_session() as session:
            stmt = select(ConversationTurnConfigDB).where(
                ConversationTurnConfigDB.conversation_turn_id == conversation_turn_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def save_conversation_turn_config(
        self,
        conversation_turn_id: str,
        session_id: str,
        user_id: Optional[int],
        final_config: dict,
        config_sources: dict,
        scenario_id: Optional[int] = None,  # 改为整数类型，与数据库字段类型一致
        scenario_name: Optional[str] = None,
    ) -> ConversationTurnConfigDB:
        """Save conversation turn configuration log"""
        async with self.async_session() as session:
            # Check if config already exists (update if exists)
            stmt = select(ConversationTurnConfigDB).where(
                ConversationTurnConfigDB.conversation_turn_id == conversation_turn_id
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing record
                existing.session_id = session_id
                existing.user_id = user_id
                existing.final_config = final_config
                existing.config_sources = config_sources
                existing.scenario_id = scenario_id
                existing.scenario_name = scenario_name
                await session.commit()
                await session.refresh(existing)
                return existing
            else:
                # Create new record
                config_log = ConversationTurnConfigDB(
                    conversation_turn_id=conversation_turn_id,
                    session_id=session_id,
                    user_id=user_id,
                    final_config=final_config,
                    config_sources=config_sources,
                    scenario_id=scenario_id,
                    scenario_name=scenario_name,
                    created_at=datetime.utcnow(),
                )
                session.add(config_log)
                await session.commit()
                await session.refresh(config_log)
                return config_log

    # ==================== File Relationship Methods ====================
    
    async def create_file_relationship(
        self,
        user_id: int,
        session_id: Optional[str],  # 允许 None
        conversation_turn_id: str,  # 必需，不允许 None
        doc_id: str,
        file_name: str,
        file_type: str,
        file_size: Optional[int] = None,
    ) -> UserFileRelationshipDB:
        """
        Create a file relationship record
        
        Args:
            user_id: User ID (required)
            session_id: Session ID (optional, can be None for first conversation)
            conversation_turn_id: Conversation turn ID (required, generated early)
            doc_id: Document ID (required)
            file_name: File name (required)
            file_type: File type (required)
            file_size: File size (optional)
        
        Note:
            session_id can be None initially and bound later when available.
            conversation_turn_id is required and should be generated before file upload.
        """
        async with self.async_session() as session:
            relationship = UserFileRelationshipDB(
                user_id=user_id,
                session_id=session_id,  # Can be None
                conversation_turn_id=conversation_turn_id,  # Required
                doc_id=doc_id,
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(relationship)
            await session.commit()
            await session.refresh(relationship)
            return relationship
    
    async def update_session_id_for_turn(
        self,
        conversation_turn_id: str,
        session_id: str,
        user_id: Optional[int] = None,
    ) -> int:
        """
        Batch update session_id for all records related to a conversation turn
        
        This is called when session_id becomes available (after SDK returns it).
        Updates:
        1. user_file_relationships records
        2. conversation_turn_config records
        
        Args:
            conversation_turn_id: Conversation turn ID
            session_id: Session ID to bind
            user_id: Optional user ID for additional filtering
        
        Returns:
            Number of records updated
        """
        from models.database import ConversationTurnConfigDB
        
        async with self.async_session() as session:
            updated_count = 0
            
            # 1. Update file relationships (only NULL session_id)
            stmt = update(UserFileRelationshipDB).where(
                UserFileRelationshipDB.conversation_turn_id == conversation_turn_id,
                UserFileRelationshipDB.session_id.is_(None)  # Only update NULL records
            )
            if user_id:
                stmt = stmt.where(UserFileRelationshipDB.user_id == user_id)
            
            result = await session.execute(stmt.values(session_id=session_id))
            updated_count += result.rowcount
            
            # 2. Update conversation turn config (empty string or NULL)
            stmt = update(ConversationTurnConfigDB).where(
                ConversationTurnConfigDB.conversation_turn_id == conversation_turn_id
            ).where(
                (ConversationTurnConfigDB.session_id == "") | 
                (ConversationTurnConfigDB.session_id.is_(None))
            ).values(session_id=session_id)
            
            result = await session.execute(stmt)
            updated_count += result.rowcount
            
            await session.commit()
            logger.info(
                f"Updated {updated_count} records with session_id={session_id} "
                f"for conversation_turn_id={conversation_turn_id}"
            )
            return updated_count
    
    async def get_file_relationship(self, doc_id: str) -> Optional[UserFileRelationshipDB]:
        """Get file relationship by doc_id"""
        async with self.async_session() as session:
            stmt = select(UserFileRelationshipDB).where(
                UserFileRelationshipDB.doc_id == doc_id,
                UserFileRelationshipDB.is_active == True
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_session_files(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[UserFileRelationshipDB]:
        """Get all files for a session"""
        async with self.async_session() as session:
            stmt = select(UserFileRelationshipDB).where(
                UserFileRelationshipDB.session_id == session_id,
                UserFileRelationshipDB.is_active == True
            )
            if user_id:
                stmt = stmt.where(UserFileRelationshipDB.user_id == user_id)
            stmt = stmt.order_by(UserFileRelationshipDB.created_at.desc())
            if limit:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_turn_files(
        self,
        conversation_turn_id: str,
        user_id: Optional[int] = None,
    ) -> List[UserFileRelationshipDB]:
        """Get all files for a conversation turn"""
        async with self.async_session() as session:
            stmt = select(UserFileRelationshipDB).where(
                UserFileRelationshipDB.conversation_turn_id == conversation_turn_id,
                UserFileRelationshipDB.is_active == True
            )
            if user_id:
                stmt = stmt.where(UserFileRelationshipDB.user_id == user_id)
            stmt = stmt.order_by(UserFileRelationshipDB.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_user_files(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[UserFileRelationshipDB]:
        """Get all files for a user (optionally filtered by session)"""
        async with self.async_session() as session:
            stmt = select(UserFileRelationshipDB).where(
                UserFileRelationshipDB.user_id == user_id,
                UserFileRelationshipDB.is_active == True
            )
            if session_id:
                stmt = stmt.where(UserFileRelationshipDB.session_id == session_id)
            stmt = stmt.order_by(UserFileRelationshipDB.created_at.desc())
            if limit:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def deactivate_file_relationship(self, doc_id: str) -> bool:
        """Soft delete a file relationship (mark as inactive)"""
        async with self.async_session() as session:
            stmt = update(UserFileRelationshipDB).where(
                UserFileRelationshipDB.doc_id == doc_id
            ).values(is_active=False)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get or create global database service"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
