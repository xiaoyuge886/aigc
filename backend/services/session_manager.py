"""
Session manager for maintaining multiple agent conversations with SQLite persistence
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from loguru import logger

from services.database import DatabaseService


class AgentSession:
    """Represents a single agent session with Claude SDK client"""

    def __init__(
        self,
        session_id: str,
        options: ClaudeAgentOptions,
        timeout_seconds: int = 3600,
        db_service: Optional[DatabaseService] = None,
    ):
        self.session_id = session_id
        self.options = options
        self.timeout_seconds = timeout_seconds
        self.client: Optional[ClaudeSDKClient] = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.is_connected = False
        self.db_service = db_service
        self.turn_count = 0  # Track message turns

    async def connect(self) -> None:
        """Connect to Claude SDK"""
        if not self.is_connected:
            self.client = ClaudeSDKClient(self.options)
            await self.client.connect()
            self.is_connected = True
            logger.info(f"Session {self.session_id} connected")

            # Update database
            if self.db_service:
                await self.db_service.set_session_connected(self.session_id, True)

    async def disconnect(self) -> None:
        """Disconnect from Claude SDK"""
        if self.client and self.is_connected:
            try:
                await self.client.disconnect()
            except RuntimeError as e:
                # Handle case where client was created in a different task
                # This happens when session is created in one request and deleted in another
                if "cancel scope" in str(e):
                    logger.warning(
                        f"Session {self.session_id} disconnect in different task - "
                        f"cleaning up client reference"
                    )
                    # Just clear the reference - the SDK will clean up internally
                    self.client = None
                    self.is_connected = False
                    return
                raise
            except Exception as e:
                logger.warning(f"Session {self.session_id} error during disconnect: {e}")
            finally:
                # 无论是否有异常，都标记为未连接
                self.is_connected = False
                logger.info(f"Session {self.session_id} disconnected (is_connected={self.is_connected})")

            # Update database
            if self.db_service:
                await self.db_service.set_session_connected(self.session_id, False)
        else:
            logger.debug(f"Session {self.session_id} already disconnected (is_connected={self.is_connected})")

    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    async def update_activity_db(self):
        """Update activity in database"""
        self.update_activity()
        if self.db_service:
            await self.db_service.update_session_activity(self.session_id)

    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.now() - self.last_activity > timedelta(seconds=self.timeout_seconds)

    async def ensure_connected(self) -> None:
        """Ensure client is connected"""
        if not self.is_connected:
            logger.info(f"[ensure_connected] Session {self.session_id} is not connected, connecting...")
            await self.connect()
        else:
            logger.debug(f"[ensure_connected] Session {self.session_id} already connected")


class SessionManager:
    """Manages multiple agent sessions with SQLite persistence"""

    def __init__(
        self,
        max_sessions: int = 100,
        timeout_seconds: int = 3600,
        db_service: Optional[DatabaseService] = None
    ):
        self.max_sessions = max_sessions
        self.timeout_seconds = timeout_seconds
        self.sessions: Dict[str, AgentSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5 minutes
        self._running = False
        self.db_service = db_service

    async def start(self) -> None:
        """Start the session manager and cleanup task"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Load active sessions from database
        if self.db_service:
            await self._load_sessions_from_db()

        logger.info("Session manager started")

    async def _load_sessions_from_db(self):
        """Load active sessions from database on startup"""
        from models.database import SessionDB

        # Note: We only load metadata, not reconnect clients yet
        # Clients will be connected on-demand when needed
        logger.info("Loading sessions from database...")
        # This would require extending DatabaseService to list all active sessions
        # For now, sessions are loaded on-demand via get_session

    async def stop(self) -> None:
        """Stop the session manager and cleanup all sessions"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Disconnect all sessions
        for session in list(self.sessions.values()):
            await session.disconnect()

        # Close database connection
        if self.db_service:
            await self.db_service.close()

        self.sessions.clear()
        logger.info("Session manager stopped")

    async def _cleanup_loop(self) -> None:
        """Periodically cleanup expired sessions"""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)

                # Cleanup memory sessions
                await self.cleanup_expired()

                # Cleanup database sessions
                if self.db_service:
                    await self.db_service.cleanup_expired_sessions(self.timeout_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def cleanup_expired(self) -> int:
        """Remove expired sessions and return count removed"""
        expired = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]

        for session_id in expired:
            await self.remove_session(session_id)
            logger.debug(f"Removed expired session: {session_id}")

        return len(expired)

    async def create_session(
        self,
        options: ClaudeAgentOptions,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,  # ← 新增：用户 ID
    ) -> AgentSession:
        """Create a new session"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        if len(self.sessions) >= self.max_sessions:
            # Try to cleanup expired first
            await self.cleanup_expired()
            if len(self.sessions) >= self.max_sessions:
                raise RuntimeError("Maximum sessions reached")

        # Create session object
        session = AgentSession(
            session_id=session_id,
            options=options,
            timeout_seconds=self.timeout_seconds,
            db_service=self.db_service,
        )

        # Store in memory
        self.sessions[session_id] = session

        # Store in database
        if self.db_service:
            await self.db_service.create_session(
                session_id=session_id,
                user_id=user_id,  # ← 传递 user_id
                system_prompt=getattr(options, 'system_prompt', None),
                model=getattr(options, 'model', None),
                allowed_tools=list(options.allowed_tools) if options.allowed_tools else None,
                permission_mode=getattr(options, 'permission_mode', None),
                max_turns=getattr(options, 'max_turns', None),
                timeout_seconds=self.timeout_seconds,
            )

        logger.info(f"Created session: {session_id} for user: {user_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get an existing session (from memory or database)"""
        # First check memory cache
        session = self.sessions.get(session_id)
        if session:
            if session.is_expired():
                await self.remove_session(session_id)
                return None
            await session.update_activity_db()
            return session

        # If not in memory, check database
        if self.db_service:
            db_session = await self.db_service.get_session(session_id)
            if db_session:
                # Reconstruct AgentSession from database
                options = ClaudeAgentOptions(
                    allowed_tools=json.loads(db_session.allowed_tools) if db_session.allowed_tools else [],
                    permission_mode=db_session.permission_mode or "default",
                    max_turns=db_session.max_turns or 20,
                    model=db_session.model or "sonnet",
                    # 默认不加载 skill，需要用户明确配置
                    # 如果会话创建时用户配置了 custom_skills，会在 agent_config 中设置
                    setting_sources=None,
                )

                if db_session.system_prompt:
                    options.system_prompt = db_session.system_prompt

                session = AgentSession(
                    session_id=db_session.session_id,
                    options=options,
                    timeout_seconds=db_session.timeout_seconds,
                    db_service=self.db_service,
                )

                # Cache in memory
                self.sessions[session_id] = session
                logger.info(f"Loaded session from database: {session_id}")

                return session

        return None

    async def remove_session(self, session_id: str) -> bool:
        """Remove and disconnect a session"""
        # Remove from memory
        session = self.sessions.pop(session_id, None)
        if session:
            try:
                await session.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting session {session_id}: {e}")
                # Continue with cleanup anyway

        # Remove from database
        if self.db_service:
            try:
                await self.db_service.delete_session(session_id)
            except Exception as e:
                logger.error(f"Error deleting session {session_id} from database: {e}")

        logger.info(f"Removed session: {session_id}")
        return True

    def get_session_count(self) -> int:
        """Get current number of active sessions in memory"""
        return len(self.sessions)

    async def save_message(
        self,
        session_id: str,
        role: str,
        message_type: str,
        content: Optional[str] = None,
        extra_data: Optional[dict] = None,
        result_info: Optional[dict] = None,
        conversation_turn_id: Optional[str] = None,
        parent_message_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Save a message to the database
        
        Returns:
            Message ID if saved successfully, None otherwise
        """
        if self.db_service:
            # Get turn number
            session = self.sessions.get(session_id)
            turn_number = session.turn_count + 1 if session else 1

            # For user messages, increment turn count
            # For assistant messages, use the same turn_number as the user message
            if role == "user" and session:
                session.turn_count = turn_number
            elif role == "assistant" and session:
                # Use the same turn_number as the user message in this turn
                turn_number = session.turn_count

            message = await self.db_service.create_message(
                session_id=session_id,
                role=role,
                message_type=message_type,
                content=content,
                extra_data=extra_data,
                result_info=result_info,
                turn_number=turn_number,
                conversation_turn_id=conversation_turn_id,
                parent_message_id=parent_message_id,
            )

            return message.id
        return None

    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """Get message history for a session"""
        if self.db_service:
            messages = await self.db_service.get_messages(session_id, limit)
            return [
                {
                    "role": msg.role,
                    "type": msg.message_type,
                    "content": msg.content,
                    "metadata": msg.extra_data,  # Map to "metadata" for API compatibility
                    "turn_number": msg.turn_number,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ]
        return []


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
