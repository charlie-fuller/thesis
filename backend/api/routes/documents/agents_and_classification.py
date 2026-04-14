"""Document agent assignments and classification routes."""

from fastapi import APIRouter, HTTPException

import pb_client as pb
from logger_config import get_logger
from repositories import documents as doc_repo
from validation import validate_uuid

from ._shared import ConfirmClassificationRequest, UpdateDocumentAgentsRequest

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# AGENT ASSIGNMENTS
# ============================================================================


@router.get("/{document_id}/agents")
async def get_document_agents(
    document_id: str,
):
    """Get the agents linked to a document.

    Args:
        document_id: UUID of the document.

    Returns:
        is_global: True if document has no agent links (available to all agents).
        linked_agents: List of agent IDs linked to this document.
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        kb_links = pb.get_all(
            "agent_knowledge_base",
            filter=f"document_id='{pb.escape_filter(document_id)}'",
        )

        linked_agents = []
        for link in kb_links:
            agent = pb.get_record("agents", link["agent_id"])
            if agent:
                linked_agents.append(
                    {
                        "id": agent["id"],
                        "name": agent["name"],
                        "display_name": agent.get("display_name", ""),
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
):
    """Update the agents linked to a document.

    Args:
        document_id: UUID of the document.
        request: Contains agent_ids list. Empty list makes document global.
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete all existing links for this document
        existing_links = pb.get_all(
            "agent_knowledge_base",
            filter=f"document_id='{pb.escape_filter(document_id)}'",
        )
        for link in existing_links:
            pb.delete_record("agent_knowledge_base", link["id"])

        # Create new links
        linked_agents = []
        for agent_id in request.agent_ids:
            try:
                validate_uuid(agent_id, "agent_id")

                agent = pb.get_record("agents", agent_id)
                if not agent:
                    logger.warning(f"Agent {agent_id} not found, skipping")
                    continue

                pb.create_record(
                    "agent_knowledge_base",
                    {
                        "agent_id": agent_id,
                        "document_id": document_id,
                        "priority": 0,
                    },
                )

                linked_agents.append(
                    {
                        "id": agent["id"],
                        "name": agent["name"],
                        "display_name": agent.get("display_name", ""),
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
):
    """Get classification results for a document.

    Returns classification status, suggested agents, and whether user review is needed.

    Args:
        document_id: UUID of the document.
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        classifications = doc_repo.list_document_classifications(document_id)

        if not classifications:
            return {
                "success": True,
                "document_id": document_id,
                "classification": None,
                "message": "No classification found for this document",
            }

        classification = classifications[0]  # Already sorted by -confidence

        # Get current agent links with relevance scores
        kb_links = pb.get_all(
            "agent_knowledge_base",
            filter=f"document_id='{pb.escape_filter(document_id)}'",
        )

        linked_agents = []
        for link in kb_links:
            agent = pb.get_record("agents", link["agent_id"])
            if agent:
                linked_agents.append(
                    {
                        "id": agent["id"],
                        "name": agent["name"],
                        "display_name": agent.get("display_name", ""),
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
                "raw_scores": pb.parse_json_field(classification.get("raw_scores"), {}),
                "created_at": classification.get("created"),
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
):
    """Confirm or modify auto-classification for a document.

    Called when user reviews and approves/modifies suggested agent tags.

    Args:
        document_id: UUID of the document.
        request: Contains agent_ids and optional relevance_scores.
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete all existing links
        existing_links = pb.get_all(
            "agent_knowledge_base",
            filter=f"document_id='{pb.escape_filter(document_id)}'",
        )
        for link in existing_links:
            pb.delete_record("agent_knowledge_base", link["id"])

        # Create confirmed links
        linked_agents = []
        for agent_id in request.agent_ids:
            try:
                validate_uuid(agent_id, "agent_id")

                # Get relevance score (from request override or default)
                relevance_score = 0.8  # Default for user-confirmed
                if request.relevance_scores and agent_id in request.relevance_scores:
                    relevance_score = request.relevance_scores[agent_id]

                agent = pb.get_record("agents", agent_id)
                if not agent:
                    logger.warning(f"Agent {agent_id} not found, skipping")
                    continue

                pb.create_record(
                    "agent_knowledge_base",
                    {
                        "agent_id": agent_id,
                        "document_id": document_id,
                        "priority": 0,
                        "relevance_score": relevance_score,
                        "classification_source": "user_confirmed",
                        "classification_confidence": relevance_score,
                        "user_confirmed": True,
                    },
                )

                linked_agents.append(
                    {
                        "id": agent["id"],
                        "name": agent["name"],
                        "display_name": agent.get("display_name", ""),
                        "relevance_score": relevance_score,
                    }
                )
                logger.info(f"User confirmed document {document_id} link to agent {agent_id}")

            except Exception as link_error:
                logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        # Update classification status to reviewed
        classifications = doc_repo.list_document_classifications(document_id)
        for cl in classifications:
            doc_repo.update_document_classification(
                cl["id"],
                {
                    "status": "reviewed",
                    "requires_user_review": False,
                },
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
