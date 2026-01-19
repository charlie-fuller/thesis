"""
Opportunity KB Sync Service

Detects when knowledge base changes are relevant to opportunities
and triggers re-evaluation of scores/justifications.

This service runs after document upload/processing to:
1. Find opportunities that may be affected by the new document
2. Queue re-evaluation of those opportunities
"""

import logging
from typing import List, Optional
import os

from database import get_supabase
from services.opportunity_justification import generate_opportunity_justifications

logger = logging.getLogger(__name__)

# Minimum similarity score to consider a document relevant to an opportunity
MIN_RELEVANCE_THRESHOLD = 0.35


async def find_opportunities_affected_by_document(
    document_id: str,
    client_id: str,
    min_similarity: float = MIN_RELEVANCE_THRESHOLD,
) -> List[dict]:
    """
    Find opportunities that might be affected by a new/updated document.

    Uses vector similarity between document chunks and opportunity context
    to identify opportunities that should be re-evaluated.

    Returns list of opportunity dicts with similarity scores.
    """
    supabase = get_supabase()

    # Get the document's chunks
    chunks_result = supabase.table("document_chunks") \
        .select("id, embedding, content") \
        .eq("document_id", document_id) \
        .execute()

    if not chunks_result.data:
        logger.info(f"No chunks found for document {document_id}")
        return []

    # Get all opportunities for this client
    opps_result = supabase.table("ai_opportunities") \
        .select("id, title, description, current_state, desired_state, department") \
        .eq("client_id", client_id) \
        .execute()

    if not opps_result.data:
        return []

    # For each opportunity, check if any document chunk is relevant
    # We'll use a simple keyword/semantic approach
    affected = []

    for opp in opps_result.data:
        # Build opportunity context for matching
        opp_context = " ".join(filter(None, [
            opp.get("title", ""),
            opp.get("description", ""),
            opp.get("current_state", ""),
            opp.get("desired_state", ""),
            opp.get("department", ""),
        ])).lower()

        # Check each chunk for relevance
        max_relevance = 0.0
        for chunk in chunks_result.data:
            chunk_content = (chunk.get("content") or "").lower()

            # Simple keyword overlap score
            # (In production, you'd use vector similarity with embeddings)
            opp_words = set(opp_context.split())
            chunk_words = set(chunk_content.split())

            if opp_words and chunk_words:
                overlap = len(opp_words & chunk_words)
                # Normalize by smaller set size
                relevance = overlap / min(len(opp_words), len(chunk_words)) if overlap > 0 else 0

                # Boost for department matches
                dept = (opp.get("department") or "").lower()
                if dept and dept in chunk_content:
                    relevance = min(relevance + 0.2, 1.0)

                max_relevance = max(max_relevance, relevance)

        if max_relevance >= min_similarity:
            affected.append({
                "id": opp["id"],
                "title": opp["title"],
                "relevance": max_relevance,
            })

    # Sort by relevance
    affected.sort(key=lambda x: x["relevance"], reverse=True)

    logger.info(
        f"Found {len(affected)} opportunities potentially affected by document {document_id}"
    )
    return affected


async def sync_opportunities_after_document_change(
    document_id: str,
    client_id: str,
    regenerate_justifications: bool = True,
    max_opportunities: int = 10,
) -> dict:
    """
    Called after a document is added/updated to sync affected opportunities.

    Args:
        document_id: The document that changed
        client_id: Client owning the document
        regenerate_justifications: Whether to regenerate justifications
        max_opportunities: Maximum number of opportunities to update (to limit API calls)

    Returns:
        Dict with sync results
    """
    affected = await find_opportunities_affected_by_document(
        document_id=document_id,
        client_id=client_id,
    )

    if not affected:
        return {
            "document_id": document_id,
            "opportunities_checked": 0,
            "opportunities_updated": 0,
            "message": "No affected opportunities found",
        }

    # Limit to top N most relevant
    to_update = affected[:max_opportunities]

    updated_count = 0
    errors = []

    if regenerate_justifications:
        for opp in to_update:
            try:
                await generate_opportunity_justifications(
                    opportunity_id=opp["id"],
                    client_id=client_id,
                )
                updated_count += 1
                logger.info(
                    f"Regenerated justifications for opportunity {opp['title']} "
                    f"(relevance: {opp['relevance']:.2f})"
                )
            except Exception as e:
                errors.append({"id": opp["id"], "error": str(e)})
                logger.error(f"Failed to update opportunity {opp['id']}: {e}")

    return {
        "document_id": document_id,
        "opportunities_checked": len(affected),
        "opportunities_updated": updated_count,
        "opportunities": [{"id": o["id"], "title": o["title"], "relevance": o["relevance"]} for o in to_update],
        "errors": errors if errors else None,
    }


async def check_and_sync_opportunities_for_document(document_id: str):
    """
    Background task wrapper that finds the client_id and syncs opportunities.

    This is the function to call from document processing background tasks.
    """
    supabase = get_supabase()

    # Get document's client_id
    doc_result = supabase.table("documents") \
        .select("client_id") \
        .eq("id", document_id) \
        .single() \
        .execute()

    if not doc_result.data:
        logger.warning(f"Document {document_id} not found for opportunity sync")
        return

    client_id = doc_result.data["client_id"]

    result = await sync_opportunities_after_document_change(
        document_id=document_id,
        client_id=client_id,
        regenerate_justifications=True,
    )

    logger.info(f"Opportunity KB sync complete: {result}")
    return result
