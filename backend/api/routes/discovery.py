"""Discovery API Routes.

Unified endpoints for the Discovery Inbox feature.
Provides counts and data across all candidate types (tasks, opportunities, stakeholders).

Note: Only shows candidates from the last 3 weeks to avoid stale items.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import pb_client as pb

# Only show candidates from the last N weeks
DISCOVERY_MAX_AGE_WEEKS = 2

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class DiscoveryCounts(BaseModel):
    """Counts of pending candidates across all types."""

    tasks: int
    projects: int
    opportunities: Optional[int] = None  # Backward compatibility alias
    stakeholders: int
    total: int


class ScanningStatus(BaseModel):
    """Status of document scanning for discovery extraction."""

    active: bool
    pending_documents: int = 0
    message: Optional[str] = None
    current_document: Optional[str] = None


class TaskCandidateItem(BaseModel):
    """Task candidate for discovery panel."""

    id: str
    title: str
    description: Optional[str]
    assignee_name: Optional[str]
    suggested_due_date: Optional[str]
    team: Optional[str]
    source_document_name: Optional[str]
    confidence: str
    created_at: str


class ProjectCandidateItem(BaseModel):
    """Project candidate for discovery panel."""

    id: str
    title: str
    description: Optional[str]
    department: Optional[str]
    source_document_name: Optional[str]
    suggested_roi_potential: Optional[int]
    suggested_effort: Optional[int]
    suggested_alignment: Optional[int]
    suggested_readiness: Optional[int]
    confidence: str
    matched_project_id: Optional[str]
    match_reason: Optional[str]
    created_at: str


class StakeholderCandidateItem(BaseModel):
    """Stakeholder candidate for discovery panel."""

    id: str
    name: str
    role: Optional[str]
    department: Optional[str]
    source_document_name: Optional[str]
    initial_sentiment: Optional[str]
    confidence: str
    potential_match_stakeholder_id: Optional[str]
    created_at: str


class DiscoveryAllResponse(BaseModel):
    """All pending candidates for inline review."""

    tasks: List[TaskCandidateItem]
    projects: List[ProjectCandidateItem]
    opportunities: Optional[List[ProjectCandidateItem]] = None  # Backward compatibility alias
    stakeholders: List[StakeholderCandidateItem]
    counts: DiscoveryCounts
    scanning: Optional[ScanningStatus] = None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/counts", response_model=DiscoveryCounts)
async def get_discovery_counts():
    """Get counts of pending candidates across all types.

    Used for dashboard badge display showing total pending items.
    """
    # Only show candidates from the last N weeks
    cutoff_date = (datetime.now(timezone.utc) - timedelta(weeks=DISCOVERY_MAX_AGE_WEEKS)).isoformat()
    esc_cutoff = pb.escape_filter(cutoff_date)

    # Get task candidates count
    tasks_count = pb.count(
        "task_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
    )

    # Get project candidates count
    opps_count = pb.count(
        "project_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
    )

    # Get stakeholder candidates count
    stakeholders_count = pb.count(
        "stakeholder_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
    )

    return {
        "tasks": tasks_count,
        "projects": opps_count,
        "stakeholders": stakeholders_count,
        "total": tasks_count + opps_count + stakeholders_count,
    }


@router.get("/all", response_model=DiscoveryAllResponse)
async def get_all_pending_candidates(
    limit: int = Query(20, ge=1, le=100),
):
    """Get all pending candidates for inline review.

    Returns tasks, projects, and stakeholders with their counts.
    Used by the unified discovery panel for carousel-style review.
    """
    # Only show candidates from the last N weeks
    cutoff_date = (datetime.now(timezone.utc) - timedelta(weeks=DISCOVERY_MAX_AGE_WEEKS)).isoformat()
    esc_cutoff = pb.escape_filter(cutoff_date)

    # Get pending task candidates
    tasks_result = pb.list_records(
        "task_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
        sort="-created",
        per_page=limit,
    )

    tasks = [
        {
            "id": t["id"],
            "title": t["title"],
            "description": t.get("description"),
            "assignee_name": t.get("assignee_name"),
            "suggested_due_date": t.get("suggested_due_date"),
            "team": t.get("team"),
            "source_document_name": t.get("source_document_name"),
            "confidence": t.get("confidence", "medium"),
            "created_at": t.get("created", ""),
        }
        for t in tasks_result.get("items", [])
    ]

    # Get pending project candidates
    opps_result = pb.list_records(
        "project_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
        sort="-created",
        per_page=limit,
    )

    projects = [
        {
            "id": o["id"],
            "title": o["title"],
            "description": o.get("description"),
            "department": o.get("department"),
            "source_document_name": o.get("source_document_name"),
            "suggested_roi_potential": o.get("suggested_roi_potential"),
            "suggested_effort": o.get("suggested_effort"),
            "suggested_alignment": o.get("suggested_alignment"),
            "suggested_readiness": o.get("suggested_readiness"),
            "confidence": o.get("confidence", "medium"),
            "matched_project_id": o.get("matched_project_id"),
            "match_reason": o.get("match_reason"),
            "created_at": o.get("created", ""),
        }
        for o in opps_result.get("items", [])
    ]

    # Get pending stakeholder candidates
    stakeholders_result = pb.list_records(
        "stakeholder_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
        sort="-created",
        per_page=limit,
    )

    stakeholders = [
        {
            "id": s["id"],
            "name": s["name"],
            "role": s.get("role"),
            "department": s.get("department"),
            "source_document_name": s.get("source_document_name"),
            "initial_sentiment": s.get("initial_sentiment"),
            "confidence": s.get("confidence", "medium"),
            "potential_match_stakeholder_id": s.get("potential_match_stakeholder_id"),
            "created_at": s.get("created", ""),
        }
        for s in stakeholders_result.get("items", [])
    ]

    # Get actual counts (not limited)
    tasks_count = pb.count(
        "task_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
    )

    opps_count = pb.count(
        "project_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
    )

    stakeholders_count = pb.count(
        "stakeholder_candidates",
        filter=f"status='pending' && created>='{esc_cutoff}'",
    )

    # Check for pending Granola documents (synced but not yet scanned for extraction)
    scanning_status = None
    try:
        from services.granola_scanner import get_scan_status

        # Check if a background scan is actually running
        from api.routes.pipeline import _active_user_scans

        scan_actually_running = len(_active_user_scans) > 0

        # Use Granola scanner's status function to get accurate pending count
        granola_status = get_scan_status()
        pending_count = granola_status.get("pending_files", 0)

        if scan_actually_running and pending_count > 0:
            next_doc = granola_status.get("next_document")
            if next_doc:
                display_name = next_doc[:40] + "..." if len(next_doc) > 40 else next_doc
                message = f"Analyzing: {display_name}"
            else:
                message = f"Analyzing {pending_count} meeting{'s' if pending_count != 1 else ''}..."
            scanning_status = ScanningStatus(
                active=True,
                pending_documents=pending_count,
                message=message,
                current_document=next_doc,
            )
        else:
            scanning_status = ScanningStatus(
                active=False,
                pending_documents=pending_count,
            )
    except Exception as e:
        logger.warning(f"Failed to get scanning status: {e}")
        scanning_status = ScanningStatus(active=False, pending_documents=0)

    return {
        "tasks": tasks,
        "projects": projects,
        "opportunities": projects,  # Backward compatibility
        "stakeholders": stakeholders,
        "counts": {
            "tasks": tasks_count,
            "projects": opps_count,
            "opportunities": opps_count,  # Backward compatibility
            "stakeholders": stakeholders_count,
            "total": tasks_count + opps_count + stakeholders_count,
        },
        "scanning": scanning_status,
    }
