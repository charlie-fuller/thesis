"""
Help Chat API Routes

Provides AI-powered help chat using RAG over help documentation.
Separate from main chat conversations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import anthropic
import os

from database import get_supabase
from auth import get_current_user
from services.embeddings import create_embedding
from logger_config import get_logger

from utils.safe_db import safe_get_first
logger = get_logger(__name__)
router = APIRouter(prefix="/api/help", tags=["help"])
limiter = Limiter(key_func=get_remote_address)

supabase = get_supabase()
claude_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


class HelpChatRequest(BaseModel):
    """Request model for help chat"""
    message: str
    conversation_id: Optional[str] = None  # If continuing conversation
    top_k: int = 3  # Number of help chunks to retrieve (reduced for speed)


class HelpChatResponse(BaseModel):
    """Response model for help chat"""
    conversation_id: str
    message_id: str
    response: str
    sources: List[Dict]  # Referenced help documents


@router.post("/ask")
@limiter.limit("30/minute")
async def ask_help_question(
    request: Request,
    chat_request: HelpChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ask a question to the help system.

    Uses RAG to search help documentation and provide answers with sources.

    **Rate limit**: 30 requests per minute

    **Returns**:
    - conversation_id: ID to continue conversation
    - message_id: ID of assistant message
    - response: AI-generated answer
    - sources: Help documents referenced
    """
    user_id = current_user['id']
    user_role = current_user.get('role', 'user')

    logger.info(
        "Help chat request",
        extra={
            "user_id": user_id,
            "user_role": user_role,
            "message_length": len(chat_request.message),
            "conversation_id": chat_request.conversation_id
        }
    )

    try:
        # Get or create conversation
        if chat_request.conversation_id:
            # Verify user owns this conversation
            conv = supabase.table('help_conversations').select('id').eq(
                'id', chat_request.conversation_id
            ).eq('user_id', user_id).execute()

            if not conv.data:
                raise HTTPException(status_code=404, detail="Conversation not found")

            conversation_id = chat_request.conversation_id

        else:
            # Create new help conversation
            conv = supabase.table('help_conversations').insert({
                'user_id': user_id,
                'title': chat_request.message[:50]  # First 50 chars as title
            }).execute()

            conversation_id = safe_get_first(conv.data)['id']
            logger.info(f"Created new help conversation: {conversation_id}")

        # Step 1: Generate query embedding
        query_embedding = create_embedding(chat_request.message, input_type="query")

        # Step 2: Search help chunks via vector similarity
        help_chunks = supabase.rpc(
            'match_help_chunks',
            {
                'query_embedding': query_embedding,
                'match_count': chat_request.top_k,
                'user_role': user_role
            }
        ).execute()

        if not help_chunks.data:
            logger.warning(f"No help chunks found for query: {chat_request.message[:50]}")
            # Still answer, but without context
            context = "No specific documentation found for this query."
            sources = []
        else:
            # Build context from retrieved chunks
            context_parts = []
            sources = []

            for i, chunk in enumerate(help_chunks.data):
                context_parts.append(
                    f"[Source {i+1}: {chunk['document_title']} - {chunk['heading_context']}]\n{chunk['content']}"
                )

                sources.append({
                    "title": chunk['document_title'],
                    "section": chunk['heading_context'],
                    "file_path": chunk['file_path'],
                    "similarity": chunk['similarity']
                })

            context = "\n\n---\n\n".join(context_parts)

        # Step 3: Get conversation history
        history = supabase.table('help_messages').select(
            'role, content'
        ).eq('conversation_id', conversation_id).order('timestamp').execute()

        # Step 4: Build system prompt for help assistant
        system_prompt = f"""You are a helpful assistant for the SuperAssistant platform.

Your role is to answer questions about:
- How to use the admin dashboard
- Understanding metrics and KPIs (Ideation Velocity, Correction Loop, TRIPS)
- How the Solomon Engine works
- Onboarding new clients
- Managing documents and system instructions
- Troubleshooting issues
- Understanding the Bradbury Impact Loop framework
- Technical details about the system

CRITICAL INSTRUCTIONS FOR ANSWERING:

1. **PROCESS/HOW-TO QUESTIONS** (highest priority):
   - If the documentation contains step-by-step instructions, YOU MUST include ALL steps verbatim
   - NEVER summarize or skip steps from documented processes
   - If documentation shows 7 steps, your answer MUST include all 7 steps
   - Use the EXACT formatting from the documentation (numbered lists, bold text, etc.)
   - Include ALL details: tab names, button names, dropdown selections, everything
   - After listing all steps, you MAY offer: "Would you like more detail on any step?"

2. **NAVIGATION PATHS** (critical for all how-to questions):
   - **ALWAYS** include the complete navigation path from the documentation
   - Use **bold** for page names, tab names, and button names exactly as shown in docs
   - Format: "Navigate to **Page Name** → **Tab Name** → **Button/Option**"
   - Include every intermediate step (e.g., if you need to click a tab, say so)
   - Be explicit about WHERE to click, not just WHAT to do

3. **CONCEPTUAL/EXPLANATION QUESTIONS**:
   - Keep answers concise (2-4 sentences) unless documentation provides more detail
   - If documentation has extensive explanation, provide the key points
   - Offer more detail: "Would you like more information about [specific aspect]?"

4. **ACCURACY RULES**:
   - If documentation directly answers the question, quote or paraphrase it EXACTLY
   - Do NOT invent steps, simplify processes, or skip documented details
   - If unsure or documentation is unclear, say so immediately
   - Never contradict the documentation

DOCUMENTATION CONTEXT:
{context}

If the documentation doesn't cover the user's question, acknowledge this briefly and provide general guidance if possible."""

        # Step 5: Generate response using Claude
        messages = [
            {"role": msg['role'], "content": msg['content']}
            for msg in history.data
        ] + [
            {"role": "user", "content": chat_request.message}
        ]

        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Sonnet 4.5 for help responses
            max_tokens=1500,  # Increased to allow complete process documentation (was 500, too restrictive)
            system=system_prompt,
            messages=messages
        )

        assistant_response = response.content[0].text

        # Step 6: Save messages to database
        # Save user message
        user_msg = supabase.table('help_messages').insert({
            'conversation_id': conversation_id,
            'role': 'user',
            'content': chat_request.message
        }).execute()

        # Save assistant message with sources
        assistant_msg = supabase.table('help_messages').insert({
            'conversation_id': conversation_id,
            'role': 'assistant',
            'content': assistant_response,
            'sources': sources
        }).execute()

        message_id = safe_get_first(assistant_msg.data)['id']

        logger.info(
            "Help response generated",
            extra={
                "conversation_id": conversation_id,
                "message_id": message_id,
                "sources_count": len(sources),
                "response_length": len(assistant_response)
            }
        )

        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "response": assistant_response,
            "sources": sources
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in help chat: {e}")
        logger.error(f"Full traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error generating help response: {str(e)}")


