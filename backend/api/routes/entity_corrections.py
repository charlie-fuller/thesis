"""Entity Corrections API endpoints.

Record and retrieve correction history.

Version: 1.0.0
Created: 2026-01-23
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase
from services.entity_registry_manager import EntityRegistryManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entity-corrections", tags=["Entity Corrections"])


# =============================================================================
# Request/Response Models
# =============================================================================


class RecordCorrectionRequest(BaseModel):
    entity_type: str  # 'person' or 'organization'
    original_value: str
    corrected_value: str
    source_document_id: Optional[str] = None
    source_candidate_id: Optional[str] = None
    context: Optional[str] = None


class CorrectionEntry(BaseModel):
    id: str
    entity_type: str
    original_value: str
    corrected_value: str
    source_document_id: Optional[str]
    source_candidate_id: Optional[str]
    corrected_by: Optional[str]
    correction_context: Optional[str]
    created_at: str


class CorrectionHistoryResponse(BaseModel):
    corrections: list[CorrectionEntry]
    count: int


# =============================================================================
# Endpoints
# =============================================================================


@router.post("")
async def record_correction(
    request: RecordCorrectionRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Record a correction and learn from it.

    The original value will be added as an alias to the corrected entry.
    If the corrected entry doesn't exist, it will be created.
    """
    client_id = current_user.get("client_id")
    user_id = current_user.get("id")

    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    if request.entity_type not in ("person", "organization"):
        raise HTTPException(status_code=400, detail="entity_type must be 'person' or 'organization'")

    manager = EntityRegistryManager(supabase)
    success = await manager.learn_from_correction(
        client_id=client_id,
        entity_type=request.entity_type,
        original_value=request.original_value,
        corrected_value=request.corrected_value,
        source_document_id=request.source_document_id,
        source_candidate_id=request.source_candidate_id,
        corrected_by=user_id,
        context=request.context,
    )

    return {
        "success": success,
        "message": (f"Recorded correction: '{request.original_value}' -> '{request.corrected_value}'"),
    }


@router.get("/history", response_model=CorrectionHistoryResponse)
async def get_correction_history(
    entity_type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get recent correction history."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    if entity_type and entity_type not in ("person", "organization"):
        raise HTTPException(status_code=400, detail="entity_type must be 'person' or 'organization'")

    manager = EntityRegistryManager(supabase)
    corrections = await manager.get_correction_history(client_id, entity_type, limit)

    return CorrectionHistoryResponse(
        corrections=[
            CorrectionEntry(
                id=c["id"],
                entity_type=c["entity_type"],
                original_value=c["original_value"],
                corrected_value=c["corrected_value"],
                source_document_id=c.get("source_document_id"),
                source_candidate_id=c.get("source_candidate_id"),
                corrected_by=c.get("corrected_by"),
                correction_context=c.get("correction_context"),
                created_at=c["created_at"],
            )
            for c in corrections
        ],
        count=len(corrections),
    )


@router.post("/batch-apply")
async def batch_apply_corrections(
    entity_type: str,
    original_value: str,
    corrected_value: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Apply a correction to all historical instances.

    This updates existing stakeholders/opportunities that have the
    original (incorrect) value.
    """
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID required")

    if entity_type not in ("person", "organization"):
        raise HTTPException(status_code=400, detail="entity_type must be 'person' or 'organization'")

    updated_count = 0

    try:
        if entity_type == "person":
            # Update stakeholder names
            result = (
                supabase.table("stakeholders")
                .update({"name": corrected_value})
                .eq("client_id", client_id)
                .eq("name", original_value)
                .execute()
            )
            updated_count = len(result.data) if result.data else 0

        elif entity_type == "organization":
            # Update stakeholder organizations
            result = (
                supabase.table("stakeholders")
                .update({"organization": corrected_value})
                .eq("client_id", client_id)
                .eq("organization", original_value)
                .execute()
            )
            updated_count = len(result.data) if result.data else 0

            # Also update opportunities department if applicable
            opp_result = (
                supabase.table("ai_projects")
                .update({"department": corrected_value})
                .eq("client_id", client_id)
                .eq("department", original_value)
                .execute()
            )
            updated_count += len(opp_result.data) if opp_result.data else 0

        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} records",
        }

    except Exception as e:
        logger.error(f"Error applying batch corrections: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
