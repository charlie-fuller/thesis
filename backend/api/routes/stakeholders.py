"""
Stakeholders API Routes

Endpoints for managing stakeholders, their insights, and stakeholder candidates.
"""

import logging
import os
from typing import Optional
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stakeholders", tags=["stakeholders"])


class StakeholderCreate(BaseModel):
    """Create a new stakeholder."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    organization: str = "Contentful"
    notes: Optional[str] = None
    # Project-triage fields
    priority_level: Optional[str] = "tier_3"
    ai_priorities: Optional[list] = None
    pain_points: Optional[list] = None
    win_conditions: Optional[list] = None
    communication_style: Optional[str] = None
    relationship_status: Optional[str] = "new"
    open_questions: Optional[list] = None
    reports_to_name: Optional[str] = None
    team_size: Optional[int] = None


class StakeholderUpdate(BaseModel):
    """Update a stakeholder."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    organization: Optional[str] = None
    engagement_level: Optional[str] = None
    notes: Optional[str] = None
    # Project-triage fields
    priority_level: Optional[str] = None
    ai_priorities: Optional[list] = None
    pain_points: Optional[list] = None
    win_conditions: Optional[list] = None
    communication_style: Optional[str] = None
    relationship_status: Optional[str] = None
    open_questions: Optional[list] = None
    last_contact: Optional[str] = None
    reports_to_name: Optional[str] = None
    team_size: Optional[int] = None


class StakeholderResponse(BaseModel):
    """Stakeholder response model."""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    department: Optional[str]
    organization: str
    sentiment_score: float
    sentiment_trend: str
    engagement_level: str
    alignment_score: float
    total_interactions: int
    last_interaction: Optional[str]
    key_concerns: list
    interests: list
    notes: Optional[str]
    created_at: str
    # Project-triage fields
    priority_level: Optional[str] = "tier_3"
    ai_priorities: Optional[list] = None
    pain_points: Optional[list] = None
    win_conditions: Optional[list] = None
    communication_style: Optional[str] = None
    relationship_status: Optional[str] = "new"
    open_questions: Optional[list] = None
    last_contact: Optional[str] = None
    reports_to_name: Optional[str] = None
    team_size: Optional[int] = None


class StakeholderInsightResponse(BaseModel):
    """Stakeholder insight response."""
    id: str
    insight_type: str
    content: str
    quote: Optional[str]
    confidence: float
    is_resolved: bool
    meeting_title: Optional[str]
    meeting_date: Optional[str]
    created_at: str


class InsightResolve(BaseModel):
    """Resolve an insight."""
    resolution_notes: Optional[str] = None


# ============================================================================
# STAKEHOLDER CANDIDATE MODELS
# ============================================================================

class StakeholderCandidateResponse(BaseModel):
    """Stakeholder candidate response."""
    id: str
    name: str
    role: Optional[str]
    department: Optional[str]
    organization: Optional[str]
    email: Optional[str]
    key_concerns: list
    interests: list
    initial_sentiment: Optional[str]
    influence_level: Optional[str]
    source_document_id: Optional[str]
    source_document_name: Optional[str]
    source_text: Optional[str]
    extraction_context: Optional[str]
    related_opportunity_ids: list
    related_task_ids: list
    status: str
    confidence: str
    potential_match_stakeholder_id: Optional[str]
    potential_match_name: Optional[str]
    match_confidence: Optional[float]
    created_at: str


class CandidateAccept(BaseModel):
    """Accept a stakeholder candidate."""
    # Override extracted values if needed
    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class CandidateReject(BaseModel):
    """Reject a stakeholder candidate."""
    reason: Optional[str] = None


class CandidateMerge(BaseModel):
    """Merge candidate into existing stakeholder."""
    target_stakeholder_id: str
    update_concerns: bool = True
    update_interests: bool = True


class ScanDocumentsRequest(BaseModel):
    """Request to scan documents for stakeholders."""
    force_rescan: bool = False
    since_days: int = 90
    limit: int = 20


