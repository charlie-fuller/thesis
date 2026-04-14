"""Conversation management routes.

Handles creation, retrieval, updating, and deletion of conversations.
"""

import os
from typing import Optional

from anthropic import Anthropic
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

import pb_client as pb
from document_processor import process_conversation_to_kb, remove_conversation_from_kb
from logger_config import get_logger
from repositories import conversations as convos_repo
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ============================================================================
# Request/Response Models
# ============================================================================


class ConversationCreateRequest(BaseModel):
    user_id: str
    title: str = "New Conversation"
    client_id: Optional[str] = None
    agent_id: Optional[str] = None  # Link to specific agent for agent-focused chat
    project_id: Optional[str] = None  # Link to specific project for context-aware chat
    initiative_id: Optional[str] = None  # Link to specific initiative for context-aware chat


class ConversationUpdateRequest(BaseModel):
    title: str


class ConversationSearchRequest(BaseModel):
    query: str
    limit: int = 10


class GenerateTitleRequest(BaseModel):
    message: str
    agent_name: Optional[str] = None  # If provided, prefix title with agent name


# ============================================================================
# Conversation CRUD Operations
# ============================================================================


@router.post("/create")
async def create_conversation(request: ConversationCreateRequest):
    """Create a new conversation."""
    try:
        logger.info(f"Creating conversation")

        # Build conversation data
        conversation_data = {
            "title": request.title,
        }
        # Only include agent_id if provided (NULL means auto/coordinator mode)
        if request.agent_id:
            conversation_data["agent_id"] = request.agent_id
        # Include project_id if provided (for project-scoped conversations)
        if request.project_id:
            validate_uuid(request.project_id, "project_id")
            conversation_data["project_id"] = request.project_id
        # Include initiative_id if provided (for initiative-scoped conversations)
        if request.initiative_id:
            validate_uuid(request.initiative_id, "initiative_id")
            conversation_data["initiative_id"] = request.initiative_id

        # Create conversation in database
        conversation = convos_repo.create_conversation(conversation_data)
        logger.info(f"Conversation created: {conversation['id']}")

        return {
            "success": True,
            "conversation_id": conversation["id"],
            "client_id": conversation.get("client_id"),
            "user_id": conversation.get("user_id"),
            "title": conversation["title"],
            "agent_id": conversation.get("agent_id"),
            "project_id": conversation.get("project_id"),
            "initiative_id": conversation.get("initiative_id"),
            "created_at": conversation.get("created"),
        }

    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a single conversation by ID."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        conversation = convos_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get message count
        msg_count = pb.count("messages", filter=f"conversation_id='{pb.escape_filter(conversation_id)}'")
        conversation["message_count"] = msg_count

        return {"success": True, "conversation": conversation}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Fetch messages ordered by created ascending
        messages = convos_repo.get_conversation_messages(conversation_id)

        # Fetch associated documents for each message
        message_ids = [msg["id"] for msg in messages]
        if message_ids:
            # Build a map of message_id -> list of documents
            message_docs_map: dict[str, list] = {}
            for msg_id in message_ids:
                msg_docs = convos_repo.get_message_documents(msg_id)
                if msg_docs:
                    docs_list = []
                    for link in msg_docs:
                        doc_id = link.get("document_id")
                        if doc_id:
                            from repositories import documents as docs_repo
                            doc = docs_repo.get_document(doc_id)
                            if doc:
                                docs_list.append({
                                    "id": doc["id"],
                                    "filename": doc.get("filename"),
                                    "mime_type": doc.get("mime_type"),
                                })
                    if docs_list:
                        message_docs_map[msg_id] = docs_list

            # Attach documents to each message
            for msg in messages:
                msg["documents"] = message_docs_map.get(msg["id"], [])
        else:
            # No messages, so no documents
            for msg in messages:
                msg["documents"] = []

        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages),
        }

    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
):
    """Update conversation (rename)."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        conversation = convos_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        updated = convos_repo.update_conversation(conversation_id, {"title": request.title})
        return {"success": True, "conversation": updated}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Delete messages first (foreign key constraint)
        msgs = convos_repo.get_conversation_messages(conversation_id)
        for msg in msgs:
            convos_repo.delete_message(msg["id"])

        # Delete conversation
        convos_repo.delete_conversation(conversation_id)

        return {"success": True, "message": "Conversation deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{conversation_id}/generate-title")
async def generate_conversation_title(
    conversation_id: str,
    request: GenerateTitleRequest,
):
    """Generate a concise title for a conversation based on the initial message.

    Uses Claude to create a short, descriptive title (3-6 words).
    Optionally prefixes with agent name if a single agent is being used.
    """
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Generate title using Claude
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": f"""Generate a concise title (3-6 words) for a conversation that starts with this message. The title should capture the main topic or intent. Do not use quotes or punctuation. Just output the title, nothing else.

