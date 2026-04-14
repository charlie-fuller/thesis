"""Help Chat API Routes.

Provides AI-powered help chat using RAG over help documentation.
Separate from main chat conversations.
"""

import os
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, List, Optional

import anthropic
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

import pb_client as pb
from repositories.help_repo import (
    list_help_documents,
    get_help_document,
    list_help_chunks,
    get_help_chunk,
    list_help_conversations,
    get_help_conversation as repo_get_help_conversation,
    create_help_conversation,
    delete_help_conversation as repo_delete_help_conversation,
    list_help_messages,
    create_help_message,
    search_help,
)
from logger_config import get_logger
from services.embeddings import create_embedding

logger = get_logger(__name__)
router = APIRouter(prefix="/api/help", tags=["help"])
limiter = Limiter(key_func=get_remote_address)

# Global indexing state
_indexing_state = {
    "is_indexing": False,
    "progress": 0,
    "total_files": 0,
    "current_file": "",
    "status": "idle",
    "error": None,
    "started_at": None,
    "completed_at": None,
    "result": None,
}
_indexing_lock = Lock()
claude_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


HELP_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "help", "user")

# Mapping of slug -> filename for the Features tab
FEATURE_DOCS = {
    "chat": "02-chat.md",
    "documents": "04-knowledge-base.md",
    "disco-pipeline": "09-disco-initiatives.md",
    "projects-tasks": "06-projects.md",
    "profile": "07-stakeholders.md",
}


@router.get("/docs")
@limiter.limit("60/minute")
async def get_help_docs(request: Request):
    """Get help markdown documents for the Features tab.

    Returns a list of {slug, title, content} from docs/help/user/.
    """
    docs = []
    docs_dir = os.path.normpath(HELP_DOCS_DIR)

    for slug, filename in FEATURE_DOCS.items():
        filepath = os.path.join(docs_dir, filename)
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from first # heading
        title = slug.replace("-", " ").title()
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        docs.append({"slug": slug, "title": title, "content": content})

    return docs


class HelpChatRequest(BaseModel):
    """Request model for help chat."""

    message: str
    conversation_id: Optional[str] = None  # If continuing conversation
    top_k: int = 3  # Number of help chunks to retrieve (reduced for speed)
    help_type: Optional[str] = None  # 'admin' or 'user' - auto-detected from role if not provided


class HelpChatResponse(BaseModel):
    """Response model for help chat."""

    conversation_id: str
    message_id: str
    response: str
    sources: List[Dict]  # Referenced help documents


