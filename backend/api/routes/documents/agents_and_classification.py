"""Document agent assignments and classification routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from auth import check_owner_or_admin, get_current_user
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

from ._shared import ConfirmClassificationRequest, UpdateDocumentAgentsRequest

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()


# ============================================================================
# AGENT ASSIGNMENTS
# ============================================================================


@router.get("/{document_id}/agents")
async def get_document_agents(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the agents linked to a document.

    Args:
        document_id: UUID of the document.
        current_user: Injected by FastAPI dependency.

    Returns:
        is_global: True if document has no agent links (available to all agents).
        linked_agents: List of agent IDs linked to this document.
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        links_result = await asyncio.to_thread(
            lambda: supabase.table("agent_knowledge_base")
            .select("agent_id, agents(id, name, display_name)")
            .eq("document_id", document_id)
            .execute()
        )

        linked_agents = []
        for link in links_result.data or []:
            if link.get("agents"):
                linked_agents.append(
                    {
                        "id": link["agents"]["id"],
                        "name": link["agents"]["name"],
                        "display_name": link["agents"]["display_name"],
                    }
                )

        return {
            "success": True,
            "document_id": document_id,
            "is_global": len(linked_agents) == 0,
            "linked_agents": linked_agents,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document agents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.put("/{document_id}/agents")
async def update_document_agents(
    document_id: str,
    request: UpdateDocumentAgentsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update the agents linked to a document.

    Args:
        document_id: UUID of the document.
        request: Contains agent_ids list. Empty list makes document global.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        user_id = current_user["id"]

        # Delete all existing links for this document
        await asyncio.to_thread(
            lambda: supabase.table("agent_knowledge_base").delete().eq("document_id", document_id).execute()
        )

        # Create new links
        linked_agents = []
        for agent_id in request.agent_ids:
            try:
                validate_uuid(agent_id, "agent_id")

                agent_result = await asyncio.to_thread(
                    lambda aid=agent_id: supabase.table("agents")
                    .select("id, name, display_name")
                    .eq("id", aid)
                    .single()
                    .execute()
                )

                if not agent_result.data:
                    logger.warning(f"Agent {agent_id} not found, skipping")
                    continue

                await asyncio.to_thread(
                    lambda aid=agent_id: supabase.table("agent_knowledge_base")
                    .insert(
                        {
                            "agent_id": aid,
                            "document_id": document_id,
                            "added_by": user_id,
                            "priority": 0,
                        }
                    )
                    .execute()
                )

                linked_agents.append(
                    {
                        "id": agent_result.data["id"],
                        "name": agent_result.data["name"],
                        "display_name": agent_result.data["display_name"],
                    }
                )
                logger.info(f"Linked document {document_id} to agent {agent_id}")

            except Exception as link_error:
                logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        is_global = len(linked_agents) == 0

        return {
            "success": True,
            "document_id": document_id,
            "is_global": is_global,
            "linked_agents": linked_agents,
            "message": "Global (all agents)" if is_global else f"Linked to {len(linked_agents)} agent(s)",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document agents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# CLASSIFICATION
# ============================================================================


@router.get("/{document_id}/classification")
async def get_document_classification(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get classification results for a document.

    Returns classification status, suggested agents, and whether user review is needed.

    Args:
        document_id: UUID of the document.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, filename").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        classification_result = await asyncio.to_thread(
            lambda: supabase.table("document_classifications")
            .select("*")
            .eq("document_id", document_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not classification_result.data:
            return {
                "success": True,
                "document_id": document_id,
                "classification": None,
                "message": "No classification found for this document",
            }

        classification = classification_result.data[0]

        # Get current agent links with relevance scores
        links_result = await asyncio.to_thread(
            lambda: supabase.table("agent_knowledge_base")
            .select(
                "agent_id, relevance_score, classification_source, "
                "classification_confidence, user_confirmed, agents(id, name, display_name)"
            )
            .eq("document_id", document_id)
            .execute()
        )

        linked_agents = []
        for link in links_result.data or []:
            if link.get("agents"):
                linked_agents.append(
                    {
                        "id": link["agents"]["id"],
                        "name": link["agents"]["name"],
                        "display_name": link["agents"]["display_name"],
                        "relevance_score": link.get("relevance_score", 0),
                        "classification_source": link.get("classification_source", "manual"),
                        "confidence": link.get("classification_confidence"),
                        "user_confirmed": link.get("user_confirmed", False),
                    }
                )

        return {
            "success": True,
            "document_id": document_id,
            "classification": {
                "id": classification["id"],
                "detected_type": classification.get("detected_type"),
                "method": classification.get("classification_method"),
                "status": classification.get("status"),
                "requires_user_review": classification.get("requires_user_review", False),
                "review_reason": classification.get("review_reason"),
                "raw_scores": classification.get("raw_scores", {}),
                "created_at": classification.get("created_at"),
            },
            "linked_agents": linked_agents,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document classification: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{document_id}/classification/confirm")
async def confirm_classification(
    document_id: str,
    request: ConfirmClassificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Confirm or modify auto-classification for a document.

    Called when user reviews and approves/modifies suggested agent tags.

    Args:
        document_id: UUID of the document.
        request: Contains agent_ids and optional relevance_scores.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        user_id = current_user["id"]

        # Delete all existing links
        await asyncio.to_thread(
            lambda: supabase.table("agent_knowledge_base").delete().eq("document_id", document_id).execute()
        )

        # Create confirmed links
        linked_agents = []
        for agent_id in request.agent_ids:
            try:
                validate_uuid(agent_id, "agent_id")

                # Get relevance score (from request override or default)
                relevance_score = 0.8  # Default for user-confirmed
                if request.relevance_scores and agent_id in request.relevance_scores:
                    relevance_score = request.relevance_scores[agent_id]

                agent_result = await asyncio.to_thread(
                    lambda aid=agent_id: supabase.table("agents")
                    .select("id, name, display_name")
                    .eq("id", aid)
                    .single()
                    .execute()
                )

                if not agent_result.data:
                    logger.warning(f"Agent {agent_id} not found, skipping")
                    continue

                await asyncio.to_thread(
                    lambda aid=agent_id, rs=relevance_score: supabase.table("agent_knowledge_base")
                    .insert(
                        {
                            "agent_id": aid,
                            "document_id": document_id,
                            "added_by": user_id,
                            "priority": 0,
                            "relevance_score": rs,
                            "classification_source": "user_confirmed",
                            "classification_confidence": rs,
                            "user_confirmed": True,
                        }
                    )
                    .execute()
                )

                linked_agents.append(
                    {
                        "id": agent_result.data["id"],
                        "name": agent_result.data["name"],
                        "display_name": agent_result.data["display_name"],
                        "relevance_score": relevance_score,
                    }
                )
                logger.info(f"User confirmed document {document_id} link to agent {agent_id}")

            except Exception as link_error:
                logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        # Update classification status to reviewed
        await asyncio.to_thread(
            lambda: supabase.table("document_classifications")
            .update(
                {
                    "status": "reviewed",
                    "requires_user_review": False,
                    "reviewed_at": "now()",
                    "reviewed_by": user_id,
                }
            )
            .eq("document_id", document_id)
            .execute()
        )

        return {
            "success": True,
            "document_id": document_id,
            "is_global": len(linked_agents) == 0,
            "linked_agents": linked_agents,
            "message": f"Classification confirmed with {len(linked_agents)} agent(s)",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming document classification: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
