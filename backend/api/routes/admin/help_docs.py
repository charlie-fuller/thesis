"""Admin help docs routes - help documentation management and analytics."""

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from auth import require_admin
from logger_config import get_logger

from ._shared import limiter, supabase

logger = get_logger(__name__)
router = APIRouter()


@router.get("/help-documents/{document_id}")
async def get_help_document(
    document_id: str,
    current_user: dict = Depends(require_admin),
):
    """Get a single help document with its full content for editing.

    Args:
        document_id: UUID of the help document.
        current_user: Injected by FastAPI dependency.
    """
    try:
        doc_result = await asyncio.to_thread(
            lambda: supabase.table("help_documents")
            .select("id, title, file_path, category, content, created_at, updated_at")
            .eq("id", document_id)
            .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = doc_result.data[0]

        chunk_result = await asyncio.to_thread(
            lambda: supabase.table("help_chunks")
            .select("id", count="exact")
            .eq("document_id", document_id)
            .execute()
        )
        doc["chunk_count"] = chunk_result.count or 0

        return {"success": True, "document": doc}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get help document error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/help-documents")
async def get_help_documents(current_user: dict = Depends(require_admin)):
    """Get all help documents with their metadata.

    Returns documents grouped by category (user/admin).

    Args:
        current_user: Injected by FastAPI dependency.
    """
    try:
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("help_documents")
            .select("id, title, file_path, category, created_at, updated_at")
            .order("category")
            .order("title")
            .execute()
        )
        documents = docs_result.data or []

        for doc in documents:
            chunk_result = await asyncio.to_thread(
                lambda doc_id=doc["id"]: supabase.table("help_chunks")
                .select("id", count="exact")
                .eq("document_id", doc_id)
                .execute()
            )
            doc["chunk_count"] = chunk_result.count or 0

        user_docs = [d for d in documents if d.get("category") == "user"]
        admin_docs = [d for d in documents if d.get("category") == "admin"]

        return {
            "success": True,
            "documents": {"user": user_docs, "admin": admin_docs},
            "total_count": len(documents),
        }
    except Exception as e:
        logger.error(f"Help documents error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/help-documents/{document_id}/reindex")
