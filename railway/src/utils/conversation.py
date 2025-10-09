# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/utils/conversation.py
# PURPOSE: Conversation and message persistence utilities
#
# WHAT IT DOES:
#   - Creates and manages conversations in the database
#   - Stores agent messages and interactions
#   - Tracks conversation metadata
#
# DEPENDENCIES:
#   - psycopg2 (PostgreSQL adapter)
#   - utils.db (database utilities)
#
# USAGE:
#   from utils.conversation import create_conversation, add_message
#
#   conv_id = create_conversation(agent_role="Energy Systems Monitor")
#   add_message(conv_id, role="user", content="What's my battery level?")
#   add_message(conv_id, role="assistant", content="Your battery is at 52%")
# ═══════════════════════════════════════════════════════════════════════════

import json
import uuid
from typing import Optional, Dict, Any, List

from psycopg2.extras import Json
from .db import get_connection, query_one, query_all, execute


# ─────────────────────────────────────────────────────────────────────────────
# Conversation Management
# ─────────────────────────────────────────────────────────────────────────────

def create_conversation(
    agent_role: str,
    user_id: Optional[str] = None,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new conversation.

    Args:
        agent_role: The role of the agent (e.g., "Energy Systems Monitor")
        user_id: Optional user identifier
        title: Optional conversation title
        metadata: Optional metadata dictionary

    Returns:
        str: UUID of the created conversation

    Example:
        >>> conv_id = create_conversation("Energy Systems Monitor")
        >>> print(conv_id)
        'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
    """
    conversation_id = str(uuid.uuid4())

    with get_connection() as conn:
        execute(
            conn,
            """
            INSERT INTO agent.conversations
                (id, agent_role, user_id, title, metadata)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                conversation_id,
                agent_role,
                user_id,
                title,
                Json(metadata or {})
            )
        )

    return conversation_id


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get conversation details by ID.

    Args:
        conversation_id: UUID of the conversation

    Returns:
        Dict with conversation data, or None if not found or invalid UUID
    """
    try:
        with get_connection() as conn:
            return query_one(
                conn,
                "SELECT * FROM agent.conversations WHERE id = %s",
                (conversation_id,)
            )
    except Exception as e:
        # Handle invalid UUID format or other database errors gracefully
        print(f"⚠️  Warning: Could not retrieve conversation {conversation_id}: {e}")
        return None


def update_conversation_summary(
    conversation_id: str,
    title: Optional[str] = None,
    summary: Optional[str] = None
) -> None:
    """
    Update conversation title and/or summary.

    Args:
        conversation_id: UUID of the conversation
        title: New title (optional)
        summary: New summary (optional)
    """
    with get_connection() as conn:
        if title:
            execute(
                conn,
                "UPDATE agent.conversations SET title = %s WHERE id = %s",
                (title, conversation_id)
            )
        if summary:
            execute(
                conn,
                "UPDATE agent.conversations SET summary = %s WHERE id = %s",
                (summary, conversation_id)
            )


# ─────────────────────────────────────────────────────────────────────────────
# Message Management
# ─────────────────────────────────────────────────────────────────────────────

def add_message(
    conversation_id: str,
    role: str,
    content: str,
    agent_role: Optional[str] = None,
    tool_calls: Optional[List[Dict]] = None,
    tool_results: Optional[List[Dict]] = None,
    tokens_used: Optional[int] = None,
    duration_ms: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add a message to a conversation.

    Args:
        conversation_id: UUID of the conversation
        role: Message role ('user', 'assistant', 'system', 'tool')
        content: Message content
        agent_role: Which agent generated this (if assistant)
        tool_calls: List of tool calls made
        tool_results: List of tool results
        tokens_used: Number of tokens used
        duration_ms: Time to generate in milliseconds
        metadata: Optional metadata dictionary

    Returns:
        str: UUID of the created message

    Example:
        >>> msg_id = add_message(
        ...     conv_id,
        ...     role="user",
        ...     content="What's my battery level?"
        ... )
    """
    message_id = str(uuid.uuid4())

    with get_connection() as conn:
        execute(
            conn,
            """
            INSERT INTO agent.messages
                (id, conversation_id, role, content, agent_role,
                 tool_calls, tool_results, tokens_used, duration_ms, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                message_id,
                conversation_id,
                role,
                content,
                agent_role,
                Json(tool_calls or []),
                Json(tool_results or []),
                tokens_used,
                duration_ms,
                Json(metadata or {})
            )
        )

    return message_id


def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """
    Get all messages in a conversation.

    Args:
        conversation_id: UUID of the conversation

    Returns:
        List of message dicts, ordered by created_at

    Example:
        >>> messages = get_conversation_messages(conv_id)
        >>> for msg in messages:
        ...     print(f"{msg['role']}: {msg['content']}")
    """
    with get_connection() as conn:
        return query_all(
            conn,
            """
            SELECT * FROM agent.messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            """,
            (conversation_id,)
        )


def get_recent_conversations(
    agent_role: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get recent conversations, optionally filtered by agent role.

    Args:
        agent_role: Filter by agent role (optional)
        limit: Maximum number to return

    Returns:
        List of conversation dicts, ordered by most recent first
    """
    with get_connection() as conn:
        if agent_role:
            return query_all(
                conn,
                """
                SELECT * FROM agent.conversations
                WHERE agent_role = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (agent_role, limit)
            )
        else:
            return query_all(
                conn,
                """
                SELECT * FROM agent.conversations
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,)
            )


