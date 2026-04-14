"""Admin stats routes - basic platform statistics."""

from fastapi import APIRouter, HTTPException, Request

import pb_client as pb
from logger_config import get_logger

from ._shared import limiter

logger = get_logger(__name__)
router = APIRouter()


@router.get("/stats")
@limiter.limit("60/minute")
async def get_admin_stats(request: Request):
    """Get overall platform statistics."""
    try:
        total_conversations = pb.count("conversations")
        total_documents = pb.count("documents")
        total_messages = pb.count("messages")

        logger.info(
            f"Stats: {total_conversations} conversations, "
            f"{total_documents} documents, {total_messages} messages"
        )

        return {
            "success": True,
            "total_users": 1,  # single-tenant
            "total_conversations": total_conversations,
            "total_documents": total_documents,
            "total_messages": total_messages,
        }
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