Message: {request.message[:500]}""",
                }
            ],
        )

        # Extract the title from the response
        generated_title = response.content[0].text.strip()

        # If agent name provided, prefix the title with it
        if request.agent_name:
            # Capitalize agent name for display
            agent_display = request.agent_name.capitalize()
            title = f"{agent_display}: {generated_title}"
        else:
            title = generated_title

        # Ensure title is not too long (max 100 chars for UI)
        if len(title) > 100:
            title = title[:97] + "..."

        # Update the conversation title in the database
        existing = convos_repo.get_conversation(conversation_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Conversation not found")

        convos_repo.update_conversation(conversation_id, {"title": title})

        logger.info(f"Generated title for conversation {conversation_id}: {title}")

        return {"success": True, "title": title, "conversation_id": conversation_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating conversation title: {str(e)}")
        # Return a fallback - don't fail the request
        return {"success": False, "title": "New Conversation", "error": str(e)}


# ============================================================================
# Conversation Listing
# ============================================================================


@router.get("")
async def list_conversations(
    user_id: Optional[str] = None,
    client_id: Optional[str] = None,
    project_id: Optional[str] = None,
    initiative_id: Optional[str] = None,
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    """List conversations.

    Supports filtering by project_id and/or initiative_id for context-scoped views.
    """
    try:
        # Build PocketBase filter
        parts = []

        # Filter by project_id if provided
        if project_id:
            validate_uuid(project_id, "project_id")
            parts.append(f"project_id='{pb.escape_filter(project_id)}'")

        # Filter by initiative_id if provided
        if initiative_id:
            validate_uuid(initiative_id, "initiative_id")
            parts.append(f"initiative_id='{pb.escape_filter(initiative_id)}'")

        # Exclude archived by default
        if not include_archived:
            parts.append("(archived=false || archived=null)")

        filter_str = " && ".join(parts)

        # Fetch conversations with pagination
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "conversations",
            filter=filter_str,
            sort="-updated",
            page=page,
            per_page=limit,
        )

        conversations = result.get("items", [])
        total = result.get("totalItems", 0)

        # Get message counts for all conversations
        if conversations:
            for conv in conversations:
                conv["message_count"] = pb.count(
                    "messages",
                    filter=f"conversation_id='{pb.escape_filter(conv['id'])}'",
                )

        return {"success": True, "conversations": conversations, "total": total}

    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Knowledge Base Integration
# ============================================================================


@router.post("/{conversation_id}/add-to-kb")
async def add_conversation_to_knowledge_base(
    conversation_id: str,
    background_tasks: BackgroundTasks,
):
    """Add conversation to knowledge base for RAG search."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Process conversation in background
        background_tasks.add_task(process_conversation_to_kb, conversation_id)

        return {
            "success": True,
            "message": "Conversation is being added to knowledge base",
            "conversation_id": conversation_id,
        }

    except Exception as e:
        logger.error(f"Error adding conversation to KB: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{conversation_id}/remove-from-kb")
async def remove_conversation_from_knowledge_base(conversation_id: str):
    """Remove conversation from knowledge base."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Remove conversation chunks
        remove_conversation_from_kb(conversation_id)

        return {
            "success": True,
            "message": "Conversation removed from knowledge base",
            "conversation_id": conversation_id,
        }

    except Exception as e:
        logger.error(f"Error removing conversation from KB: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Archive/Restore
# ============================================================================


@router.post("/{conversation_id}/archive")
async def archive_conversation(conversation_id: str):
    """Archive a conversation."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        existing = convos_repo.get_conversation(conversation_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Conversation not found")

        updated = convos_repo.update_conversation(conversation_id, {"archived": True})
        return {"success": True, "message": "Conversation archived", "conversation": updated}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{conversation_id}/restore")
async def restore_conversation(conversation_id: str):
    """Restore an archived conversation."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        existing = convos_repo.get_conversation(conversation_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Conversation not found")

        updated = convos_repo.update_conversation(conversation_id, {"archived": False})
        return {"success": True, "message": "Conversation restored", "conversation": updated}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
