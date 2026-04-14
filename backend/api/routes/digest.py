"""Task Digest API Routes.

Endpoints for generating task digest documents.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/digest", tags=["Task Digest"])


# ============================================================================
# MODELS
# ============================================================================


class DigestPreviewResponse(BaseModel):
    """Response model for digest preview."""

    status: str
    title: Optional[str] = None
    summary: Optional[str] = None
    markdown_content: Optional[str] = None
    health_score: Optional[int] = None
    total_active: Optional[int] = None
    overdue_count: Optional[int] = None
    due_today_count: Optional[int] = None
    message: Optional[str] = None


class DigestSaveResponse(BaseModel):
    """Response model for saving digest to KB."""

    status: str
    document_id: Optional[str] = None
    filename: Optional[str] = None
    is_update: Optional[bool] = None
    message: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/preview", response_model=DigestPreviewResponse)
async def preview_digest():
    """Generate a digest preview without saving it."""
    from services.task_digest import TaskDigestService

    try:
        # TODO: TaskDigestService still takes supabase -- needs service-level migration
        digest_service = TaskDigestService(None)

        digest = await digest_service.generate_digest(None)

        return DigestPreviewResponse(
            status="success",
            title=digest.title,
            summary=digest.summary,
            markdown_content=digest.markdown_content,
            health_score=digest.health_score,
            total_active=digest.total_active,
            overdue_count=digest.overdue_count,
            due_today_count=digest.due_today_count,
        )

    except Exception as e:
        logger.error(f"Error generating digest preview: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/save", response_model=DigestSaveResponse)
async def save_digest_to_kb():
    """Generate and save a task digest to the Knowledge Base.

    Creates a new document or updates today's existing digest.
    The document is automatically tagged for the Taskmaster agent.
    """
    from services.task_digest import TaskDigestService

    try:
        # TODO: TaskDigestService still takes supabase -- needs service-level migration
        digest_service = TaskDigestService(None)

        # Generate digest
        digest = await digest_service.generate_digest(None)

        # Save to KB (single-tenant: no client_id needed)
        result = await digest_service.save_digest_to_kb(digest, None)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return DigestSaveResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving digest to KB: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
