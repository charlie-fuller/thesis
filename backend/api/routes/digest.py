"""
Task Digest API Routes

Endpoints for generating task digest documents.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from logger_config import get_logger
from auth import get_current_user
from database import get_supabase

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
async def preview_digest(user=Depends(get_current_user)):
    """
    Generate a digest preview without saving it.

    Returns the markdown content that would be saved to KB.
    """
    from services.task_digest import TaskDigestService

    try:
        supabase = get_supabase()
        digest_service = TaskDigestService(supabase)

        digest = await digest_service.generate_digest(user["id"])

        return DigestPreviewResponse(
            status="success",
            title=digest.title,
            summary=digest.summary,
            markdown_content=digest.markdown_content,
            health_score=digest.health_score,
            total_active=digest.total_active,
            overdue_count=digest.overdue_count,
            due_today_count=digest.due_today_count
        )

    except Exception as e:
        logger.error(f"Error generating digest preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save", response_model=DigestSaveResponse)
async def save_digest_to_kb(user=Depends(get_current_user)):
    """
    Generate and save a task digest to the Knowledge Base.

    Creates a new document or updates today's existing digest.
    The document is automatically tagged for the Taskmaster agent.
    """
    from services.task_digest import TaskDigestService

    try:
        supabase = get_supabase()
        digest_service = TaskDigestService(supabase)

        # Generate digest
        digest = await digest_service.generate_digest(user["id"])

        # Get user's client_id
        user_result = supabase.table('users').select('client_id').eq(
            'id', user["id"]
        ).single().execute()

        if not user_result.data:
            raise HTTPException(status_code=400, detail="User not found")

        client_id = user_result.data['client_id']

        # Save to KB
        result = await digest_service.save_digest_to_kb(digest, client_id)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return DigestSaveResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving digest to KB: {e}")
        raise HTTPException(status_code=500, detail=str(e))
