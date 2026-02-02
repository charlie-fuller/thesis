"""Discovery API Routes.

Unified endpoints for the Discovery Inbox feature.
Provides counts and data across all candidate types (tasks, opportunities, stakeholders).

Note: Only shows candidates from the last 3 weeks to avoid stale items.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase

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
async def get_discovery_counts(
    current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get counts of pending candidates across all types.

    Used for dashboard badge display showing total pending items.
    """
    client_id = current_user["client_id"]
    if not client_id:
        raise HTTPException(status_code=400, detail="User has no client_id assigned")

    # Only show candidates from the last N weeks
    cutoff_date = (
        datetime.now(timezone.utc) - timedelta(weeks=DISCOVERY_MAX_AGE_WEEKS)
    ).isoformat()

    # Get task candidates count
    tasks_result = (
        supabase.table("task_candidates")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .execute()
    )
    tasks_count = tasks_result.count or 0

    # Get project candidates count
    opps_result = (
        supabase.table("project_candidates")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .execute()
    )
    opps_count = opps_result.count or 0

    # Get stakeholder candidates count
    stakeholders_result = (
        supabase.table("stakeholder_candidates")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .execute()
    )
    stakeholders_count = stakeholders_result.count or 0

    return {
        "tasks": tasks_count,
        "projects": opps_count,
        "stakeholders": stakeholders_count,
        "total": tasks_count + opps_count + stakeholders_count,
    }


@router.get("/all", response_model=DiscoveryAllResponse)
async def get_all_pending_candidates(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get all pending candidates for inline review.

    Returns tasks, projects, and stakeholders with their counts.
    Used by the unified discovery panel for carousel-style review.
    """
    client_id = current_user["client_id"]
    if not client_id:
        raise HTTPException(status_code=400, detail="User has no client_id assigned")

    # Only show candidates from the last N weeks
    cutoff_date = (
        datetime.now(timezone.utc) - timedelta(weeks=DISCOVERY_MAX_AGE_WEEKS)
    ).isoformat()

    # Get pending task candidates
    tasks_result = (
        supabase.table("task_candidates")
        .select("*")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
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
            "created_at": t["created_at"],
        }
        for t in tasks_result.data
    ]

    # Get pending project candidates
    opps_result = (
        supabase.table("project_candidates")
        .select("*")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
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
            "created_at": o["created_at"],
        }
        for o in opps_result.data
    ]

    # Get pending stakeholder candidates
    stakeholders_result = (
        supabase.table("stakeholder_candidates")
        .select("*")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
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
            "created_at": s["created_at"],
        }
        for s in stakeholders_result.data
    ]

    # Get actual counts (not limited)
    tasks_count_result = (
        supabase.table("task_candidates")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .execute()
    )
    tasks_count = tasks_count_result.count or 0

    opps_count_result = (
        supabase.table("project_candidates")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .execute()
    )
    opps_count = opps_count_result.count or 0

    stakeholders_count_result = (
        supabase.table("stakeholder_candidates")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .gte("created_at", cutoff_date)
        .execute()
    )
    stakeholders_count = stakeholders_count_result.count or 0

    # Check for pending Granola documents (synced but not yet scanned for extraction)
    scanning_status = None
    try:
        from services.granola_scanner import get_scan_status

        user_id = current_user["id"]

        # Use Granola scanner's status function to get accurate pending count
        granola_status = get_scan_status(user_id)
        pending_count = granola_status.get("pending_files", 0)

        if pending_count > 0:
            next_doc = granola_status.get("next_document")
            if next_doc:
                # Truncate long filenames
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
            scanning_status = ScanningStatus(active=False, pending_documents=0)
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