def get_conversation_context(
    agent_role: str,
    current_conversation_id: Optional[str] = None,
    max_conversations: int = 3,
    max_messages_per_conversation: int = 10
) -> str:
    """
    Get formatted conversation context for agent prompts.

    Retrieves recent conversations and formats them as context
    that can be included in agent prompts to provide memory.

    Args:
        agent_role: Agent role to filter conversations
        current_conversation_id: Exclude this conversation (optional)
        max_conversations: Maximum number of past conversations to include
        max_messages_per_conversation: Max messages per conversation

    Returns:
        str: Formatted conversation context, or empty string if no history

    Example:
        >>> context = get_conversation_context("Energy Systems Monitor")
        >>> print(context)
        Previous Conversations:

        [2 hours ago]
        User: What's my battery level?
        Assistant: Your battery is at 52%...
    """
    with get_connection() as conn:
        # Get recent conversations
        query = """
            SELECT id, created_at, title
            FROM agent.conversations
            WHERE agent_role = %s
        """
        params = [agent_role]

        if current_conversation_id:
            query += " AND id != %s"
            params.append(current_conversation_id)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(max_conversations)

        conversations = query_all(conn, query, tuple(params))

        if not conversations:
            return ""

        # Build context string
        context_parts = ["Previous Conversations:\n"]

        for conv in conversations:
            # Calculate time ago
            from datetime import datetime
            created = conv['created_at']
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace('Z', '+00:00'))

            now = datetime.now(created.tzinfo) if created.tzinfo else datetime.utcnow()
            time_diff = now - created

            if time_diff.days > 0:
                time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            else:
                minutes = time_diff.seconds // 60
                time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"

            context_parts.append(f"\n[{time_ago}]")
            if conv.get('title'):
                context_parts.append(f"Topic: {conv['title']}")

            # Get messages for this conversation
            messages = query_all(
                conn,
                """
                SELECT role, content, created_at
                FROM agent.messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                LIMIT %s
                """,
                (conv['id'], max_messages_per_conversation)
            )

            for msg in messages:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content']
                # Truncate long messages
                if len(content) > 200:
                    content = content[:197] + "..."
                context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)


def get_session_context(
    session_id: str,
    max_messages: int = 10
) -> List[Dict[str, Any]]:
    """
    Get conversation context for a specific session.

    Used for multi-turn conversations where user continues
    in the same session/conversation.

    Args:
        session_id: Conversation ID (session identifier)
        max_messages: Maximum messages to retrieve

    Returns:
        List of message dicts in chronological order

    Example:
        >>> messages = get_session_context(conv_id, max_messages=5)
        >>> for msg in messages:
        ...     print(f"{msg['role']}: {msg['content']}")
    """
    with get_connection() as conn:
        return query_all(
            conn,
            """
            SELECT role, content, created_at
            FROM agent.messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            LIMIT %s
            """,
            (session_id, max_messages)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

def log_event(
    level: str,
    event_type: str,
    message: str,
    agent_role: Optional[str] = None,
    conversation_id: Optional[str] = None,
    message_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an agent event.

    Args:
        level: Log level ('debug', 'info', 'warning', 'error')
        event_type: Event type ('task_start', 'task_complete', 'tool_call', 'error')
        message: Log message
        agent_role: Agent role (optional)
        conversation_id: Related conversation ID (optional)
        message_id: Related message ID (optional)
        data: Additional data (optional)

    Example:
        >>> log_event(
        ...     level="info",
        ...     event_type="task_start",
        ...     message="Started processing user query",
        ...     agent_role="Energy Systems Monitor",
        ...     conversation_id=conv_id
        ... )
    """
    with get_connection() as conn:
        execute(
            conn,
            """
            INSERT INTO agent.logs
                (level, event_type, message, agent_role, conversation_id, message_id, data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (level, event_type, message, agent_role, conversation_id, message_id, Json(data or {}))
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test conversation persistence."""
    print("🔍 Testing conversation persistence...")

    # Create a test conversation
    print("\n📝 Creating conversation...")
    conv_id = create_conversation(
        agent_role="Energy Systems Monitor",
        title="Test Conversation"
    )
    print(f"✅ Created conversation: {conv_id}")

    # Add messages
    print("\n💬 Adding messages...")
    add_message(conv_id, role="user", content="What's my battery level?")
    add_message(
        conv_id,
        role="assistant",
        content="Your battery is at 52%",
        agent_role="Energy Systems Monitor",
        duration_ms=1250
    )
    print("✅ Messages added")

    # Retrieve messages
    print("\n📖 Retrieving messages...")
    messages = get_conversation_messages(conv_id)
    print(f"✅ Found {len(messages)} messages:")
    for msg in messages:
        print(f"   {msg['role']}: {msg['content'][:50]}...")

    # Log an event
    print("\n📊 Logging event...")
    log_event(
        level="info",
        event_type="test",
        message="Test event logged",
        conversation_id=conv_id
    )
    print("✅ Event logged")

    print("\n✅ All tests passed!")
