"""Admin stats routes - basic platform statistics."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import require_admin
from logger_config import get_logger

from ._shared import limiter, supabase

logger = get_logger(__name__)
router = APIRouter()


@router.get("/stats")
@limiter.limit("60/minute")
async def get_admin_stats(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    """Get overall platform statistics.

    Args:
        request: FastAPI request object for rate limiting.
        current_user: Injected by FastAPI dependency.
    """
    try:
        users_result = await asyncio.to_thread(
            lambda: supabase.table("users").select("id", count="exact").execute()
        )
        total_users = users_result.count or 0

        convos_result = await asyncio.to_thread(
            lambda: supabase.table("conversations").select("id", count="exact").execute()
        )
        total_conversations = convos_result.count or 0

        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id", count="exact").execute()
        )
        total_documents = docs_result.count or 0

        messages_result = await asyncio.to_thread(
            lambda: supabase.table("messages").select("id", count="exact").execute()
        )
        total_messages = messages_result.count or 0

        logger.info(
            f"Stats: {total_users} users, {total_conversations} conversations, "
            f"{total_documents} documents, {total_messages} messages"
        )

        return {
            "success": True,
            "total_users": total_users,
            "total_conversations": total_conversations,
            "total_documents": total_documents,
            "total_messages": total_messages,
        }
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
