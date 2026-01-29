"""
Context Manager for chat sessions.
Handles session creation, message history, and action tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from models.database import ChatSession, ChatMessage, User


class ContextManager:
    """
    Manages conversation context including session state,
    message history, and reversible action tracking.
    """

    MAX_HISTORY_MESSAGES = 10  # Last N messages for context

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> ChatSession:
        """
        Get existing session or create a new one.

        Args:
            session_id: Optional existing session ID
            user: Optional authenticated user

        Returns:
            ChatSession object
        """
        if session_id:
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            if session:
                # Update last message timestamp
                session.last_message_at = datetime.now(timezone.utc)
                return session

        # Create new session
        session = ChatSession(
            user_id=user.id if user else None,
            context={}
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_message(
        self,
        session: ChatSession,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Add a message to the session history.

        Args:
            session: ChatSession to add message to
            role: 'user', 'assistant', or 'system'
            content: Message content
            metadata: Optional metadata (intent, recommendations, etc.)

        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            session_id=session.id,
            role=role,
            content=content,
            message_metadata=metadata or {}
        )
        self.db.add(message)

        # Update session timestamp
        session.last_message_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_message_history(
        self,
        session: ChatSession,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get message history for context.

        Args:
            session: ChatSession to get history from
            limit: Max messages to return (default: MAX_HISTORY_MESSAGES)

        Returns:
            List of message dicts with role, content, and metadata
        """
        limit = limit or self.MAX_HISTORY_MESSAGES

        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()

        # Reverse to get chronological order
        messages = list(reversed(messages))

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.message_metadata,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]

    def get_formatted_history(
        self,
        session: ChatSession,
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get history formatted for LLM context (just role and content).

        Args:
            session: ChatSession
            limit: Max messages

        Returns:
            List of {"role": ..., "content": ...} dicts
        """
        history = self.get_message_history(session, limit)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]

    def track_action(
        self,
        session: ChatSession,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> None:
        """
        Track a reversible action in session context.

        Args:
            session: ChatSession
            action_type: Type of action (e.g., 'cellar_add', 'cellar_remove', 'rate')
            action_data: Data needed to reverse the action
        """
        # Create a NEW dict to ensure SQLAlchemy detects the change
        context = dict(session.context or {})

        # Initialize actions list if needed
        if "recent_actions" not in context:
            context["recent_actions"] = []
        else:
            # Also copy the list to avoid in-place mutation issues
            context["recent_actions"] = list(context["recent_actions"])

        # Add action to front (most recent first)
        context["recent_actions"].insert(0, {
            "type": action_type,
            "data": action_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep only last 5 actions
        context["recent_actions"] = context["recent_actions"][:5]

        session.context = context
        self.db.commit()

    def get_last_action(self, session: ChatSession) -> Optional[Dict[str, Any]]:
        """
        Get the most recent reversible action.

        Args:
            session: ChatSession

        Returns:
            Action dict or None
        """
        context = session.context or {}
        actions = context.get("recent_actions", [])
        return actions[0] if actions else None

    def pop_last_action(self, session: ChatSession) -> Optional[Dict[str, Any]]:
        """
        Get and remove the most recent action (for undo).

        Args:
            session: ChatSession

        Returns:
            Action dict or None
        """
        # Create a NEW dict to ensure SQLAlchemy detects the change
        context = dict(session.context or {})
        actions = list(context.get("recent_actions", []))

        if not actions:
            return None

        action = actions.pop(0)
        context["recent_actions"] = actions
        session.context = context
        self.db.commit()

        return action

    def update_session_context(
        self,
        session: ChatSession,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update session context with new data.

        Args:
            session: ChatSession
            updates: Dict of context updates to merge
        """
        # Create a NEW dict to ensure SQLAlchemy detects the change
        # (SQLAlchemy may not detect in-place mutations to JSON columns)
        context = dict(session.context or {})
        context.update(updates)
        session.context = context
        self.db.commit()

    def get_recent_wine_references(
        self,
        session: ChatSession,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get recently mentioned/recommended wines from message history.

        Args:
            session: ChatSession
            limit: Max wine references to return

        Returns:
            List of wine reference dicts
        """
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(20).all()

        wine_refs = []
        for msg in messages:
            metadata = msg.message_metadata or {}

            # Check for recommendations in message metadata
            if "recommendations" in metadata:
                for rec in metadata["recommendations"]:
                    wine_refs.append({
                        "wine_id": rec.get("wine_id"),
                        "wine_name": rec.get("wine_name"),
                        "producer": rec.get("producer"),
                        "source": "recommendation"
                    })

            # Check for wine references
            if "wine_reference" in metadata:
                wine_refs.append(metadata["wine_reference"])

            if len(wine_refs) >= limit:
                break

        return wine_refs[:limit]

    def is_returning_user(self, session: ChatSession) -> bool:
        """
        Check if user has previous chat history.

        Args:
            session: ChatSession

        Returns:
            True if user has previous messages
        """
        if not session.user_id:
            return False

        # Check for previous sessions
        prev_sessions = self.db.query(ChatSession).filter(
            ChatSession.user_id == session.user_id,
            ChatSession.id != session.id
        ).count()

        return prev_sessions > 0

    def set_pending_request(
        self,
        session: ChatSession,
        message: str,
        entities: Dict[str, Any]
    ) -> None:
        """
        Store a pending request that needs clarification.

        Args:
            session: ChatSession
            message: Original user message
            entities: Extracted entities
        """
        # Create a NEW dict to ensure SQLAlchemy detects the change
        context = dict(session.context or {})
        context["pending_request"] = {
            "message": message,
            "entities": entities,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        session.context = context
        self.db.commit()

    def get_pending_request(self, session: ChatSession) -> Optional[Dict[str, Any]]:
        """
        Get and clear the pending request.

        Args:
            session: ChatSession

        Returns:
            Pending request dict or None
        """
        # Create a NEW dict to ensure SQLAlchemy detects the change
        context = dict(session.context or {})
        pending = context.pop("pending_request", None)
        if pending:
            session.context = context
            self.db.commit()
        return pending