@router.get("/conversations")
@limiter.limit("60/minute")
async def get_help_conversations(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all help conversations for current user.

    Returns list of conversations with message counts.
    """
    user_id = current_user['id']

    try:
        conversations = supabase.table('help_conversations').select(
            'id, title, created_at, updated_at'
        ).eq('user_id', user_id).order('updated_at', desc=True).execute()

        # Get message counts for each conversation
        result = []
        for conv in conversations.data:
            messages = supabase.table('help_messages').select(
                'id', count='exact'
            ).eq('conversation_id', conv['id']).execute()

            result.append({
                **conv,
                "message_count": messages.count
            })

        return result

    except Exception as e:
        logger.error(f"Error fetching help conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
@limiter.limit("60/minute")
async def get_help_conversation(
    request: Request,
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get full conversation history with messages.
    """
    user_id = current_user['id']

    try:
        # Verify ownership
        conv = supabase.table('help_conversations').select('*').eq(
            'id', conversation_id
        ).eq('user_id', user_id).execute()

        if not conv.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        messages = supabase.table('help_messages').select(
            'id, role, content, sources, timestamp'
        ).eq('conversation_id', conversation_id).order('timestamp').execute()

        return {
            **safe_get_first(conv.data),
            "messages": messages.data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching help conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
@limiter.limit("30/minute")
async def delete_help_conversation(
    request: Request,
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a help conversation and all its messages.
    """
    user_id = current_user['id']

    try:
        # Verify ownership
        conv = supabase.table('help_conversations').select('id').eq(
            'id', conversation_id
        ).eq('user_id', user_id).execute()

        if not conv.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Delete conversation (messages cascade)
        supabase.table('help_conversations').delete().eq('id', conversation_id).execute()

        return {"status": "deleted", "conversation_id": conversation_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting help conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{message_id}")
@limiter.limit("100/minute")
async def submit_help_feedback(
    request: Request,
    message_id: str,
    feedback: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit feedback (thumbs up/down) for a help message.

    **Parameters**:
    - message_id: ID of the assistant message
    - feedback: 1 for thumbs up, -1 for thumbs down
    """
    if feedback not in [-1, 1]:
        raise HTTPException(status_code=400, detail="Feedback must be 1 (thumbs up) or -1 (thumbs down)")

    user_id = current_user['id']

    try:
        # Verify message exists and belongs to user's conversation
        message = supabase.table('help_messages').select(
            'id, conversation_id'
        ).eq('id', message_id).execute()

        if not message.data:
            raise HTTPException(status_code=404, detail="Message not found")

        conversation_id = safe_get_first(message.data)['conversation_id']

        # Verify user owns the conversation
        conv = supabase.table('help_conversations').select('id').eq(
            'id', conversation_id
        ).eq('user_id', user_id).execute()

        if not conv.data:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update feedback
        from datetime import datetime
        supabase.table('help_messages').update({
            'feedback': feedback,
            'feedback_timestamp': datetime.utcnow().isoformat()
        }).eq('id', message_id).execute()

        logger.info(f"Feedback recorded: message={message_id}, feedback={feedback}, user={user_id}")

        return {
            "status": "success",
            "message_id": message_id,
            "feedback": feedback
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
@limiter.limit("60/minute")
async def search_help_docs(
    request: Request,
    query: str,
    top_k: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Search help documentation directly (without starting a conversation).

    Useful for quick lookups or autocomplete.

    **Query Parameters**:
    - query: Search query
    - top_k: Number of results to return (default: 10, max: 20)

    **Returns**:
    - List of relevant help chunks with sources
    """
    user_role = current_user.get('role', 'user')

    # Cap top_k
    top_k = min(top_k, 20)

    try:
        # Generate query embedding
        query_embedding = create_embedding(query, input_type="query")

        # Search help chunks
        results = supabase.rpc(
            'match_help_chunks',
            {
                'query_embedding': query_embedding,
                'match_count': top_k,
                'user_role': user_role
            }
        ).execute()

        return {
            "query": query,
            "results": results.data
        }

    except Exception as e:
        logger.error(f"Error searching help docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
@limiter.limit("60/minute")
async def get_help_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics about help documentation.

    Admin-only endpoint.

    **Returns**:
    - Total documents
    - Total chunks
    - Documents by category
    - Most referenced sources
    """
    user_role = current_user.get('role', 'user')

    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get counts
        doc_count = supabase.table('help_documents').select('id', count='exact').execute()
        chunk_count = supabase.table('help_chunks').select('id', count='exact').execute()

        # Documents by category
        docs_by_category = supabase.table('help_documents').select(
            'category'
        ).execute()

        category_counts = {}
        for doc in docs_by_category.data:
            cat = doc['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Most recent updates
        recent_docs = supabase.table('help_documents').select(
            'title, category, updated_at'
        ).order('updated_at', desc=True).limit(5).execute()

        return {
            "total_documents": doc_count.count,
            "total_chunks": chunk_count.count,
            "documents_by_category": category_counts,
            "recent_updates": recent_docs.data
        }

    except Exception as e:
        logger.error(f"Error fetching help stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def help_system_status():
    """
    Public endpoint to check help system status (no auth required for debugging).
    Shows if help documentation has been indexed and database connectivity.
    """
    try:
        # Get counts
        doc_count = supabase.table('help_documents').select('id', count='exact').execute()
        chunk_count = supabase.table('help_chunks').select('id', count='exact').execute()

        return {
            "status": "operational",
            "total_documents": doc_count.count if doc_count else 0,
            "total_chunks": chunk_count.count if chunk_count else 0,
            "database_connected": True,
            "indexed": chunk_count.count > 0 if chunk_count else False
        }

    except Exception as e:
        logger.error(f"Error checking help status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "database_connected": False,
            "indexed": False
        }


@router.get("/test-search")
async def test_help_search():
    """
    Debug endpoint to test the full search pipeline (no auth required).
    Tests embedding generation and vector search.
    """
    try:
        test_query = "How do I onboard a new client?"

        # Step 1: Test embedding generation
        query_embedding = create_embedding(test_query, input_type="query")
        embedding_len = len(query_embedding)

        # Step 2: Test RPC call
        help_chunks = supabase.rpc(
            'match_help_chunks',
            {
                'query_embedding': query_embedding,
                'match_count': 3,
                'user_role': 'admin'
            }
        ).execute()

        return {
            "status": "success",
            "test_query": test_query,
            "embedding_dimension": embedding_len,
            "chunks_found": len(help_chunks.data) if help_chunks.data else 0,
            "sample_results": [
                {
                    "title": chunk['document_title'],
                    "section": chunk['heading_context'],
                    "similarity": chunk['similarity']
                }
                for chunk in (help_chunks.data[:3] if help_chunks.data else [])
            ]
        }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/index-docs")
@limiter.limit("1/hour")
async def index_help_docs(
    request: Request,
    current_user: dict = Depends(get_current_user),
    force: bool = False
):
    """
    Index or reindex help documentation.

    Admin-only endpoint for one-time setup or updates.
    This runs the indexing script to process markdown files into searchable chunks.

    **Query Parameters**:
    - force: If True, reindex all documents even if they exist (default: False)

    **Rate limit**: 1 request per hour (to prevent accidental multiple runs)

    **Returns**:
    - Status of indexing operation
    - Number of documents and chunks created
    """
    user_role = current_user.get('role', 'user')

    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(f"Admin {current_user['id']} triggered help docs indexing (force={force})")

    try:
        import sys
        from pathlib import Path

        # Add backend to path for imports
        backend_path = Path(__file__).parent.parent.parent
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        # Import and run the indexing function
        from scripts.index_help_docs import index_all_help_docs

        # Run indexing (this will take 30-60 seconds)
        index_all_help_docs(force=force)

        # Get final counts
        doc_count = supabase.table('help_documents').select('id', count='exact').execute()
        chunk_count = supabase.table('help_chunks').select('id', count='exact').execute()

        logger.info(f"Help docs indexing complete: {doc_count.count} docs, {chunk_count.count} chunks")

        return {
            "status": "success",
            "message": "Help documentation indexed successfully",
            "total_documents": doc_count.count,
            "total_chunks": chunk_count.count,
            "force_reindex": force
        }

    except Exception as e:
        logger.error(f"Error indexing help docs: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/index-docs-webhook")
async def index_help_docs_webhook(
    request: Request,
    force: bool = True
):
    """
    Webhook endpoint for automated help docs reindexing.

    Called by GitHub Actions when help documentation changes.
    Uses API key authentication instead of user JWT.

    **Headers Required**:
    - Authorization: Bearer <REINDEX_API_KEY>

    **Query Parameters**:
    - force: If True, reindex all documents (default: True)

    **Returns**:
    - Status of indexing operation
    - Number of documents and chunks created
    """
    # Check API key authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    provided_key = auth_header.replace("Bearer ", "").strip()
    expected_key = os.environ.get("HELP_REINDEX_API_KEY")

    if not expected_key:
        logger.error("HELP_REINDEX_API_KEY not configured in environment")
        raise HTTPException(status_code=500, detail="Server configuration error")

    if provided_key != expected_key:
        logger.warning(f"Invalid API key attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid API key")

    logger.info(f"Webhook triggered help docs reindexing from {request.client.host}")

    try:
        import sys
        from pathlib import Path

        # Add backend to path for imports
        backend_path = Path(__file__).parent.parent.parent
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        # Import and run the indexing function
        from scripts.index_help_docs import index_all_help_docs

        # Run indexing (this will take 30-60 seconds)
        index_all_help_docs(force=force)

        # Get final counts
        doc_count = supabase.table('help_documents').select('id', count='exact').execute()
        chunk_count = supabase.table('help_chunks').select('id', count='exact').execute()

        logger.info(f"Webhook reindex complete: {doc_count.count} docs, {chunk_count.count} chunks")

        return {
            "status": "success",
            "message": "Help documentation indexed successfully via webhook",
            "total_documents": doc_count.count,
            "total_chunks": chunk_count.count,
            "force_reindex": force,
            "triggered_by": "github_actions"
        }

    except Exception as e:
        logger.error(f"Error in webhook reindexing: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