@router.post("/ask")
@limiter.limit("30/minute")
async def ask_help_question(
    request: Request, chat_request: HelpChatRequest,
):
    """Ask a question to the help system.

    Uses RAG to search help documentation and provide answers with sources.
    """
    logger.info(
        "Help chat request",
        extra={
            "message_length": len(chat_request.message),
            "conversation_id": chat_request.conversation_id,
        },
    )

    try:
        # Get or create conversation
        if chat_request.conversation_id:
            # Verify conversation exists
            conv = repo_get_help_conversation(chat_request.conversation_id)
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")

            conversation_id = chat_request.conversation_id

        else:
            # Create new help conversation
            help_type = chat_request.help_type or "user"

            conv = create_help_conversation(
                {
                    "title": chat_request.message[:50],
                    "help_type": help_type,
                }
            )

            conversation_id = conv["id"]
            logger.info(f"Created new help conversation: {conversation_id} (type: {help_type})")

        # Step 1: Generate query embedding
        query_embedding = create_embedding(chat_request.message, input_type="query")

        # Step 1.5: Detect recency queries and calculate date filter
        query_lower = chat_request.message.lower()
        recency_keywords = [
            "this week", "past week", "last week", "recent", "latest",
            "today", "yesterday", "past few days", "last few days",
            "last couple days", "most recent", "new docs", "new documents",
        ]
        is_recency_query = any(kw in query_lower for kw in recency_keywords)

        min_date = None
        if is_recency_query:
            min_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            logger.info(f"Detected recency query - filtering to docs after {min_date[:10]}")

        # Step 2: Search help chunks via vector similarity
        from services.pinecone_service import get_index as _get_pc_index
        from services.pinecone_service import query_vectors as _query_pc

        if _get_pc_index() is not None:
            # Build Pinecone metadata filter
            pc_filter = None

            matches = _query_pc(
                embedding=query_embedding,
                namespace="help_chunks",
                top_k=chat_request.top_k * 2,
                filter=pc_filter,
            )
            matches = [m for m in matches if m["score"] >= 0.4]

            if matches:
                chunk_ids = [m["id"] for m in matches]
                scores_map = {m["id"]: m["score"] for m in matches}

                # Fetch chunk details from PocketBase
                formatted_chunks = []
                for chunk_id in chunk_ids:
                    chunk = pb.get_record("help_chunks", chunk_id)
                    if not chunk:
                        continue
                    doc = pb.get_record("help_documents", chunk["document_id"]) if chunk.get("document_id") else {}
                    if not doc:
                        doc = {}
                    if min_date and doc.get("created", "") < min_date:
                        continue
                    formatted_chunks.append({
                        "id": chunk["id"],
                        "content": chunk["content"],
                        "heading_context": chunk.get("heading_context", ""),
                        "document_title": doc.get("title", "Unknown"),
                        "file_path": doc.get("file_path", ""),
                        "similarity": scores_map.get(str(chunk["id"]), 0),
                        "created_at": doc.get("created"),
                    })
                formatted_chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
                formatted_chunks = formatted_chunks[:chat_request.top_k]
                help_chunks_data = formatted_chunks
            else:
                help_chunks_data = []
        else:
            # Fallback -- no Pinecone, use simple text search or empty
            help_chunks_data = []

        if not help_chunks_data:
            logger.warning(f"No help chunks found for query: {chat_request.message[:50]}")
            if is_recency_query:
                context = "No documents found from the past 7 days matching this query. The date filter was applied because you asked for recent/this week's content."
            else:
                context = "No specific documentation found for this query."
            sources = []
        else:
            # Build context from retrieved chunks
            context_parts = []
            sources = []

            for i, chunk in enumerate(help_chunks_data):
                context_parts.append(
                    f"[Source {i + 1}: {chunk['document_title']} - {chunk['heading_context']}]\n{chunk['content']}"
                )

                sources.append(
                    {
                        "title": chunk["document_title"],
                        "section": chunk["heading_context"],
                        "file_path": chunk["file_path"],
                        "similarity": chunk["similarity"],
                    }
                )

            context = "\n\n---\n\n".join(context_parts)

        # Step 3: Get conversation history
        history = list_help_messages(conversation_id)

        # Step 4: Build system prompt for help assistant
        system_prompt = f"""You are a helpful assistant for the Thesis platform - a multi-agent GenAI strategy platform.

Your role is to answer questions about:
- Using the agent chat system (21 specialized AI agents)
- Managing the Knowledge Base (documents, auto-classification)
- Creating and managing Tasks (Kanban board)
- Managing AI Projects in the pipeline
- Running Meeting Rooms (autonomous multi-agent discussions)
- Tracking Stakeholders
- Using DISCo product discovery workflow
- Using the Discovery Inbox
- Admin functions (user management, agent configuration)

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
   - Format: "Navigate to **Page Name** -> **Tab Name** -> **Button/Option**"
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
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history] + [
            {"role": "user", "content": chat_request.message}
        ]

        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=system_prompt,
            messages=messages,
        )

        assistant_response = response.content[0].text

        # Step 6: Save messages to database
        # Save user message
        create_help_message(
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": chat_request.message,
            }
        )

        # Save assistant message with sources
        assistant_msg = create_help_message(
            {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": assistant_response,
                "sources": sources,
            }
        )

        message_id = assistant_msg["id"]

        logger.info(
            "Help response generated",
            extra={
                "conversation_id": conversation_id,
                "message_id": message_id,
                "sources_count": len(sources),
                "response_length": len(assistant_response),
            },
        )

        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "response": assistant_response,
            "sources": sources,
        }

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        logger.error(f"Error in help chat: {e}")
        logger.error(f"Full traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error generating help response: {str(e)}") from None


@router.get("/conversations")
@limiter.limit("60/minute")
async def get_help_conversations(request: Request):
    """Get all help conversations.

    Returns list of conversations with message counts.
    """
    try:
        conversations = list_help_conversations()

        # Get message counts for each conversation
        result = []
        for conv in conversations:
            messages = list_help_messages(conv["id"])
            result.append({**conv, "message_count": len(messages)})

        return result

    except Exception as e:
        logger.error(f"Error fetching help conversations: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/conversations/{conversation_id}")
@limiter.limit("60/minute")
async def get_help_conversation(request: Request, conversation_id: str):
    """Get full conversation history with messages."""
    try:
        # Verify conversation exists
        conv = repo_get_help_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        messages = list_help_messages(conversation_id)

        return {**conv, "messages": messages}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching help conversation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/conversations/{conversation_id}")
@limiter.limit("30/minute")
async def delete_help_conversation(
    request: Request, conversation_id: str,
):
    """Delete a help conversation and all its messages."""
    try:
        # Verify conversation exists
        conv = repo_get_help_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Delete conversation (messages cascade)
        repo_delete_help_conversation(conversation_id)

        return {"status": "deleted", "conversation_id": conversation_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting help conversation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/feedback/{message_id}")
@limiter.limit("100/minute")
async def submit_help_feedback(
    request: Request, message_id: str, feedback: int,
):
    """Submit feedback (thumbs up/down) for a help message.

    **Parameters**:
    - message_id: ID of the assistant message
    - feedback: 1 for thumbs up, -1 for thumbs down
    """
    if feedback not in [-1, 1]:
        raise HTTPException(status_code=400, detail="Feedback must be 1 (thumbs up) or -1 (thumbs down)")

    try:
        # Verify message exists
        message = pb.get_record("help_messages", message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # Update feedback
        pb.update_record(
            "help_messages",
            message_id,
            {"feedback": feedback, "feedback_timestamp": datetime.now(timezone.utc).isoformat()},
        )

        logger.info(f"Feedback recorded: message={message_id}, feedback={feedback}")

        return {"status": "success", "message_id": message_id, "feedback": feedback}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/search")
@limiter.limit("60/minute")
async def search_help_docs(
    request: Request, query: str, top_k: int = 10,
):
    """Search help documentation directly (without starting a conversation).

    Useful for quick lookups or autocomplete.
    """
    # Cap top_k
    top_k = min(top_k, 20)

    try:
        # Detect recency queries
        query_lower = query.lower()
        recency_keywords = [
            "this week", "past week", "last week", "recent", "latest",
            "today", "yesterday", "past few days", "last few days",
            "last couple days", "most recent", "new docs", "new documents",
        ]
        is_recency_query = any(kw in query_lower for kw in recency_keywords)

        min_date = None
        if is_recency_query:
            min_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        # Generate query embedding
        query_embedding = create_embedding(query, input_type="query")

        # Search help chunks
        from services.pinecone_service import get_index as _get_pc_idx
        from services.pinecone_service import query_vectors as _qv_pc

        if _get_pc_idx() is not None:
            pc_filter = None

            matches = _qv_pc(
                embedding=query_embedding,
                namespace="help_chunks",
                top_k=top_k * 2,
                filter=pc_filter,
            )
            matches = [m for m in matches if m["score"] >= 0.4]

            if matches:
                chunk_ids = [m["id"] for m in matches]
                scores_map = {m["id"]: m["score"] for m in matches}

                search_results = []
                for chunk_id in chunk_ids:
                    chunk = pb.get_record("help_chunks", chunk_id)
                    if not chunk:
                        continue
                    doc = pb.get_record("help_documents", chunk["document_id"]) if chunk.get("document_id") else {}
                    if not doc:
                        doc = {}
                    if min_date and doc.get("created", "") < min_date:
                        continue
                    search_results.append({
                        "id": chunk["id"],
                        "content": chunk["content"],
                        "heading_context": chunk.get("heading_context", ""),
                        "document_title": doc.get("title", "Unknown"),
                        "file_path": doc.get("file_path", ""),
                        "similarity": scores_map.get(str(chunk["id"]), 0),
                        "created_at": doc.get("created"),
                    })
                search_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
                search_results = search_results[:top_k]
            else:
                search_results = []

            return {
                "query": query,
                "results": search_results,
                "recency_filtered": is_recency_query,
                "min_date": min_date,
            }
        else:
            return {
                "query": query,
                "results": [],
                "recency_filtered": is_recency_query,
                "min_date": min_date,
            }

    except Exception as e:
        logger.error(f"Error searching help docs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/stats")
@limiter.limit("60/minute")
async def get_help_stats(request: Request):
    """Get statistics about help documentation.

    Admin-only endpoint (auth check removed -- will be handled at middleware level).
    """
    try:
        # Get counts
        doc_count = pb.count("help_documents")
        chunk_count = pb.count("help_chunks")

        # Documents by category
        all_docs = pb.get_all("help_documents")
        category_counts = {}
        for doc in all_docs:
            cat = doc.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Most recent updates
        recent_result = pb.list_records("help_documents", sort="-updated", per_page=5)
        recent_docs = recent_result.get("items", [])

        return {
            "total_documents": doc_count,
            "total_chunks": chunk_count,
            "documents_by_category": category_counts,
            "recent_updates": recent_docs,
        }

    except Exception as e:
        logger.error(f"Error fetching help stats: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/status")
async def help_system_status():
    """Public endpoint to check help system status (no auth required for debugging)."""
    try:
        doc_count = pb.count("help_documents")
        chunk_count = pb.count("help_chunks")

        # Get category breakdown for documents
        categories = {}
        if doc_count > 0:
            all_docs = pb.get_all("help_documents")
            for doc in all_docs:
                cat = doc.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

        # Get breakdown by role (admin vs user)
        by_role = {"admin": {"documents": 0, "chunks": 0}, "user": {"documents": 0, "chunks": 0}}
        by_role["admin"]["documents"] = categories.get("admin", 0)
        by_role["user"]["documents"] = categories.get("user", 0)

        # Count chunks by category from the documents they belong to
        if chunk_count > 0:
            all_chunks = pb.get_all("help_chunks")
            # Build doc category map
            doc_categories = {}
            if doc_count > 0:
                for doc in (all_docs if doc_count > 0 else []):
                    doc_categories[doc["id"]] = doc.get("category", "unknown")

            admin_chunk_count = 0
            user_chunk_count = 0
            for chunk in all_chunks:
                doc_id = chunk.get("document_id")
                cat = doc_categories.get(doc_id, "unknown")
                if cat == "admin":
                    admin_chunk_count += 1
                elif cat == "user":
                    user_chunk_count += 1

            by_role["admin"]["chunks"] = admin_chunk_count
            by_role["user"]["chunks"] = user_chunk_count

        return {
            "status": "operational",
            "total_documents": doc_count,
            "total_chunks": chunk_count,
            "database_connected": True,
            "indexed": chunk_count > 0,
            "indexing_status": "complete" if chunk_count > 0 else "pending",
            "categories": categories,
            "by_role": by_role,
        }

    except Exception as e:
        logger.error(f"Error checking help status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "database_connected": False,
            "indexed": False,
            "indexing_status": "error",
            "total_documents": 0,
            "total_chunks": 0,
            "categories": {},
            "by_role": {
                "admin": {"documents": 0, "chunks": 0},
                "user": {"documents": 0, "chunks": 0},
            },
        }


@router.get("/test-search")
async def test_help_search(query: str = "How do I customize the theme?"):
    """Debug endpoint to test the full search pipeline (no auth required)."""
    try:
        test_query = query

        # Detect recency queries
        query_lower = test_query.lower()
        recency_keywords = [
            "this week", "past week", "last week", "recent", "latest",
            "today", "yesterday", "past few days", "last few days",
            "last couple days", "most recent", "new docs", "new documents",
        ]
        is_recency_query = any(kw in query_lower for kw in recency_keywords)

        min_date = None
        if is_recency_query:
            min_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        # Step 1: Test embedding generation
        query_embedding = create_embedding(test_query, input_type="query")
        embedding_len = len(query_embedding)

        # Step 2: Test vector search
        from services.pinecone_service import get_index as _get_pc_test
        from services.pinecone_service import query_vectors as _qv_pc_test

        using_pinecone = _get_pc_test() is not None

        if using_pinecone:
            matches = _qv_pc_test(
                embedding=query_embedding,
                namespace="help_chunks",
                top_k=5,
                filter={"role_access": {"$eq": "admin"}},
            )
            matches = [m for m in matches if m["score"] >= 0.4]

            sample_results = []
            if matches:
                for m in matches:
                    chunk = pb.get_record("help_chunks", m["id"])
                    if not chunk:
                        continue
                    doc = pb.get_record("help_documents", chunk["document_id"]) if chunk.get("document_id") else {}
                    if not doc:
                        doc = {}
                    sample_results.append({
                        "title": doc.get("title", "Unknown"),
                        "section": chunk.get("heading_context", ""),
                        "similarity": m["score"],
                        "created_at": doc.get("created"),
                    })
                sample_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)

            return {
                "status": "success",
                "test_query": test_query,
                "embedding_dimension": embedding_len,
                "chunks_found": len(matches),
                "recency_filtered": is_recency_query,
                "min_date": min_date,
                "backend": "pinecone",
                "sample_results": sample_results[:3],
            }
        else:
            return {
                "status": "success",
                "test_query": test_query,
                "embedding_dimension": embedding_len,
                "chunks_found": 0,
                "recency_filtered": is_recency_query,
                "min_date": min_date,
                "backend": "none",
                "sample_results": [],
            }

    except Exception as e:
        import traceback

        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


def _update_progress(progress_pct: int, current_file: str):
    """Callback to update indexing progress."""
    global _indexing_state
    with _indexing_lock:
        _indexing_state["progress"] = progress_pct
        _indexing_state["current_file"] = current_file


def _run_indexing_background(force: bool):
    """Background task to run help docs indexing."""
    global _indexing_state

    try:
        import sys
        from pathlib import Path

        # Add backend to path for imports
        backend_path = Path(__file__).parent.parent.parent
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        import importlib

        import scripts.index_help_docs as help_indexer

        importlib.reload(help_indexer)

        # Get total files for progress tracking
        docs_path = help_indexer.get_help_docs_path()
        if docs_path.exists():
            markdown_files = list(docs_path.glob("**/*.md"))
            with _indexing_lock:
                _indexing_state["total_files"] = len(markdown_files)

        # Run indexing with progress callback
        help_indexer.index_all_help_docs(force=force, progress_callback=_update_progress)

        # Get final counts
        doc_count = pb.count("help_documents")
        chunk_count = pb.count("help_chunks")

        with _indexing_lock:
            _indexing_state["status"] = "completed"
            _indexing_state["is_indexing"] = False
            _indexing_state["progress"] = 100
            _indexing_state["completed_at"] = datetime.now(timezone.utc).isoformat()
            _indexing_state["result"] = {
                "total_documents": doc_count,
                "total_chunks": chunk_count,
            }

        logger.info(f"Background indexing complete: {doc_count} docs, {chunk_count} chunks")

    except Exception as e:
        logger.error(f"Background indexing error: {e}")
        with _indexing_lock:
            _indexing_state["status"] = "error"
            _indexing_state["is_indexing"] = False
            _indexing_state["error"] = str(e)


@router.get("/index-status")
async def get_indexing_status():
    """Get the current status of help documentation indexing."""
    with _indexing_lock:
        return {
            "is_indexing": _indexing_state["is_indexing"],
            "status": _indexing_state["status"],
            "progress": _indexing_state["progress"],
            "total_files": _indexing_state["total_files"],
            "current_file": _indexing_state["current_file"],
            "started_at": _indexing_state["started_at"],
            "completed_at": _indexing_state["completed_at"],
            "result": _indexing_state["result"],
            "error": _indexing_state["error"],
        }


@router.post("/index-docs")
@limiter.limit("10/hour")
async def index_help_docs(
    request: Request,
    background_tasks: BackgroundTasks,
    force: bool = False,
):
    """Index or reindex help documentation (runs in background).

    Admin-only endpoint for one-time setup or updates.
    """
    global _indexing_state

    # Check if already indexing
    with _indexing_lock:
        if _indexing_state["is_indexing"]:
            return {
                "status": "already_running",
                "message": "Indexing is already in progress",
                "started_at": _indexing_state["started_at"],
                "progress": _indexing_state["progress"],
            }

        # Reset state and start
        _indexing_state["is_indexing"] = True
        _indexing_state["status"] = "running"
        _indexing_state["progress"] = 0
        _indexing_state["total_files"] = 0
        _indexing_state["current_file"] = ""
        _indexing_state["error"] = None
        _indexing_state["started_at"] = datetime.now(timezone.utc).isoformat()
        _indexing_state["completed_at"] = None
        _indexing_state["result"] = None

    logger.info(f"Triggered background help docs indexing (force={force})")

    # Run indexing in background
    background_tasks.add_task(_run_indexing_background, force)

    return {
        "status": "started",
        "message": "Help documentation indexing started in background",
        "force_reindex": force,
        "started_at": _indexing_state["started_at"],
        "check_progress_at": "/api/help/index-status",
    }


@router.post("/index-docs-webhook")
async def index_help_docs_webhook(request: Request, force: bool = True):
    """Webhook endpoint for automated help docs reindexing.

    Called by GitHub Actions when help documentation changes.
    Uses API key authentication instead of user JWT.
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

        backend_path = Path(__file__).parent.parent.parent
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        import importlib

        import scripts.index_help_docs as help_indexer

        importlib.reload(help_indexer)

        # Run indexing
        help_indexer.index_all_help_docs(force=force)

        # Get final counts
        doc_count = pb.count("help_documents")
        chunk_count = pb.count("help_chunks")

        logger.info(f"Webhook reindex complete: {doc_count} docs, {chunk_count} chunks")

        return {
            "status": "success",
            "message": "Help documentation indexed successfully via webhook",
            "total_documents": doc_count,
            "total_chunks": chunk_count,
            "force_reindex": force,
            "triggered_by": "github_actions",
        }

    except Exception as e:
        logger.error(f"Error in webhook reindexing: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}") from None