@limiter.limit("10/minute")
async def reindex_help_document(
    request: Request,
    document_id: str,
    current_user: dict = Depends(require_admin),
):
    """Reindex a single help document by its ID.

    Deletes existing chunks and recreates them with fresh embeddings.

    Args:
        request: FastAPI request object for rate limiting.
        document_id: UUID of the help document.
        current_user: Injected by FastAPI dependency.
    """
    try:
        doc_result = await asyncio.to_thread(
            lambda: supabase.table("help_documents")
            .select("id, title, file_path, category")
            .eq("id", document_id)
            .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = doc_result.data[0]
        title = doc["title"]
        category = doc["category"]

        logger.info(f"Reindexing document: {title}")

        await asyncio.to_thread(
            lambda: supabase.table("help_chunks").delete().eq("document_id", document_id).execute()
        )

        content_result = await asyncio.to_thread(
            lambda: supabase.table("help_documents")
            .select("content")
            .eq("id", document_id)
            .execute()
        )

        if not content_result.data or not content_result.data[0].get("content"):
            raise HTTPException(status_code=400, detail="Document has no content to index")

        content = content_result.data[0]["content"]

        from services.embeddings import create_embedding

        role_access_map = {
            "admin": ["admin"],
            "system": ["admin", "user"],
            "user": ["user"],
            "technical": ["admin"],
        }

        def extract_sections(md_content: str):
            sections = []
            current_heading = "Introduction"
            current_content = []

            for line in md_content.split("\n"):
                if line.strip().startswith("#"):
                    if current_content:
                        sections.append((current_heading, "\n".join(current_content)))
                    current_heading = line.strip().lstrip("#").strip()
                    current_content = []
                else:
                    current_content.append(line)

            if current_content:
                sections.append((current_heading, "\n".join(current_content)))

            return sections

        def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
            chunks = []
            start = 0

            while start < len(text):
                end = start + chunk_size

                if end < len(text):
                    sentence_end = max(
                        text.rfind(". ", start, end),
                        text.rfind(".\n", start, end),
                        text.rfind("? ", start, end),
                        text.rfind("! ", start, end),
                    )
                    if sentence_end > start + chunk_size - 100:
                        end = sentence_end + 1

                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)

                start = end - overlap if end < len(text) else len(text)

            return chunks

        sections = extract_sections(content)
        chunks_created = 0
        chunk_index = 0

        for heading, section_content in sections:
            section_chunks = chunk_text(section_content)

            for chunk_text_content in section_chunks:
                if len(chunk_text_content.strip()) < 50:
                    continue

                try:
                    embedding_content = f"{title} - {heading}\n\n{chunk_text_content}"
                    embedding = create_embedding(embedding_content, input_type="document")

                    await asyncio.to_thread(
                        lambda emb=embedding,
                        idx=chunk_index,
                        head=heading,
                        chunk=chunk_text_content: supabase.table("help_chunks")
                        .insert(
                            {
                                "document_id": document_id,
                                "content": chunk,
                                "embedding": emb,
                                "chunk_index": idx,
                                "heading_context": head,
                                "role_access": role_access_map.get(category, ["admin", "user"]),
                                "metadata": {"category": category, "title": title, "section": head},
                            }
                        )
                        .execute()
                    )

                    chunks_created += 1
                    chunk_index += 1

                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {chunk_index}: {e}")
                    continue

        await asyncio.to_thread(
            lambda: supabase.table("help_documents")
            .update({"updated_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", document_id)
            .execute()
        )

        logger.info(f"Reindexed {title}: {chunks_created} chunks created")

        return {
            "success": True,
            "document_id": document_id,
            "title": title,
            "chunks_created": chunks_created,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reindex document error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.put("/help-documents/{document_id}")
async def update_help_document(
    document_id: str,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    """Update a help document's title and/or content.

    Automatically triggers reindexing after update.

    Args:
        document_id: UUID of the help document.
        request: FastAPI request object containing update data.
        current_user: Injected by FastAPI dependency.
    """
    try:
        body = await request.json()
        title = body.get("title")
        content = body.get("content")

        if not title and not content:
            raise HTTPException(status_code=400, detail="Must provide title or content to update")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("help_documents")
            .select("id, title, file_path, category, content")
            .eq("id", document_id)
            .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = doc_result.data[0]
        new_title = title if title else doc["title"]
        new_content = content if content else doc["content"]
        category = doc["category"]

        if not new_title or len(new_title.strip()) < 3:
            raise HTTPException(status_code=400, detail="Title must be at least 3 characters")

        if not new_content or len(new_content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Content must be at least 50 characters")

        word_count = len(new_content.split())

        await asyncio.to_thread(
            lambda: supabase.table("help_documents")
            .update(
                {
                    "title": new_title.strip(),
                    "content": new_content,
                    "word_count": word_count,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", document_id)
            .execute()
        )

        logger.info(f"Updated help document: {new_title} by admin {current_user['id']}")

        await asyncio.to_thread(
            lambda: supabase.table("help_chunks").delete().eq("document_id", document_id).execute()
        )

        from services.embeddings import create_embedding

        role_access_map = {
            "admin": ["admin"],
            "system": ["admin", "user"],
            "user": ["user"],
            "technical": ["admin"],
        }

        def extract_sections(md_content: str):
            sections = []
            current_heading = "Introduction"
            current_content = []

            for line in md_content.split("\n"):
                if line.strip().startswith("#"):
                    if current_content:
                        sections.append((current_heading, "\n".join(current_content)))
                    current_heading = line.strip().lstrip("#").strip()
                    current_content = []
                else:
                    current_content.append(line)

            if current_content:
                sections.append((current_heading, "\n".join(current_content)))

            return sections

        def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
            chunks = []
            start = 0

            while start < len(text):
                end = start + chunk_size

                if end < len(text):
                    sentence_end = max(
                        text.rfind(". ", start, end),
                        text.rfind(".\n", start, end),
                        text.rfind("? ", start, end),
                        text.rfind("! ", start, end),
                    )
                    if sentence_end > start + chunk_size - 100:
                        end = sentence_end + 1

                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)

                start = end - overlap if end < len(text) else len(text)

            return chunks

        sections = extract_sections(new_content)
        chunks_created = 0
        chunk_index = 0

        for heading, section_content in sections:
            section_chunks = chunk_text(section_content)

            for chunk_text_content in section_chunks:
                if len(chunk_text_content.strip()) < 50:
                    continue

                try:
                    embedding_content = f"{new_title} - {heading}\n\n{chunk_text_content}"
                    embedding = create_embedding(embedding_content, input_type="document")

                    await asyncio.to_thread(
                        lambda emb=embedding,
                        idx=chunk_index,
                        head=heading,
                        chunk=chunk_text_content: supabase.table("help_chunks")
                        .insert(
                            {
                                "document_id": document_id,
                                "content": chunk,
                                "embedding": emb,
                                "chunk_index": idx,
                                "heading_context": head,
                                "role_access": role_access_map.get(category, ["admin", "user"]),
                                "metadata": {
                                    "category": category,
                                    "title": new_title,
                                    "section": head,
                                },
                            }
                        )
                        .execute()
                    )

                    chunks_created += 1
                    chunk_index += 1

                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {chunk_index}: {e}")
                    continue

        logger.info(f"Reindexed {new_title} after update: {chunks_created} chunks created")

        return {
            "success": True,
            "document_id": document_id,
            "title": new_title,
            "word_count": word_count,
            "chunks_created": chunks_created,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update help document error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/help-analytics")
async def get_help_analytics(
    current_user: dict = Depends(require_admin),
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
):
    """Get analytics for the help system.

    Returns questions asked, low confidence responses, and feedback breakdown.

    Args:
        current_user: Injected by FastAPI dependency.
        days: Number of days to analyze.
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        messages_result = await asyncio.to_thread(
            lambda: supabase.table("help_messages")
            .select(
                "id, conversation_id, role, content, sources, "
                "feedback, feedback_timestamp, timestamp"
            )
            .gte("timestamp", start_date.isoformat())
            .order("timestamp", desc=True)
            .execute()
        )
        messages = messages_result.data or []

        conversations_result = await asyncio.to_thread(
            lambda: supabase.table("help_conversations")
            .select("id, user_id, title, created_at, help_type")
            .gte("created_at", start_date.isoformat())
            .execute()
        )
        conversations = {c["id"]: c for c in (conversations_result.data or [])}

        user_questions = []
        low_confidence_responses = []
        feedback_counts = {"positive": 0, "negative": 0, "none": 0}
        total_responses = 0
        total_similarity = 0
        similarity_count = 0

        for msg in messages:
            if msg.get("role") == "user":
                user_questions.append(
                    {
                        "id": msg["id"],
                        "conversation_id": msg["conversation_id"],
                        "question": msg.get("content", "")[:200],
                        "timestamp": msg.get("timestamp"),
                    }
                )
            elif msg.get("role") == "assistant":
                total_responses += 1
                sources = msg.get("sources") or []

                if sources:
                    similarities = [s.get("similarity", 0) for s in sources if s.get("similarity")]
                    if similarities:
                        avg_similarity = sum(similarities) / len(similarities)
                        total_similarity += avg_similarity
                        similarity_count += 1

                        if avg_similarity < 0.75:
                            conv_id = msg["conversation_id"]
                            conv = conversations.get(conv_id, {})

                            low_confidence_responses.append(
                                {
                                    "id": msg["id"],
                                    "conversation_id": conv_id,
                                    "conversation_title": conv.get("title", "Unknown"),
                                    "help_type": conv.get("help_type", "user"),
                                    "response_preview": msg.get("content", "")[:150],
                                    "avg_similarity": round(avg_similarity, 3),
                                    "source_count": len(sources),
                                    "sources": [
                                        {
                                            "title": s.get("title"),
                                            "section": s.get("section"),
                                            "similarity": round(s.get("similarity", 0), 3),
                                        }
                                        for s in sources
                                    ],
                                    "timestamp": msg.get("timestamp"),
                                    "feedback": msg.get("feedback"),
                                }
                            )

                feedback = msg.get("feedback")
                if feedback == 1:
                    feedback_counts["positive"] += 1
                elif feedback == -1:
                    feedback_counts["negative"] += 1
                else:
                    feedback_counts["none"] += 1

        low_confidence_responses.sort(key=lambda x: x["avg_similarity"])

        avg_confidence = (
            round(total_similarity / similarity_count, 3) if similarity_count > 0 else 0
        )
        feedback_rate = (
            round(
                (feedback_counts["positive"] + feedback_counts["negative"]) / total_responses * 100,
                1,
            )
            if total_responses > 0
            else 0
        )

        if avg_confidence >= 0.8 and feedback_counts["negative"] <= feedback_counts["positive"]:
            health_status = "healthy"
        elif (
            avg_confidence >= 0.7 or feedback_counts["negative"] <= feedback_counts["positive"] * 2
        ):
            health_status = "warning"
        else:
            health_status = "critical"

        logger.info(
            f"Help analytics: {len(user_questions)} questions, "
            f"{len(low_confidence_responses)} low confidence, avg confidence {avg_confidence}"
        )

        return {
            "success": True,
            "period_days": days,
            "summary": {
                "total_questions": len(user_questions),
                "total_responses": total_responses,
                "avg_confidence": avg_confidence,
                "low_confidence_count": len(low_confidence_responses),
                "feedback_rate": feedback_rate,
                "health_status": health_status,
            },
            "feedback": {
                "positive": feedback_counts["positive"],
                "negative": feedback_counts["negative"],
                "no_feedback": feedback_counts["none"],
            },
            "low_confidence_responses": low_confidence_responses[:20],
            "recent_questions": user_questions[:20],
        }
    except Exception as e:
        logger.error(f"Help analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/help-conversations/export")
async def export_help_conversations(
    current_user: dict = Depends(require_admin),
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    format: str = Query("json", description="Export format: json or csv"),
):
    """Export all help conversations with messages for analysis.

    Returns conversations with their full message history.

    Args:
        current_user: Injected by FastAPI dependency.
        days: Number of days to export.
        format: Export format.
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        conversations_result = await asyncio.to_thread(
            lambda: supabase.table("help_conversations")
            .select("id, user_id, title, help_type, created_at, updated_at")
            .gte("created_at", start_date.isoformat())
            .order("created_at", desc=True)
            .execute()
        )
        conversations = conversations_result.data or []

        if not conversations:
            return {"success": True, "count": 0, "conversations": [], "period_days": days}

        conversation_ids = [c["id"] for c in conversations]
        messages_result = await asyncio.to_thread(
            lambda: supabase.table("help_messages")
            .select("id, conversation_id, role, content, sources, feedback, timestamp")
            .in_("conversation_id", conversation_ids)
            .order("timestamp")
            .execute()
        )
        messages = messages_result.data or []

        user_ids = list({c["user_id"] for c in conversations if c.get("user_id")})
        users_result = (
            await asyncio.to_thread(
                lambda: supabase.table("users")
                .select("id, email, name")
                .in_("id", user_ids)
                .execute()
            )
            if user_ids
            else type("obj", (object,), {"data": []})()
        )
        users = {u["id"]: u for u in (users_result.data or [])}

        messages_by_conv = {}
        for msg in messages:
            conv_id = msg["conversation_id"]
            if conv_id not in messages_by_conv:
                messages_by_conv[conv_id] = []
            messages_by_conv[conv_id].append(
                {
                    "id": msg["id"],
                    "role": msg["role"],
                    "content": msg["content"],
                    "sources": msg.get("sources"),
                    "feedback": msg.get("feedback"),
                    "timestamp": msg["timestamp"],
                }
            )

        export_data = []
        for conv in conversations:
            user = users.get(conv.get("user_id"), {})
            export_data.append(
                {
                    "id": conv["id"],
                    "title": conv.get("title", "Help Chat"),
                    "help_type": conv.get("help_type", "user"),
                    "user_email": user.get("email", "Unknown"),
                    "user_name": user.get("name", "Unknown"),
                    "created_at": conv["created_at"],
                    "message_count": len(messages_by_conv.get(conv["id"], [])),
                    "messages": messages_by_conv.get(conv["id"], []),
                }
            )

        logger.info(
            f"Exported {len(export_data)} help conversations for admin {current_user['id']}"
        )

        return {
            "success": True,
            "count": len(export_data),
            "period_days": days,
            "conversations": export_data,
        }

    except Exception as e:
        logger.error(f"Help conversations export error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
