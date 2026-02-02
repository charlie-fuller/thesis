"""Project KB Sync Service.

Detects when knowledge base changes are relevant to projects
and triggers re-evaluation of scores/justifications.

This service runs after document upload/processing to:
1. Find projects that may be affected by the new document
2. Queue re-evaluation of those projects
"""

import logging
from typing import List

from database import get_supabase
from services.project_justification import generate_project_justifications

logger = logging.getLogger(__name__)

# Minimum similarity score to consider a document relevant to a project
MIN_RELEVANCE_THRESHOLD = 0.35


async def find_projects_affected_by_document(
    document_id: str,
    client_id: str,
    min_similarity: float = MIN_RELEVANCE_THRESHOLD,
) -> List[dict]:
    """Find projects that might be affected by a new/updated document.

    Uses vector similarity between document chunks and project context
    to identify projects that should be re-evaluated.

    Returns list of project dicts with similarity scores.
    """
    supabase = get_supabase()

    # Get the document's chunks
    chunks_result = (
        supabase.table("document_chunks")
        .select("id, embedding, content")
        .eq("document_id", document_id)
        .execute()
    )

    if not chunks_result.data:
        logger.info(f"No chunks found for document {document_id}")
        return []

    # Get all projects for this client
    projects_result = (
        supabase.table("ai_projects")
        .select("id, title, description, current_state, desired_state, department")
        .eq("client_id", client_id)
        .execute()
    )

    if not projects_result.data:
        return []

    # For each project, check if any document chunk is relevant
    # We'll use a simple keyword/semantic approach
    affected = []

    for project in projects_result.data:
        # Build project context for matching
        project_context = " ".join(
            filter(
                None,
                [
                    project.get("title", ""),
                    project.get("description", ""),
                    project.get("current_state", ""),
                    project.get("desired_state", ""),
                    project.get("department", ""),
                ],
            )
        ).lower()

        # Check each chunk for relevance
        max_relevance = 0.0
        for chunk in chunks_result.data:
            chunk_content = (chunk.get("content") or "").lower()

            # Simple keyword overlap score
            # (In production, you'd use vector similarity with embeddings)
            project_words = set(project_context.split())
            chunk_words = set(chunk_content.split())

            if project_words and chunk_words:
                overlap = len(project_words & chunk_words)
                # Normalize by smaller set size
                relevance = (
                    overlap / min(len(project_words), len(chunk_words)) if overlap > 0 else 0
                )

                # Boost for department matches
                dept = (project.get("department") or "").lower()
                if dept and dept in chunk_content:
                    relevance = min(relevance + 0.2, 1.0)

                max_relevance = max(max_relevance, relevance)

        if max_relevance >= min_similarity:
            affected.append(
                {
                    "id": project["id"],
                    "title": project["title"],
                    "relevance": max_relevance,
                }
            )

    # Sort by relevance
    affected.sort(key=lambda x: x["relevance"], reverse=True)

    logger.info(f"Found {len(affected)} projects potentially affected by document {document_id}")
    return affected


async def sync_projects_after_document_change(
    document_id: str,
    client_id: str,
    regenerate_justifications: bool = True,
    max_projects: int = 10,
) -> dict:
    """Called after a document is added/updated to sync affected projects.

    Args:
        document_id: The document that changed
        client_id: Client owning the document
        regenerate_justifications: Whether to regenerate justifications
        max_projects: Maximum number of projects to update (to limit API calls)

    Returns:
        Dict with sync results
    """
    affected = await find_projects_affected_by_document(
        document_id=document_id,
        client_id=client_id,
    )

    if not affected:
        return {
            "document_id": document_id,
            "projects_checked": 0,
            "projects_updated": 0,
            "message": "No affected projects found",
        }

    # Limit to top N most relevant
    to_update = affected[:max_projects]

    updated_count = 0
    errors = []

    if regenerate_justifications:
        for project in to_update:
            try:
                await generate_project_justifications(
                    project_id=project["id"],
                    client_id=client_id,
                )
                updated_count += 1
                logger.info(
                    f"Regenerated justifications for project {project['title']} "
                    f"(relevance: {project['relevance']:.2f})"
                )
            except Exception as e:
                errors.append({"id": project["id"], "error": str(e)})
                logger.error(f"Failed to update project {project['id']}: {e}")

    return {
        "document_id": document_id,
        "projects_checked": len(affected),
        "projects_updated": updated_count,
        "projects": [
            {"id": p["id"], "title": p["title"], "relevance": p["relevance"]} for p in to_update
        ],
        "errors": errors if errors else None,
    }


async def check_and_sync_projects_for_document(document_id: str):
    """Background task wrapper that finds the client_id and syncs projects.

    This is the function to call from document processing background tasks.
    """
    supabase = get_supabase()

    # Get document's client_id
    doc_result = (
        supabase.table("documents").select("client_id").eq("id", document_id).single().execute()
    )

    if not doc_result.data:
        logger.warning(f"Document {document_id} not found for project sync")
        return

    client_id = doc_result.data["client_id"]

    result = await sync_projects_after_document_change(
        document_id=document_id,
        client_id=client_id,
        regenerate_justifications=True,
    )

    logger.info(f"Project KB sync complete: {result}")
    return result
