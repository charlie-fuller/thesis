"""Admin help docs routes - help documentation management and analytics."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request

import pb_client as pb
from logger_config import get_logger

from ._shared import limiter

logger = get_logger(__name__)
router = APIRouter()

# Role access mapping for help document categories
ROLE_ACCESS_MAP = {
    "admin": ["admin"],
    "system": ["admin", "user"],
    "user": ["user"],
    "technical": ["admin"],
}


def _extract_sections(md_content: str) -> list[tuple[str, str]]:
    """Extract sections from markdown content by headings."""
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


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries."""
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


@router.get("/help-documents/{document_id}")
async def get_help_document(document_id: str):
    """Get a single help document with its full content for editing."""
    try:
        safe_id = pb.escape_filter(document_id)
        doc = pb.get_first(
            "help_documents",
            filter=f"id='{safe_id}'",
            fields="id,title,file_path,category,content,created,updated",
        )

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        doc["chunk_count"] = pb.count("help_chunks", filter=f"document_id='{safe_id}'")

        return {"success": True, "document": doc}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get help document error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/help-documents")
async def get_help_documents():
    """Get all help documents with their metadata."""
    try:
        documents = pb.get_all(
            "help_documents",
            fields="id,title,file_path,category,created,updated",
            sort="category,title",
        )

        for doc in documents:
            safe_id = pb.escape_filter(doc["id"])
            doc["chunk_count"] = pb.count("help_chunks", filter=f"document_id='{safe_id}'")

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
async def reindex_help_document(request: Request, document_id: str):
    """Reindex a single help document by its ID.

    Deletes existing chunks and recreates them with fresh embeddings.
    """
    try:
        safe_id = pb.escape_filter(document_id)
        doc = pb.get_first(
            "help_documents",
            filter=f"id='{safe_id}'",
            fields="id,title,file_path,category",
        )

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        title = doc["title"]
        category = doc["category"]

        logger.info(f"Reindexing document: {title}")

        # Delete old vectors from Pinecone before deleting chunks
        old_chunks = pb.get_all("help_chunks", filter=f"document_id='{safe_id}'", fields="id")
        if old_chunks:
            old_ids = [str(c["id"]) for c in old_chunks]
            from services.pinecone_service import delete_vectors

            delete_vectors(ids=old_ids, namespace="help_chunks")

        # Delete old chunks
        for chunk in old_chunks:
            pb.delete_record("help_chunks", chunk["id"])

        content_doc = pb.get_first(
            "help_documents",
            filter=f"id='{safe_id}'",
            fields="content",
        )

        if not content_doc or not content_doc.get("content"):
            raise HTTPException(status_code=400, detail="Document has no content to index")

        content = content_doc["content"]

        from services.embeddings import create_embedding

        sections = _extract_sections(content)
        chunks_created = 0
        chunk_index = 0
        pinecone_vectors = []

        for heading, section_content in sections:
            section_chunks = _chunk_text(section_content)

            for chunk_text_content in section_chunks:
                if len(chunk_text_content.strip()) < 50:
                    continue

                try:
                    embedding_content = f"{title} - {heading}\n\n{chunk_text_content}"
                    embedding = create_embedding(embedding_content, input_type="document")

                    insert_result = pb.create_record(
                        "help_chunks",
                        {
                            "document_id": document_id,
                            "content": chunk_text_content,
                            "embedding": embedding,
                            "chunk_index": chunk_index,
                            "heading_context": heading,
                            "role_access": ROLE_ACCESS_MAP.get(category, ["admin", "user"]),
                            "metadata": {"category": category, "title": title, "section": heading},
                        },
                    )

                    # Collect for Pinecone upsert
                    if insert_result:
                        chunk_id = insert_result["id"]
                        role_access = ROLE_ACCESS_MAP.get(category, ["admin", "user"])
                        pinecone_vectors.append({
                            "id": str(chunk_id),
                            "values": embedding,
                            "metadata": {
                                "document_id": document_id,
                                "category": category,
                                "title": title,
                                "heading": heading,
                                "role_access": role_access[0] if role_access else "user",
                            },
                        })

                    chunks_created += 1
                    chunk_index += 1

                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {chunk_index}: {e}")
                    continue

        # Batch upsert to Pinecone
        if pinecone_vectors:
            from services.pinecone_service import upsert_vectors

            upsert_vectors(vectors=pinecone_vectors, namespace="help_chunks")

        pb.update_record(
            "help_documents",
            document_id,
            {"updated": datetime.now(timezone.utc).isoformat()},
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
async def update_help_document(document_id: str, request: Request):
    """Update a help document's title and/or content.

    Automatically triggers reindexing after update.
    """
    try:
        body = await request.json()
        title = body.get("title")
        content = body.get("content")

        if not title and not content:
            raise HTTPException(status_code=400, detail="Must provide title or content to update")

        safe_id = pb.escape_filter(document_id)
        doc = pb.get_first(
            "help_documents",
            filter=f"id='{safe_id}'",
            fields="id,title,file_path,category,content",
        )

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        new_title = title if title else doc["title"]
        new_content = content if content else doc["content"]
        category = doc["category"]

        if not new_title or len(new_title.strip()) < 3:
            raise HTTPException(status_code=400, detail="Title must be at least 3 characters")

        if not new_content or len(new_content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Content must be at least 50 characters")

        word_count = len(new_content.split())

        pb.update_record(
            "help_documents",
            document_id,
            {
                "title": new_title.strip(),
                "content": new_content,
                "word_count": word_count,
            },
        )

        logger.info(f"Updated help document: {new_title}")

        # Delete old vectors from Pinecone before deleting chunks
        old_chunks_upd = pb.get_all("help_chunks", filter=f"document_id='{safe_id}'", fields="id")
        if old_chunks_upd:
            old_ids_upd = [str(c["id"]) for c in old_chunks_upd]
            from services.pinecone_service import delete_vectors as _del_vecs

            _del_vecs(ids=old_ids_upd, namespace="help_chunks")

        for chunk in old_chunks_upd:
            pb.delete_record("help_chunks", chunk["id"])

        from services.embeddings import create_embedding

        sections = _extract_sections(new_content)
        chunks_created = 0
        chunk_index = 0
        pinecone_vectors_update = []

        for heading, section_content in sections:
            section_chunks = _chunk_text(section_content)

            for chunk_text_content in section_chunks:
                if len(chunk_text_content.strip()) < 50:
                    continue

                try:
                    embedding_content = f"{new_title} - {heading}\n\n{chunk_text_content}"
                    embedding = create_embedding(embedding_content, input_type="document")

                    insert_result = pb.create_record(
                        "help_chunks",
                        {
                            "document_id": document_id,
                            "content": chunk_text_content,
                            "embedding": embedding,
                            "chunk_index": chunk_index,
                            "heading_context": heading,
                            "role_access": ROLE_ACCESS_MAP.get(category, ["admin", "user"]),
                            "metadata": {
                                "category": category,
                                "title": new_title,
                                "section": heading,
                            },
                        },
                    )

                    # Collect for Pinecone upsert
                    if insert_result:
                        chunk_id = insert_result["id"]
                        role_access = ROLE_ACCESS_MAP.get(category, ["admin", "user"])
                        pinecone_vectors_update.append({
                            "id": str(chunk_id),
                            "values": embedding,
                            "metadata": {
                                "document_id": document_id,
                                "category": category,
                                "title": new_title,
                                "heading": heading,
                                "role_access": role_access[0] if role_access else "user",
                            },
                        })

                    chunks_created += 1
                    chunk_index += 1

                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {chunk_index}: {e}")
                    continue

        # Batch upsert to Pinecone
        if pinecone_vectors_update:
            from services.pinecone_service import upsert_vectors

            upsert_vectors(vectors=pinecone_vectors_update, namespace="help_chunks")

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
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
):
    """Get analytics for the help system."""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        messages = pb.get_all(
            "help_messages",
            filter=f"timestamp>='{start_date.isoformat()}'",
            fields="id,conversation_id,role,content,sources,feedback,feedback_timestamp,timestamp",
            sort="-timestamp",
        )

        conversations_list = pb.get_all(
            "help_conversations",
            filter=f"created>='{start_date.isoformat()}'",
            fields="id,user_id,title,created,help_type",
        )
        conversations = {c["id"]: c for c in conversations_list}

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
                sources = pb.parse_json_field(msg, "sources", [])

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

        avg_confidence = round(total_similarity / similarity_count, 3) if similarity_count > 0 else 0
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
        elif avg_confidence >= 0.7 or feedback_counts["negative"] <= feedback_counts["positive"] * 2:
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
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    format: str = Query("json", description="Export format: json or csv"),
):
    """Export all help conversations with messages for analysis."""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        conversations = pb.get_all(
            "help_conversations",
            filter=f"created>='{start_date.isoformat()}'",
            fields="id,user_id,title,help_type,created,updated",
            sort="-created",
        )

        if not conversations:
            return {"success": True, "count": 0, "conversations": [], "period_days": days}

        conversation_ids = [c["id"] for c in conversations]

        # Build filter for messages belonging to these conversations
        if len(conversation_ids) <= 30:
            conv_filter_parts = []
            for cid in conversation_ids:
                safe_cid = pb.escape_filter(cid)
                conv_filter_parts.append(f"conversation_id='{safe_cid}'")
            conv_filter = " || ".join(conv_filter_parts)
        else:
            conv_filter = None

        if conv_filter:
            messages = pb.get_all(
                "help_messages",
                filter=conv_filter,
                fields="id,conversation_id,role,content,sources,feedback,timestamp",
                sort="timestamp",
            )
        else:
            # Fallback: fetch all messages in the date range
            messages = pb.get_all(
                "help_messages",
                filter=f"timestamp>='{start_date.isoformat()}'",
                fields="id,conversation_id,role,content,sources,feedback,timestamp",
                sort="timestamp",
            )

        # Single-tenant: no user lookup needed
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
                    "sources": pb.parse_json_field(msg, "sources", None),
                    "feedback": msg.get("feedback"),
                    "timestamp": msg["timestamp"],
                }
            )

        export_data = []
        for conv in conversations:
            export_data.append(
                {
                    "id": conv["id"],
                    "title": conv.get("title", "Help Chat"),
                    "help_type": conv.get("help_type", "user"),
                    "user_email": "owner",
                    "user_name": "owner",
                    "created_at": conv["created"],
                    "message_count": len(messages_by_conv.get(conv["id"], [])),
                    "messages": messages_by_conv.get(conv["id"], []),
                }
            )

        logger.info(f"Exported {len(export_data)} help conversations")

        return {
            "success": True,
            "count": len(export_data),
            "period_days": days,
            "conversations": export_data,
        }

    except Exception as e:
        logger.error(f"Help conversations export error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