@router.get("/", response_model=list[StakeholderResponse])
async def list_stakeholders(
    department: Optional[str] = None,
    engagement_level: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List all stakeholders for the current client."""
    query = supabase.table("stakeholders") \
        .select("*") \
        .eq("client_id", current_user["client_id"])

    if department:
        query = query.eq("department", department)
    if engagement_level:
        query = query.eq("engagement_level", engagement_level)

    result = query.order("name").range(offset, offset + limit - 1).execute()

    return [_format_stakeholder(s) for s in result.data]


# ============================================================================
# ENGAGEMENT ANALYTICS ENDPOINTS
# ============================================================================
# NOTE: Static routes must be defined before parameterized routes (/{stakeholder_id})

@router.get("/engagement/trends")
async def get_engagement_trends(
    days: int = 90,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get engagement level distribution over time for trend analytics.

    Returns data suitable for a stacked area chart showing how engagement
    levels have changed over time.

    Args:
        days: Number of days to look back (default 90)

    Returns:
        List of weekly snapshots with counts per engagement level
    """
    from datetime import timedelta

    client_id = current_user["client_id"]

    # Calculate start date
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get engagement history for the period
    result = supabase.table("engagement_level_history") \
        .select("engagement_level, calculated_at") \
        .eq("client_id", client_id) \
        .gte("calculated_at", start_date.isoformat()) \
        .order("calculated_at") \
        .execute()

    if not result.data:
        # Return empty trends if no history
        return []

    # Group by week and count engagement levels
    from collections import defaultdict

    weekly_data = defaultdict(lambda: {
        "champion": 0,
        "supporter": 0,
        "neutral": 0,
        "skeptic": 0,
        "blocker": 0
    })

    for record in result.data:
        # Get week start (Monday)
        calc_date = datetime.fromisoformat(record["calculated_at"].replace("Z", "+00:00"))
        week_start = calc_date - timedelta(days=calc_date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        level = record["engagement_level"].lower()
        if level in weekly_data[week_key]:
            weekly_data[week_key][level] += 1

    # Convert to sorted list
    trends = [
        {"date": date, **counts}
        for date, counts in sorted(weekly_data.items())
    ]

    return trends


@router.get("/engagement/changes")
async def get_engagement_changes(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get recent engagement level changes (who moved up/down).

    Returns stakeholders whose engagement level changed recently,
    with direction indicators.

    Args:
        days: Number of days to look back (default 30)

    Returns:
        List of engagement changes with stakeholder info
    """
    from datetime import timedelta

    client_id = current_user["client_id"]
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get history records where level changed (previous_level is not null)
    result = supabase.table("engagement_level_history") \
        .select("stakeholder_id, engagement_level, previous_level, calculation_reason, calculated_at") \
        .eq("client_id", client_id) \
        .gte("calculated_at", start_date.isoformat()) \
        .not_.is_("previous_level", "null") \
        .order("calculated_at", desc=True) \
        .limit(50) \
        .execute()

    if not result.data:
        return []

    # Get stakeholder names
    stakeholder_ids = list(set(r["stakeholder_id"] for r in result.data))
    stakeholders = supabase.table("stakeholders") \
        .select("id, name") \
        .in_("id", stakeholder_ids) \
        .execute()

    name_map = {s["id"]: s["name"] for s in stakeholders.data}

    # Calculate direction
    level_order = ["blocker", "skeptic", "neutral", "supporter", "champion"]

    def get_direction(prev: str, new: str) -> str:
        prev_idx = level_order.index(prev.lower()) if prev.lower() in level_order else 2
        new_idx = level_order.index(new.lower()) if new.lower() in level_order else 2
        if new_idx > prev_idx:
            return "up"
        elif new_idx < prev_idx:
            return "down"
        return "same"

    changes = []
    for record in result.data:
        changes.append({
            "stakeholder_id": record["stakeholder_id"],
            "name": name_map.get(record["stakeholder_id"], "Unknown"),
            "previous_level": record["previous_level"],
            "new_level": record["engagement_level"],
            "direction": get_direction(record["previous_level"], record["engagement_level"]),
            "change_date": record["calculated_at"],
            "reason": record["calculation_reason"]
        })

    return changes


@router.post("/engagement/recalculate")
async def trigger_engagement_recalculation(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Manually trigger engagement recalculation for the current client.

    This is an admin function for testing or forcing an immediate update.
    """
    from services.engagement_scheduler import trigger_manual_calculation

    client_id = current_user["client_id"]

    try:
        result = await trigger_manual_calculation(client_id=client_id)
        return {
            "message": "Engagement recalculation completed",
            "total": result.get("total", 0),
            "changed": result.get("changed", 0),
            "promotions": result.get("promotions", 0),
            "demotions": result.get("demotions", 0),
            "errors": result.get("errors", 0)
        }
    except Exception as e:
        logger.error(f"Engagement recalculation failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/dashboard")
async def get_stakeholder_dashboard(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get dashboard metrics for stakeholders.

    Returns:
    - Sentiment trends
    - Engagement distribution
    - Recent concerns
    - Alignment scores
    """
    client_id = current_user["client_id"]

    # Get all stakeholders
    stakeholders = supabase.table("stakeholders") \
        .select("*") \
        .eq("client_id", client_id) \
        .execute()

    # Get recent unresolved concerns
    concerns = supabase.table("stakeholder_insights") \
        .select("*, stakeholders(name)") \
        .eq("insight_type", "concern") \
        .eq("is_resolved", False) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()

    # Calculate metrics
    total = len(stakeholders.data)
    if total == 0:
        return {
            "total_stakeholders": 0,
            "engagement_distribution": {},
            "average_sentiment": 0,
            "average_alignment": 0,
            "recent_concerns": [],
            "stakeholders_needing_attention": []
        }

    # Engagement distribution
    engagement_dist = {}
    for s in stakeholders.data:
        level = s.get("engagement_level", "neutral")
        engagement_dist[level] = engagement_dist.get(level, 0) + 1

    # Average scores
    avg_sentiment = sum(s.get("sentiment_score", 0) for s in stakeholders.data) / total
    avg_alignment = sum(s.get("alignment_score", 0.5) for s in stakeholders.data) / total

    # Stakeholders needing attention (negative sentiment or low engagement)
    needs_attention = [
        _format_stakeholder(s) for s in stakeholders.data
        if s.get("sentiment_score", 0) < -0.2 or s.get("engagement_level") in ["skeptic", "blocker"]
    ]

    return {
        "total_stakeholders": total,
        "engagement_distribution": engagement_dist,
        "average_sentiment": round(avg_sentiment, 2),
        "average_alignment": round(avg_alignment, 2),
        "recent_concerns": [
            {
                "id": c["id"],
                "stakeholder_name": c["stakeholders"]["name"] if c.get("stakeholders") else "Unknown",
                "content": c["content"],
                "created_at": c["created_at"]
            }
            for c in concerns.data
        ],
        "stakeholders_needing_attention": needs_attention[:5]
    }


# ============================================================================
# STAKEHOLDER CANDIDATES ENDPOINTS
# ============================================================================
# NOTE: These static routes must be defined before parameterized routes (/{stakeholder_id})

@router.get("/candidates", response_model=list[StakeholderCandidateResponse])
async def list_stakeholder_candidates(
    status: Optional[str] = "pending",
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List stakeholder candidates for review."""
    query = supabase.table("stakeholder_candidates") \
        .select("*") \
        .eq("client_id", current_user["client_id"])

    if status:
        query = query.eq("status", status)

    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    # Get potential match names
    candidates_with_matches = []
    for c in result.data:
        formatted = _format_candidate(c)

        # Get match name if there's a potential match
        if c.get("potential_match_stakeholder_id"):
            match = supabase.table("stakeholders") \
                .select("name") \
                .eq("id", c["potential_match_stakeholder_id"]) \
                .single() \
                .execute()
            if match.data:
                formatted["potential_match_name"] = match.data["name"]

        candidates_with_matches.append(formatted)

    return candidates_with_matches


@router.get("/candidates/count")
async def get_candidate_count(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get count of pending stakeholder candidates."""
    result = supabase.table("stakeholder_candidates") \
        .select("id", count="exact") \
        .eq("client_id", current_user["client_id"]) \
        .eq("status", "pending") \
        .execute()

    return {"count": result.count if result.count else 0}


@router.post("/candidates/{candidate_id}/accept", response_model=StakeholderResponse)
async def accept_stakeholder_candidate(
    candidate_id: str,
    accept: CandidateAccept = CandidateAccept(),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Accept a stakeholder candidate and create the stakeholder."""
    # Get the candidate
    candidate = supabase.table("stakeholder_candidates") \
        .select("*") \
        .eq("id", candidate_id) \
        .eq("client_id", current_user["client_id"]) \
        .eq("status", "pending") \
        .single() \
        .execute()

    if not candidate.data:
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    c = candidate.data

    # Create the stakeholder (use overrides if provided)
    stakeholder_data = {
        "client_id": current_user["client_id"],
        "name": accept.name or c["name"],
        "email": accept.email or c.get("email"),
        "role": accept.role or c.get("role"),
        "department": accept.department or c.get("department"),
        "organization": accept.organization or c.get("organization") or "Contentful",
        "key_concerns": c.get("key_concerns", []),
        "interests": c.get("interests", []),
        "notes": accept.notes,
        "first_interaction": datetime.now(timezone.utc).date().isoformat()
    }

    # Set initial sentiment-based engagement
    sentiment = c.get("initial_sentiment", "neutral")
    if sentiment == "positive":
        stakeholder_data["engagement_level"] = "supporter"
        stakeholder_data["sentiment_score"] = 0.5
    elif sentiment == "negative":
        stakeholder_data["engagement_level"] = "skeptic"
        stakeholder_data["sentiment_score"] = -0.5
    else:
        stakeholder_data["engagement_level"] = "neutral"
        stakeholder_data["sentiment_score"] = 0.0

    # Create stakeholder
    stakeholder_result = supabase.table("stakeholders").insert(stakeholder_data).execute()

    if not stakeholder_result.data:
        raise HTTPException(status_code=500, detail="Failed to create stakeholder")

    new_stakeholder = stakeholder_result.data[0]

    # Link to related entities
    opportunity_ids = c.get("related_opportunity_ids", [])
    task_ids = c.get("related_task_ids", [])

    if opportunity_ids or task_ids:
        from services.stakeholder_linker import link_stakeholder_to_entities
        await link_stakeholder_to_entities(
            supabase, new_stakeholder["id"], opportunity_ids, task_ids
        )

    # Update candidate status
    supabase.table("stakeholder_candidates") \
        .update({
            "status": "accepted",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "accepted_by": current_user["id"],
            "created_stakeholder_id": new_stakeholder["id"]
        }) \
        .eq("id", candidate_id) \
        .execute()

    return _format_stakeholder(new_stakeholder)


@router.post("/candidates/{candidate_id}/reject")
async def reject_stakeholder_candidate(
    candidate_id: str,
    reject: CandidateReject = CandidateReject(),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Reject a stakeholder candidate."""
    result = supabase.table("stakeholder_candidates") \
        .update({
            "status": "rejected",
            "rejection_reason": reject.reason,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }) \
        .eq("id", candidate_id) \
        .eq("client_id", current_user["client_id"]) \
        .eq("status", "pending") \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    return {"message": "Candidate rejected"}


@router.post("/candidates/{candidate_id}/merge")
async def merge_stakeholder_candidate(
    candidate_id: str,
    merge: CandidateMerge,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Merge a candidate into an existing stakeholder."""
    # Get the candidate
    candidate = supabase.table("stakeholder_candidates") \
        .select("*") \
        .eq("id", candidate_id) \
        .eq("client_id", current_user["client_id"]) \
        .eq("status", "pending") \
        .single() \
        .execute()

    if not candidate.data:
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    c = candidate.data

    # Get the target stakeholder
    target = supabase.table("stakeholders") \
        .select("*") \
        .eq("id", merge.target_stakeholder_id) \
        .eq("client_id", current_user["client_id"]) \
        .single() \
        .execute()

    if not target.data:
        raise HTTPException(status_code=404, detail="Target stakeholder not found")

    t = target.data

    # Build update data
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

    # Merge concerns if requested
    if merge.update_concerns and c.get("key_concerns"):
        existing_concerns = t.get("key_concerns", []) or []
        new_concerns = c.get("key_concerns", [])
        # Add only unique concerns
        for concern in new_concerns:
            if concern not in existing_concerns:
                existing_concerns.append(concern)
        update_data["key_concerns"] = existing_concerns

    # Merge interests if requested
    if merge.update_interests and c.get("interests"):
        existing_interests = t.get("interests", []) or []
        new_interests = c.get("interests", [])
        # Add only unique interests
        for interest in new_interests:
            if interest not in existing_interests:
                existing_interests.append(interest)
        update_data["interests"] = existing_interests

    # Update target stakeholder
    supabase.table("stakeholders") \
        .update(update_data) \
        .eq("id", merge.target_stakeholder_id) \
        .execute()

    # Link to related entities
    opportunity_ids = c.get("related_opportunity_ids", [])
    task_ids = c.get("related_task_ids", [])

    if opportunity_ids or task_ids:
        from services.stakeholder_linker import link_stakeholder_to_entities
        await link_stakeholder_to_entities(
            supabase, merge.target_stakeholder_id, opportunity_ids, task_ids
        )

    # Update candidate status
    supabase.table("stakeholder_candidates") \
        .update({
            "status": "merged",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "accepted_by": current_user["id"],
            "merged_into_stakeholder_id": merge.target_stakeholder_id
        }) \
        .eq("id", candidate_id) \
        .execute()

    return {"message": "Candidate merged into existing stakeholder"}


@router.post("/candidates/bulk")
async def bulk_process_candidates(
    candidate_ids: list[str],
    action: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Bulk accept or reject candidates."""
    if action not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")

    results = {"processed": 0, "errors": []}

    for candidate_id in candidate_ids:
        try:
            if action == "accept":
                await accept_stakeholder_candidate(
                    candidate_id,
                    CandidateAccept(),
                    current_user,
                    supabase
                )
            else:
                await reject_stakeholder_candidate(
                    candidate_id,
                    CandidateReject(),
                    current_user,
                    supabase
                )
            results["processed"] += 1
        except HTTPException as e:
            results["errors"].append(f"{candidate_id}: {e.detail}")
        except Exception as e:
            results["errors"].append(f"{candidate_id}: {str(e)}")

    return results


@router.post("/scan-documents")
async def scan_documents_for_stakeholders(
    request: ScanDocumentsRequest = ScanDocumentsRequest(),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Manually trigger stakeholder extraction from meeting documents.

    Scans meeting summaries and transcripts for stakeholder mentions,
    creates candidates for review.
    """
    from services.stakeholder_scanner import StakeholderScanner

    # Create Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    anthropic_client = anthropic.Anthropic(api_key=api_key)

    scanner = StakeholderScanner(supabase, anthropic_client)

    # Run scan
    result = await scanner.scan_documents(
        client_id=current_user["client_id"],
        user_id=current_user["id"],
        force_rescan=request.force_rescan,
        since_days=request.since_days,
        limit=request.limit
    )

    return {
        "message": "Stakeholder scan completed",
        "documents_scanned": result["documents_scanned"],
        "stakeholders_found": result["stakeholders_found"],
        "candidates_created": result["candidates_created"],
        "duplicates_found": result["duplicates_found"],
        "errors": result["errors"]
    }


@router.post("/", response_model=StakeholderResponse)
async def create_stakeholder(
    stakeholder: StakeholderCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new stakeholder."""
    data = {
        "client_id": current_user["client_id"],
        "name": stakeholder.name,
        "email": stakeholder.email,
        "phone": stakeholder.phone,
        "role": stakeholder.role,
        "department": stakeholder.department,
        "organization": stakeholder.organization,
        "notes": stakeholder.notes,
        "first_interaction": datetime.now(timezone.utc).date().isoformat()
    }

    result = supabase.table("stakeholders").insert(data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create stakeholder")

    return _format_stakeholder(result.data[0])


@router.get("/{stakeholder_id}", response_model=StakeholderResponse)
async def get_stakeholder(
    stakeholder_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific stakeholder."""
    result = supabase.table("stakeholders") \
        .select("*") \
        .eq("id", stakeholder_id) \
        .eq("client_id", current_user["client_id"]) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    return _format_stakeholder(result.data)


@router.patch("/{stakeholder_id}", response_model=StakeholderResponse)
async def update_stakeholder(
    stakeholder_id: str,
    update: StakeholderUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a stakeholder."""
    # Build update data, excluding None values
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = supabase.table("stakeholders") \
        .update(update_data) \
        .eq("id", stakeholder_id) \
        .eq("client_id", current_user["client_id"]) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    return _format_stakeholder(result.data[0])


@router.delete("/{stakeholder_id}")
async def delete_stakeholder(
    stakeholder_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a stakeholder."""
    result = supabase.table("stakeholders") \
        .delete() \
        .eq("id", stakeholder_id) \
        .eq("client_id", current_user["client_id"]) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    return {"message": "Stakeholder deleted successfully"}


@router.get("/{stakeholder_id}/engagement/history")
async def get_stakeholder_engagement_history(
    stakeholder_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get engagement level history for a specific stakeholder.

    Returns the history of engagement level calculations, including
    the signals that drove each calculation.

    Args:
        stakeholder_id: UUID of the stakeholder
        limit: Maximum records to return (default 20)

    Returns:
        List of engagement history records
    """
    # Verify stakeholder belongs to client
    stakeholder = supabase.table("stakeholders") \
        .select("id, name") \
        .eq("id", stakeholder_id) \
        .eq("client_id", current_user["client_id"]) \
        .single() \
        .execute()

    if not stakeholder.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Get engagement history
    result = supabase.table("engagement_level_history") \
        .select("engagement_level, previous_level, calculation_reason, signals, calculated_at, calculation_type") \
        .eq("stakeholder_id", stakeholder_id) \
        .order("calculated_at", desc=True) \
        .limit(limit) \
        .execute()

    return {
        "stakeholder_id": stakeholder_id,
        "stakeholder_name": stakeholder.data["name"],
        "history": [
            {
                "engagement_level": h["engagement_level"],
                "previous_level": h.get("previous_level"),
                "reason": h.get("calculation_reason"),
                "signals": h.get("signals", {}),
                "calculated_at": h["calculated_at"],
                "calculation_type": h.get("calculation_type", "scheduled")
            }
            for h in result.data
        ]
    }


@router.get("/{stakeholder_id}/insights", response_model=list[StakeholderInsightResponse])
async def get_stakeholder_insights(
    stakeholder_id: str,
    insight_type: Optional[str] = None,
    include_resolved: bool = False,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all insights for a stakeholder."""
    # Verify stakeholder belongs to client
    stakeholder = supabase.table("stakeholders") \
        .select("id") \
        .eq("id", stakeholder_id) \
        .eq("client_id", current_user["client_id"]) \
        .single() \
        .execute()

    if not stakeholder.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Get insights with meeting info
    query = supabase.table("stakeholder_insights") \
        .select("*, meeting_transcripts(title, meeting_date)") \
        .eq("stakeholder_id", stakeholder_id)

    if insight_type:
        query = query.eq("insight_type", insight_type)
    if not include_resolved:
        query = query.eq("is_resolved", False)

    result = query.order("created_at", desc=True).execute()

    return [
        StakeholderInsightResponse(
            id=i["id"],
            insight_type=i["insight_type"],
            content=i["content"],
            quote=i.get("extracted_quote"),
            confidence=i.get("confidence", 0.8),
            is_resolved=i.get("is_resolved", False),
            meeting_title=i["meeting_transcripts"]["title"] if i.get("meeting_transcripts") else None,
            meeting_date=i["meeting_transcripts"]["meeting_date"] if i.get("meeting_transcripts") else None,
            created_at=i["created_at"]
        )
        for i in result.data
    ]


@router.post("/{stakeholder_id}/insights/{insight_id}/resolve")
async def resolve_insight(
    stakeholder_id: str,
    insight_id: str,
    resolve: InsightResolve,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark an insight as resolved."""
    # Verify stakeholder belongs to client
    stakeholder = supabase.table("stakeholders") \
        .select("id") \
        .eq("id", stakeholder_id) \
        .eq("client_id", current_user["client_id"]) \
        .single() \
        .execute()

    if not stakeholder.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Update insight
    result = supabase.table("stakeholder_insights") \
        .update({
            "is_resolved": True,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolution_notes": resolve.resolution_notes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }) \
        .eq("id", insight_id) \
        .eq("stakeholder_id", stakeholder_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Insight not found")

    return {"message": "Insight resolved successfully"}


def _format_stakeholder(s: dict) -> StakeholderResponse:
    """Format a stakeholder record for response."""
    return StakeholderResponse(
        id=s["id"],
        name=s["name"],
        email=s.get("email"),
        phone=s.get("phone"),
        role=s.get("role"),
        department=s.get("department"),
        organization=s.get("organization", "Contentful"),
        sentiment_score=s.get("sentiment_score", 0),
        sentiment_trend=s.get("sentiment_trend", "stable"),
        engagement_level=s.get("engagement_level", "neutral"),
        alignment_score=s.get("alignment_score", 0.5),
        total_interactions=s.get("total_interactions", 0),
        last_interaction=s.get("last_interaction"),
        key_concerns=s.get("key_concerns", []),
        interests=s.get("interests", []),
        notes=s.get("notes"),
        created_at=s["created_at"],
        # Project-triage fields
        priority_level=s.get("priority_level", "tier_3"),
        ai_priorities=s.get("ai_priorities"),
        pain_points=s.get("pain_points"),
        win_conditions=s.get("win_conditions"),
        communication_style=s.get("communication_style"),
        relationship_status=s.get("relationship_status", "new"),
        open_questions=s.get("open_questions"),
        last_contact=s.get("last_contact"),
        reports_to_name=s.get("reports_to_name"),
        team_size=s.get("team_size"),
    )


def _format_candidate(c: dict) -> dict:
    """Format a stakeholder candidate record for response."""
    return {
        "id": c["id"],
        "name": c["name"],
        "role": c.get("role"),
        "department": c.get("department"),
        "organization": c.get("organization"),
        "email": c.get("email"),
        "key_concerns": c.get("key_concerns", []) or [],
        "interests": c.get("interests", []) or [],
        "initial_sentiment": c.get("initial_sentiment"),
        "influence_level": c.get("influence_level"),
        "source_document_id": c.get("source_document_id"),
        "source_document_name": c.get("source_document_name"),
        "source_text": c.get("source_text"),
        "extraction_context": c.get("extraction_context"),
        "related_opportunity_ids": c.get("related_opportunity_ids", []) or [],
        "related_task_ids": c.get("related_task_ids", []) or [],
        "status": c.get("status", "pending"),
        "confidence": c.get("confidence", "medium"),
        "potential_match_stakeholder_id": c.get("potential_match_stakeholder_id"),
        "potential_match_name": None,  # Will be populated by endpoint
        "match_confidence": c.get("match_confidence"),
        "created_at": c["created_at"]
    }
