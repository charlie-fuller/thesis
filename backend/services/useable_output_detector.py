"""Useable Output Detection Service.

Blended approach using multiple signals to detect when AI output becomes useable.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

import pb_client as pb
from repositories import conversations as conversations_repo
from logger_config import get_logger

logger = get_logger(__name__)


# Positive confirmation keywords indicating useable output
CONFIRMATION_KEYWORDS = [
    # Acceptance
    "perfect",
    "exactly",
    "great",
    "excellent",
    "awesome",
    # Gratitude
    "thanks",
    "thank you",
    "appreciate",
    "appreciated",
    # Agreement
    "that works",
    "this works",
    "works for me",
    "sounds good",
    # Completion
    "got it",
    "understood",
    "makes sense",
    "i can work with this",
    "this is what i needed",
    "just what i needed",
    # Positive affirmation
    "yes this is good",
    "yes perfect",
    "thats it",
    "that's it",
    "spot on",
    "bang on",
    "nailed it",
]

# Strong negative indicators (user is still iterating)
ITERATION_KEYWORDS = [
    "actually",
    "but",
    "however",
    "instead",
    "no not",
    "can you change",
    "modify",
    "adjust",
    "fix this",
    "thats not quite",
    "that's not quite",
    "not exactly",
]


def detect_confirmation_keywords(message_content: str) -> bool:
    """Detect if user message contains positive confirmation keywords.

    Args:
        message_content: The user's message content

    Returns:
        True if confirmation detected, False otherwise
    """
    content_lower = message_content.lower().strip()

    # Check for negative indicators first (higher priority)
    if any(keyword in content_lower for keyword in ITERATION_KEYWORDS):
        return False

    # Check for positive confirmation
    return any(keyword in content_lower for keyword in CONFIRMATION_KEYWORDS)


def calculate_turns_to_message(conversation_id: str, message_id: str) -> int:
    """Calculate number of user turns up to and including a specific message.

    Args:
        conversation_id: The conversation ID
        message_id: The message ID to count up to

    Returns:
        Number of user turns
    """
    try:
        # Get the target message timestamp
        target_msg = pb.get_record("messages", message_id)

        if not target_msg:
            return 0

        target_timestamp = target_msg["timestamp"]

        # Count user messages up to this timestamp
        esc_conv = pb.escape_filter(conversation_id)
        esc_ts = pb.escape_filter(target_timestamp)
        user_messages = pb.get_all(
            "messages",
            filter=f"conversation_id='{esc_conv}' && role='user' && timestamp<='{esc_ts}'",
        )

        return len(user_messages)

    except Exception as e:
        logger.error(f"Error calculating turns to message: {e}")
        return 0


def mark_useable_output(conversation_id: str, message_id: str, method: str, user_id: Optional[str] = None) -> bool:
    """Mark a message as useable output in the database.

    Args:
        conversation_id: The conversation ID
        message_id: The assistant message ID that provided useable output
        method: Detection method (user_marked, copy_event, keyword_detected, etc.)
        user_id: Optional user ID for verification

    Returns:
        True if successfully marked, False otherwise
    """
    try:
        # Check if already marked (don't override)
        existing = conversations_repo.get_conversation(conversation_id)

        if existing and existing.get("useable_output_message_id"):
            logger.info(f"Conversation {conversation_id} already has useable output marked")
            return True  # Already marked, that's fine

        # Calculate turns to this message
        turns = calculate_turns_to_message(conversation_id, message_id)

        # Update conversation
        pb.update_record("conversations", conversation_id, {
            "useable_output_message_id": message_id,
            "turns_to_useable_output": turns,
            "useable_output_method": method,
            "useable_output_detected_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(
            f"Marked useable output for conversation {conversation_id}: "
            f"message={message_id}, turns={turns}, method={method}"
        )

        return True

    except Exception as e:
        logger.error(f"Error marking useable output: {e}")
        return False


def auto_detect_useable_output(conversation_id: str) -> Optional[Tuple[str, str, int]]:
    """Automatically detect useable output using multiple signals.

    Checks in priority order:
    1. Copy events (tracked separately)
    2. Keyword analysis in user responses
    3. Function completion (future)
    4. Conversation end pattern (fallback)

    Args:
        conversation_id: The conversation ID to analyze

    Returns:
        Tuple of (message_id, method, turns) if detected, None otherwise
    """
    try:
        # Get all messages in conversation
        esc_conv = pb.escape_filter(conversation_id)
        messages = pb.get_all(
            "messages",
            filter=f"conversation_id='{esc_conv}'",
            sort="timestamp",
        )

        if not messages or len(messages) < 2:
            return None

        # Analyze conversation flow
        for i, msg in enumerate(messages):
            # Skip if not a user message
            if msg["role"] != "user":
                continue

            # Check for confirmation keywords in user message
            if detect_confirmation_keywords(msg["content"]):
                # Previous message (assistant) was the useable output
                if i > 0 and messages[i - 1]["role"] == "assistant":
                    assistant_msg_id = messages[i - 1]["id"]
                    turns = calculate_turns_to_message(conversation_id, assistant_msg_id)
                    logger.info(f"Auto-detected useable output via keywords in conversation {conversation_id}")
                    return (assistant_msg_id, "keyword_detected", turns)

        # Fallback: If conversation has ended naturally (no activity recently)
        # Use the last assistant message
        last_messages = [m for m in messages if m["role"] == "assistant"]
        if last_messages:
            last_assistant_msg = last_messages[-1]
            turns = calculate_turns_to_message(conversation_id, last_assistant_msg["id"])
            return (last_assistant_msg["id"], "conversation_ended", turns)

        return None

    except Exception as e:
        logger.error(f"Error auto-detecting useable output: {e}")
        return None


def process_conversation_for_useable_output(conversation_id: str) -> bool:
    """Process a conversation to detect and mark useable output if not already marked.

    Args:
        conversation_id: The conversation ID

    Returns:
        True if useable output detected/marked, False otherwise
    """
    try:
        # Check if already marked
        existing = conversations_repo.get_conversation(conversation_id)

        if existing and existing.get("useable_output_message_id"):
            return True  # Already marked

        # Auto-detect
        detection = auto_detect_useable_output(conversation_id)

        if detection:
            message_id, method, turns = detection
            return mark_useable_output(conversation_id, message_id, method)

        return False

    except Exception as e:
        logger.error(f"Error processing conversation for useable output: {e}")
        return False
