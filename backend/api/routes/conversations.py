"""Conversation management routes.

Handles creation, retrieval, updating, and deletion of conversations.
"""

import asyncio
import os
from typing import Optional

from anthropic import Anthropic
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config import get_default_client_id
from database import get_supabase
from document_processor import process_conversation_to_kb, remove_conversation_from_kb
from logger_config import get_logger
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])
supabase = get_supabase()
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ============================================================================
# Request/Response Models
# ============================================================================


class ConversationCreateRequest(BaseModel):
    user_id: str
    title: str = "New Conversation"
    client_id: Optional[str] = None
    agent_id: Optional[str] = None  # Link to specific agent for agent-focused chat


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
async def create_conversation(
    request: ConversationCreateRequest, current_user: dict = Depends(get_current_user)
):
    """Create a new conversation."""
    try:
        # Auto-assign default client if not provided (single-tenant mode)
        client_id = request.client_id or get_default_client_id()
        logger.info(f"💬 Creating conversation for client: {client_id}")

        # Build conversation data
        conversation_data = {
            "client_id": client_id,
            "user_id": request.user_id,
            "title": request.title,
        }
        # Only include agent_id if provided (NULL means auto/coordinator mode)
        if request.agent_id:
            conversation_data["agent_id"] = request.agent_id

        # Create conversation in database
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations").insert(conversation_data).execute()
        )

        conversation = result.data[0]
        logger.info(f"✅ Conversation created: {conversation['id']}")

        return {
            "success": True,
            "conversation_id": conversation["id"],
            "client_id": conversation["client_id"],
            "user_id": conversation["user_id"],
            "title": conversation["title"],
            "agent_id": conversation.get("agent_id"),
            "created_at": conversation["created_at"],
        }

    except Exception as e:
        logger.error(f"❌ Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single conversation by ID."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Fetch conversation with client and user details
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .select("*, clients(name), users(name, email)")
            .eq("id", conversation_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation = result.data

        # Check access: admins can see all, regular users only their own
        is_admin = current_user.get("role") == "admin"
        if not is_admin and conversation.get("user_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get message count
        msg_result = await asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("id", count="exact")
            .eq("conversation_id", conversation_id)
            .execute()
        )
        conversation["message_count"] = msg_result.count or 0

        return {"success": True, "conversation": conversation}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    """Get all messages in a conversation."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Fetch messages ordered by created_at
        result = await asyncio.to_thread(
            lambda: supabase.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )

        messages = result.data

        # Fetch associated documents for each message
        message_ids = [msg["id"] for msg in messages]
        if message_ids:
            # Query message_documents with document details
            docs_result = await asyncio.to_thread(
                lambda: supabase.table("message_documents")
                .select("message_id, document_id, documents(id, filename, mime_type)")
                .in_("message_id", message_ids)
                .execute()
            )

            # Build a map of message_id -> list of documents
            message_docs_map = {}
            for link in docs_result.data:
                msg_id = link["message_id"]
                if msg_id not in message_docs_map:
                    message_docs_map[msg_id] = []

                # Extract document details from the nested join
                doc_data = link.get("documents")
                if doc_data:
                    message_docs_map[msg_id].append(
                        {
                            "id": doc_data["id"],
                            "filename": doc_data["filename"],
                            "mime_type": doc_data.get("mime_type"),
                        }
                    )

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
        logger.error(f"❌ Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update conversation (rename)."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Update conversation title
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .update({"title": request.title})
            .eq("id", conversation_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"success": True, "conversation": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a conversation and all its messages."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Delete messages first (foreign key constraint)
        await asyncio.to_thread(
            lambda: supabase.table("messages")
            .delete()
            .eq("conversation_id", conversation_id)
            .execute()
        )

        # Delete conversation
        await asyncio.to_thread(
            lambda: supabase.table("conversations").delete().eq("id", conversation_id).execute()
        )

        return {"success": True, "message": "Conversation deleted successfully"}

    except Exception as e:
        logger.error(f"❌ Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{conversation_id}/generate-title")
async def generate_conversation_title(
    conversation_id: str,
    request: GenerateTitleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a concise title for a conversation based on the initial message.

    Uses Claude to create a short, descriptive title (3-6 words).
    Optionally prefixes with agent name if a single agent is being used.
    """
    try:
        validate_uuid(conversation_id, "conversation_id")

        # Generate title using Claude
        response = await asyncio.to_thread(
            lambda: anthropic_client.messages.create(
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
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .update({"title": title})
            .eq("id", conversation_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

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
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """List conversations - all for admins, user-specific for regular users."""
    try:
        # Admins can see all conversations, regular users only see their own
        is_admin = current_user.get("role") == "admin"

        # Build query
        query = supabase.table("conversations").select(
            "*, clients(name), users(name, email)", count="exact"
        )

        # Apply filters
        if not is_admin:
            # Regular users can only see their own conversations
            query = query.eq("user_id", current_user["id"])
        elif user_id:
            # Admin filtering by specific user
            query = query.eq("user_id", user_id)

        if client_id:
            query = query.eq("client_id", client_id)

        # Apply ordering and limit
        query = query.order("updated_at", desc=True).limit(limit)

        result = await asyncio.to_thread(lambda: query.execute())

        # Get message counts for all conversations in a single batch query
        conversations = result.data
        if conversations:
            conv_ids = [c["id"] for c in conversations]
            # Single query to get all messages for these conversations
            msg_result = await asyncio.to_thread(
                lambda: supabase.table("messages")
                .select("conversation_id")
                .in_("conversation_id", conv_ids)
                .execute()
            )
            # Count messages per conversation
            msg_counts = {}
            for msg in msg_result.data:
                conv_id = msg["conversation_id"]
                msg_counts[conv_id] = msg_counts.get(conv_id, 0) + 1
            # Apply counts to conversations
            for conv in conversations:
                conv["message_count"] = msg_counts.get(conv["id"], 0)

        return {"success": True, "conversations": conversations, "total": result.count}

    except Exception as e:
        logger.error(f"❌ Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Knowledge Base Integration
# ============================================================================


@router.post("/{conversation_id}/add-to-kb")
async def add_conversation_to_knowledge_base(
    conversation_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
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
        logger.error(f"❌ Error adding conversation to KB: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{conversation_id}/remove-from-kb")
async def remove_conversation_from_knowledge_base(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
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
        logger.error(f"❌ Error removing conversation from KB: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Archive/Restore
# ============================================================================


@router.post("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    """Archive a conversation."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .update({"archived": True})
            .eq("id", conversation_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"success": True, "message": "Conversation archived", "conversation": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error archiving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{conversation_id}/restore")
async def restore_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    """Restore an archived conversation."""
    try:
        validate_uuid(conversation_id, "conversation_id")

        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")
            .update({"archived": False})
            .eq("id", conversation_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"success": True, "message": "Conversation restored", "conversation": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error restoring conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
