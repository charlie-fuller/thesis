"""Admin cache routes - cache management."""

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import require_admin
from logger_config import get_logger

from ._shared import limiter

logger = get_logger(__name__)
router = APIRouter()


@router.post("/clear-system-instructions-cache")
@limiter.limit("10/minute")
async def clear_system_instructions_cache(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    """Clear all system instructions cache (Redis + lru_cache).

    Use this when system instructions have been updated.
    Requires admin role.

    Args:
        request: FastAPI request object for rate limiting.
        current_user: Injected by FastAPI dependency.
    """
    try:
        from cache import invalidate_all_system_instructions

        count = invalidate_all_system_instructions()
        logger.info(f"Admin {current_user.get('email')} cleared system instructions cache")

        return {
            "success": True,
            "message": f"Cleared {count} Redis cache entries and lru_cache",
            "redis_entries_cleared": count,
        }
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/clear-search-cache")
@limiter.limit("10/minute")
async def clear_search_cache(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    """Clear all RAG search cache (Redis).

    Use this when documents have been uploaded/updated and cached search results are stale.
    Requires admin role.

    Args:
        request: FastAPI request object for rate limiting.
        current_user: Injected by FastAPI dependency.
    """
    try:
        from cache import invalidate_search_cache

        invalidate_search_cache("")
        logger.info(f"Admin {current_user.get('email')} cleared search cache")

        return {"success": True, "message": "Cleared all RAG search cache entries"}
    except Exception as e:
        logger.error(f"Search cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
