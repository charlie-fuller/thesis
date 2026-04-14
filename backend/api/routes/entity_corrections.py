"""Entity Corrections API endpoints.

Record and retrieve correction history.

Version: 1.0.0
Created: 2026-01-23
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import pb_client as pb
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
async def record_correction(request: RecordCorrectionRequest):
    """Record a correction and learn from it.

    The original value will be added as an alias to the corrected entry.
    If the corrected entry doesn't exist, it will be created.
    """
    if request.entity_type not in ("person", "organization"):
        raise HTTPException(status_code=400, detail="entity_type must be 'person' or 'organization'")

    # TODO: EntityRegistryManager still takes supabase -- needs service-level migration
    manager = EntityRegistryManager(None)
    success = await manager.learn_from_correction(
        client_id=None,
        entity_type=request.entity_type,
        original_value=request.original_value,
        corrected_value=request.corrected_value,
        source_document_id=request.source_document_id,
        source_candidate_id=request.source_candidate_id,
        corrected_by=None,
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
):
    """Get recent correction history."""
    if entity_type and entity_type not in ("person", "organization"):
        raise HTTPException(status_code=400, detail="entity_type must be 'person' or 'organization'")

    # TODO: EntityRegistryManager still takes supabase -- needs service-level migration
    manager = EntityRegistryManager(None)
    corrections = await manager.get_correction_history(None, entity_type, limit)

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
):
    """Apply a correction to all historical instances.

    This updates existing stakeholders/opportunities that have the
    original (incorrect) value.
    """
    if entity_type not in ("person", "organization"):
        raise HTTPException(status_code=400, detail="entity_type must be 'person' or 'organization'")

    updated_count = 0

    try:
        safe_original = pb.escape_filter(original_value)

        if entity_type == "person":
            # Update stakeholder names
            records = pb.get_all(
                "stakeholders",
                filter=f"name='{safe_original}'",
                fields="id",
            )
            for r in records:
                pb.update_record("stakeholders", r["id"], {"name": corrected_value})
            updated_count = len(records)

        elif entity_type == "organization":
            # Update stakeholder organizations
            records = pb.get_all(
                "stakeholders",
                filter=f"organization='{safe_original}'",
                fields="id",
            )
            for r in records:
                pb.update_record("stakeholders", r["id"], {"organization": corrected_value})
            updated_count = len(records)

            # Also update opportunities department if applicable
            opp_records = pb.get_all(
                "ai_projects",
                filter=f"department='{safe_original}'",
                fields="id",
            )
            for r in opp_records:
                pb.update_record("ai_projects", r["id"], {"department": corrected_value})
            updated_count += len(opp_records)

        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} records",
        }

    except Exception as e:
        logger.error(f"Error applying batch corrections: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
