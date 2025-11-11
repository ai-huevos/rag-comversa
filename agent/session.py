"""
Session Management for Multi-Turn Conversations
Manages conversation history and context for Pydantic AI agent
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Single message in a conversation"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSession:
    """
    Conversation session with multi-turn context

    Attributes:
        session_id: Unique session identifier
        org_id: Organization namespace
        context: Business context (optional)
        messages: Conversation history
        created_at: Session creation time
        updated_at: Last message time
        metadata: Additional session metadata
    """
    session_id: str
    org_id: str
    context: Optional[str] = None
    messages: List[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation"""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_context_messages(self, max_turns: int = 5) -> List[Dict[str, str]]:
        """
        Get recent messages formatted for LLM context

        Args:
            max_turns: Maximum number of user/assistant turns to include

        Returns:
            List of message dicts with role and content
        """
        # Take last max_turns * 2 messages (user + assistant pairs)
        recent = self.messages[-(max_turns * 2):]
        return [{"role": msg.role, "content": msg.content} for msg in recent]


class SessionManager:
    """
    Manages conversation sessions with PostgreSQL persistence

    Stores session history in chat_sessions table for multi-turn context
    and compliance tracking (R16 - 12 month retention for Habeas Data).
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize session manager

        Args:
            db_pool: PostgreSQL connection pool
        """
        self.db_pool = db_pool
        self._memory_cache: Dict[str, ConversationSession] = {}
        self._cache_lock = asyncio.Lock()

    async def get_or_create_session(
        self,
        session_id: Optional[str],
        org_id: str,
        context: Optional[str] = None,
    ) -> ConversationSession:
        """
        Get existing session or create new one

        Args:
            session_id: Session identifier (generates new if None)
            org_id: Organization namespace
            context: Business context

        Returns:
            ConversationSession
        """
        if session_id is None:
            session_id = str(uuid4())

        # Check memory cache first
        async with self._cache_lock:
            if session_id in self._memory_cache:
                logger.debug(f"Session cache hit: {session_id}")
                return self._memory_cache[session_id]

        # Try to load from database
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT
                        session_id,
                        org_id,
                        context,
                        messages,
                        created_at,
                        updated_at,
                        metadata
                    FROM chat_sessions
                    WHERE session_id = $1 AND org_id = $2
                    """,
                    session_id,
                    org_id,
                )

                if row:
                    # Reconstruct session from database
                    messages = [
                        ConversationMessage(
                            role=msg["role"],
                            content=msg["content"],
                            timestamp=datetime.fromisoformat(msg["timestamp"]),
                            metadata=msg.get("metadata", {}),
                        )
                        for msg in row["messages"]
                    ]

                    session = ConversationSession(
                        session_id=row["session_id"],
                        org_id=row["org_id"],
                        context=row["context"],
                        messages=messages,
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        metadata=row["metadata"] or {},
                    )

                    async with self._cache_lock:
                        self._memory_cache[session_id] = session

                    logger.info(f"Loaded session from DB: {session_id}")
                    return session

        except Exception as exc:
            logger.warning(f"Failed to load session from DB: {exc}")

        # Create new session
        session = ConversationSession(
            session_id=session_id,
            org_id=org_id,
            context=context,
        )

        async with self._cache_lock:
            self._memory_cache[session_id] = session

        logger.info(f"Created new session: {session_id}")
        return session

    async def save_session(self, session: ConversationSession) -> None:
        """
        Persist session to database

        Args:
            session: ConversationSession to save
        """
        try:
            messages_json = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in session.messages
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO chat_sessions (
                        session_id,
                        org_id,
                        context,
                        messages,
                        created_at,
                        updated_at,
                        metadata
                    ) VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7::jsonb)
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        context = EXCLUDED.context,
                        messages = EXCLUDED.messages,
                        updated_at = EXCLUDED.updated_at,
                        metadata = EXCLUDED.metadata
                    """,
                    session.session_id,
                    session.org_id,
                    session.context,
                    messages_json,
                    session.created_at,
                    session.updated_at,
                    session.metadata,
                )

            logger.debug(f"Saved session to DB: {session.session_id}")

        except Exception as exc:
            logger.error(f"Failed to save session {session.session_id}: {exc}")
            # Don't raise - allow agent to continue even if persistence fails

    async def add_message_and_save(
        self,
        session: ConversationSession,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add message to session and persist

        Args:
            session: ConversationSession
            role: Message role
            content: Message content
            metadata: Optional metadata
        """
        session.add_message(role, content, metadata)
        await self.save_session(session)

    async def clear_cache(self) -> None:
        """Clear memory cache (useful for testing)"""
        async with self._cache_lock:
            self._memory_cache.clear()
