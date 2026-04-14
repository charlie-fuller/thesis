"""Stakeholders API Routes.

Endpoints for managing stakeholders, their insights, and stakeholder candidates.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import anthropic
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

import pb_client as pb
from repositories.stakeholders import (
    list_stakeholders as repo_list_stakeholders,
    get_stakeholder as repo_get_stakeholder,
    create_stakeholder as repo_create_stakeholder,
    update_stakeholder as repo_update_stakeholder,
    delete_stakeholder as repo_delete_stakeholder,
    list_stakeholder_candidates as repo_list_stakeholder_candidates,
    get_stakeholder_candidate,
    update_stakeholder_candidate,
    list_stakeholder_insights,
    create_stakeholder_insight,
    update_stakeholder_insight,
)

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
):
    """List all stakeholders."""
    parts = []
    if department:
        parts.append(f"department='{pb.escape_filter(department)}'")
    if engagement_level:
        parts.append(f"engagement_level='{pb.escape_filter(engagement_level)}'")
    filter_str = " && ".join(parts)

    page = (offset // limit) + 1 if limit else 1
    result = pb.list_records(
        "stakeholders",
        filter=filter_str,
        sort="name",
        page=page,
        per_page=limit,
    )

    return [_format_stakeholder(s) for s in result.get("items", [])]


# ============================================================================
# ENGAGEMENT ANALYTICS ENDPOINTS
# ============================================================================
# NOTE: Static routes must be defined before parameterized routes (/{stakeholder_id})


@router.get("/engagement/trends")
async def get_engagement_trends(
    days: int = 90,
):
    """Get engagement level distribution over time for trend analytics.

    Returns data suitable for a stacked area chart showing how engagement
    levels have changed over time.

    Args:
        days: Number of days to look back (default 90)

    Returns:
        List of weekly snapshots with counts per engagement level
    """
    from datetime import timedelta

    # Calculate start date
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get engagement history for the period
    history = pb.get_all(
        "engagement_level_history",
        filter=f"calculated_at>='{start_date.isoformat()}'",
        sort="calculated_at",
    )

    if not history:
        return []

    # Group by week and count engagement levels
    from collections import defaultdict

    weekly_data = defaultdict(lambda: {"champion": 0, "supporter": 0, "neutral": 0, "skeptic": 0, "blocker": 0})

    for record in history:
        # Get week start (Monday)
        calc_date = datetime.fromisoformat(record["calculated_at"].replace("Z", "+00:00"))
        week_start = calc_date - timedelta(days=calc_date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        level = record["engagement_level"].lower()
        if level in weekly_data[week_key]:
            weekly_data[week_key][level] += 1

    # Convert to sorted list
    trends = [{"date": date, **counts} for date, counts in sorted(weekly_data.items())]

    return trends


@router.get("/engagement/changes")
async def get_engagement_changes(
    days: int = 30,
):
    """Get recent engagement level changes (who moved up/down).

    Returns stakeholders whose engagement level changed recently,
    with direction indicators.

    Args:
        days: Number of days to look back (default 30)

    Returns:
        List of engagement changes with stakeholder info
    """
    from datetime import timedelta

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get history records where level changed (previous_level is not null/empty)
    all_history = pb.get_all(
        "engagement_level_history",
        filter=f"calculated_at>='{start_date.isoformat()}' && previous_level!=''",
        sort="-calculated_at",
    )

    # Limit to 50
    history = all_history[:50]

    if not history:
        return []

    # Get stakeholder names
    stakeholder_ids = list({r["stakeholder_id"] for r in history})
    name_map = {}
    for sid in stakeholder_ids:
        s = pb.get_record("stakeholders", sid)
        if s:
            name_map[sid] = s.get("name", "Unknown")

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
    for record in history:
        changes.append(
            {
                "stakeholder_id": record["stakeholder_id"],
                "name": name_map.get(record["stakeholder_id"], "Unknown"),
                "previous_level": record["previous_level"],
                "new_level": record["engagement_level"],
                "direction": get_direction(record["previous_level"], record["engagement_level"]),
                "change_date": record["calculated_at"],
                "reason": record.get("calculation_reason"),
            }
        )

    return changes


@router.post("/engagement/recalculate")
async def trigger_engagement_recalculation():
    """Manually trigger engagement recalculation.

    This is an admin function for testing or forcing an immediate update.
    """
    from services.engagement_scheduler import trigger_manual_calculation

    try:
        result = await trigger_manual_calculation()
        return {
            "message": "Engagement recalculation completed",
            "total": result.get("total", 0),
            "changed": result.get("changed", 0),
            "promotions": result.get("promotions", 0),
            "demotions": result.get("demotions", 0),
            "errors": result.get("errors", 0),
        }
    except Exception as e:
        logger.error(f"Engagement recalculation failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/dashboard")
async def get_stakeholder_dashboard():
    """Get dashboard metrics for stakeholders.

    Returns:
    - Sentiment trends
    - Engagement distribution
    - Recent concerns
    - Alignment scores
    """
    # Get all stakeholders
    stakeholders_data = pb.get_all("stakeholders", sort="name")

    # Get recent unresolved concerns (without join -- separate lookups)
    concerns = pb.get_all(
        "stakeholder_insights",
        filter="insight_type='concern' && is_resolved=false",
        sort="-created",
    )
    # Limit to 10
    concerns = concerns[:10]

    # Calculate metrics
    total = len(stakeholders_data)
    if total == 0:
        return {
            "total_stakeholders": 0,
            "engagement_distribution": {},
            "average_sentiment": 0,
            "average_alignment": 0,
            "recent_concerns": [],
            "stakeholders_needing_attention": [],
        }

    # Engagement distribution
    engagement_dist = {}
    for s in stakeholders_data:
        level = s.get("engagement_level", "neutral")
        engagement_dist[level] = engagement_dist.get(level, 0) + 1

    # Average scores
    avg_sentiment = sum(s.get("sentiment_score", 0) for s in stakeholders_data) / total
    avg_alignment = sum(s.get("alignment_score", 0.5) for s in stakeholders_data) / total

    # Stakeholders needing attention (negative sentiment or low engagement)
    needs_attention = [
        _format_stakeholder(s)
        for s in stakeholders_data
        if s.get("sentiment_score", 0) < -0.2 or s.get("engagement_level") in ["skeptic", "blocker"]
    ]

    # Build concern entries with stakeholder names
    recent_concerns = []
    for c in concerns:
        stakeholder_name = "Unknown"
        if c.get("stakeholder_id"):
            stakeholder = pb.get_record("stakeholders", c["stakeholder_id"])
            if stakeholder:
                stakeholder_name = stakeholder.get("name", "Unknown")
        recent_concerns.append(
            {
                "id": c["id"],
                "stakeholder_name": stakeholder_name,
                "content": c["content"],
                "created_at": c.get("created", ""),
            }
        )

    return {
        "total_stakeholders": total,
        "engagement_distribution": engagement_dist,
        "average_sentiment": round(avg_sentiment, 2),
        "average_alignment": round(avg_alignment, 2),
        "recent_concerns": recent_concerns,
        "stakeholders_needing_attention": needs_attention[:5],
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
):
    """List stakeholder candidates for review."""
    candidates = repo_list_stakeholder_candidates(status=status or "pending", limit=limit)

    # Get potential match names
    candidates_with_matches = []
    for c in candidates:
        formatted = _format_candidate(c)

        # Get match name if there's a potential match
        if c.get("potential_match_stakeholder_id"):
            match = pb.get_record("stakeholders", c["potential_match_stakeholder_id"])
            if match:
                formatted["potential_match_name"] = match.get("name")

        candidates_with_matches.append(formatted)

    return candidates_with_matches


@router.get("/candidates/count")
async def get_candidate_count():
    """Get count of pending stakeholder candidates."""
    count = pb.count("stakeholder_candidates", filter="status='pending'")
    return {"count": count}


@router.post("/candidates/{candidate_id}/accept", response_model=StakeholderResponse)
async def accept_stakeholder_candidate(
    candidate_id: str,
    accept: CandidateAccept = CandidateAccept(),
):
    """Accept a stakeholder candidate and create the stakeholder."""
    # Get the candidate
    c = get_stakeholder_candidate(candidate_id)
    if not c or c.get("status") != "pending":
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    # Create the stakeholder (use overrides if provided)
    stakeholder_data = {
        "name": accept.name or c["name"],
        "email": accept.email or c.get("email"),
        "role": accept.role or c.get("role"),
        "department": accept.department or c.get("department"),
        "organization": accept.organization or c.get("organization") or "Contentful",
        "key_concerns": c.get("key_concerns", []),
        "interests": c.get("interests", []),
        "notes": accept.notes,
        "first_interaction": datetime.now(timezone.utc).date().isoformat(),
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
    new_stakeholder = repo_create_stakeholder(stakeholder_data)

    # Update candidate status
    update_stakeholder_candidate(
        candidate_id,
        {
            "status": "accepted",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "created_stakeholder_id": new_stakeholder["id"],
        },
    )

    return _format_stakeholder(new_stakeholder)


@router.post("/candidates/{candidate_id}/reject")
async def reject_stakeholder_candidate(
    candidate_id: str,
    reject: CandidateReject = CandidateReject(),
):
    """Reject a stakeholder candidate."""
    c = get_stakeholder_candidate(candidate_id)
    if not c or c.get("status") != "pending":
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    update_stakeholder_candidate(
        candidate_id,
        {
            "status": "rejected",
            "rejection_reason": reject.reason,
        },
    )

    return {"message": "Candidate rejected"}


@router.post("/candidates/{candidate_id}/merge")
async def merge_stakeholder_candidate(
    candidate_id: str,
    merge: CandidateMerge,
):
    """Merge a candidate into an existing stakeholder."""
    # Get the candidate
    c = get_stakeholder_candidate(candidate_id)
    if not c or c.get("status") != "pending":
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    # Get the target stakeholder
    t = repo_get_stakeholder(merge.target_stakeholder_id)
    if not t:
        raise HTTPException(status_code=404, detail="Target stakeholder not found")

    # Build update data
    update_data = {}

    # Merge concerns if requested
    if merge.update_concerns and c.get("key_concerns"):
        existing_concerns = t.get("key_concerns", []) or []
        new_concerns = c.get("key_concerns", [])
        for concern in new_concerns:
            if concern not in existing_concerns:
                existing_concerns.append(concern)
        update_data["key_concerns"] = existing_concerns

    # Merge interests if requested
    if merge.update_interests and c.get("interests"):
        existing_interests = t.get("interests", []) or []
        new_interests = c.get("interests", [])
        for interest in new_interests:
            if interest not in existing_interests:
                existing_interests.append(interest)
        update_data["interests"] = existing_interests

    # Update target stakeholder
    if update_data:
        repo_update_stakeholder(merge.target_stakeholder_id, update_data)

    # Update candidate status
    update_stakeholder_candidate(
        candidate_id,
        {
            "status": "merged",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "merged_into_stakeholder_id": merge.target_stakeholder_id,
        },
    )

    return {"message": "Candidate merged into existing stakeholder"}


@router.post("/candidates/bulk")
async def bulk_process_candidates(
    candidate_ids: list[str],
    action: str,
):
    """Bulk accept or reject candidates."""
    if action not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")

    results = {"processed": 0, "errors": []}

    for candidate_id in candidate_ids:
        try:
            if action == "accept":
                await accept_stakeholder_candidate(candidate_id, CandidateAccept())
            else:
                await reject_stakeholder_candidate(candidate_id, CandidateReject())
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
):
    """Manually trigger stakeholder extraction from meeting documents.

    Scans meeting summaries and transcripts for stakeholder mentions,
    creates candidates for review.
    """
    from services.stakeholder_scanner import StakeholderScanner

    # Create Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    anthropic_client = anthropic.Anthropic(api_key=api_key)

    # NOTE: StakeholderScanner will be rewritten later; passing None for supabase
    scanner = StakeholderScanner(None, anthropic_client)

    # Run scan
    result = await scanner.scan_documents(
        force_rescan=request.force_rescan,
        since_days=request.since_days,
        limit=request.limit,
    )

    return {
        "message": "Stakeholder scan completed",
        "documents_scanned": result["documents_scanned"],
        "stakeholders_found": result["stakeholders_found"],
        "candidates_created": result["candidates_created"],
        "duplicates_found": result["duplicates_found"],
        "errors": result["errors"],
    }


@router.post("/", response_model=StakeholderResponse)
async def create_stakeholder(
    stakeholder: StakeholderCreate,
):
    """Create a new stakeholder."""
    data = {
        "name": stakeholder.name,
        "email": stakeholder.email,
        "phone": stakeholder.phone,
        "role": stakeholder.role,
        "department": stakeholder.department,
        "organization": stakeholder.organization,
        "notes": stakeholder.notes,
        "first_interaction": datetime.now(timezone.utc).date().isoformat(),
    }

    result = repo_create_stakeholder(data)

    return _format_stakeholder(result)


@router.get("/{stakeholder_id}", response_model=StakeholderResponse)
async def get_stakeholder(
    stakeholder_id: str,
):
    """Get a specific stakeholder."""
    result = repo_get_stakeholder(stakeholder_id)

    if not result:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    return _format_stakeholder(result)


@router.patch("/{stakeholder_id}", response_model=StakeholderResponse)
async def update_stakeholder(
    stakeholder_id: str,
    update: StakeholderUpdate,
):
    """Update a stakeholder."""
    # Build update data, excluding None values
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    existing = repo_get_stakeholder(stakeholder_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    result = repo_update_stakeholder(stakeholder_id, update_data)

    return _format_stakeholder(result)


@router.delete("/{stakeholder_id}")
async def delete_stakeholder(
    stakeholder_id: str,
):
    """Delete a stakeholder."""
    existing = repo_get_stakeholder(stakeholder_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    repo_delete_stakeholder(stakeholder_id)

    return {"message": "Stakeholder deleted successfully"}


@router.get("/{stakeholder_id}/engagement/history")
async def get_stakeholder_engagement_history(
    stakeholder_id: str,
    limit: int = 20,
):
    """Get engagement level history for a specific stakeholder.

    Returns the history of engagement level calculations, including
    the signals that drove each calculation.

    Args:
        stakeholder_id: UUID of the stakeholder
        limit: Maximum records to return (default 20)

    Returns:
        List of engagement history records
    """
    # Verify stakeholder exists
    stakeholder = repo_get_stakeholder(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Get engagement history
    result = pb.list_records(
        "engagement_level_history",
        filter=f"stakeholder_id='{pb.escape_filter(stakeholder_id)}'",
        sort="-calculated_at",
        per_page=limit,
    )
    history = result.get("items", [])

    return {
        "stakeholder_id": stakeholder_id,
        "stakeholder_name": stakeholder["name"],
        "history": [
            {
                "engagement_level": h["engagement_level"],
                "previous_level": h.get("previous_level"),
                "reason": h.get("calculation_reason"),
                "signals": h.get("signals", {}),
                "calculated_at": h["calculated_at"],
                "calculation_type": h.get("calculation_type", "scheduled"),
            }
            for h in history
        ],
    }


@router.get("/{stakeholder_id}/insights", response_model=list[StakeholderInsightResponse])
async def get_stakeholder_insights(
    stakeholder_id: str,
    insight_type: Optional[str] = None,
    include_resolved: bool = False,
):
    """Get all insights for a stakeholder."""
    # Verify stakeholder exists
    stakeholder = repo_get_stakeholder(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Get insights
    all_insights = list_stakeholder_insights(stakeholder_id)

    # Apply filters
    if insight_type:
        all_insights = [i for i in all_insights if i.get("insight_type") == insight_type]
    if not include_resolved:
        all_insights = [i for i in all_insights if not i.get("is_resolved", False)]

    # Build response with meeting transcript info (separate lookup)
    result = []
    for i in all_insights:
        meeting_title = None
        meeting_date = None
        if i.get("meeting_transcript_id"):
            transcript = pb.get_record("meeting_transcripts", i["meeting_transcript_id"])
            if transcript:
                meeting_title = transcript.get("title")
                meeting_date = transcript.get("meeting_date")

        result.append(
            StakeholderInsightResponse(
                id=i["id"],
                insight_type=i["insight_type"],
                content=i["content"],
                quote=i.get("extracted_quote"),
                confidence=i.get("confidence", 0.8),
                is_resolved=i.get("is_resolved", False),
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                created_at=i.get("created", ""),
            )
        )

    return result


@router.post("/{stakeholder_id}/insights/{insight_id}/resolve")
async def resolve_insight(
    stakeholder_id: str,
    insight_id: str,
    resolve: InsightResolve,
):
    """Mark an insight as resolved."""
    # Verify stakeholder exists
    stakeholder = repo_get_stakeholder(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Verify insight exists
    insight = pb.get_record("stakeholder_insights", insight_id)
    if not insight or insight.get("stakeholder_id") != stakeholder_id:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Update insight
    update_stakeholder_insight(
        insight_id,
        {
            "is_resolved": True,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolution_notes": resolve.resolution_notes,
        },
    )

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
        created_at=s.get("created", s.get("created_at", "")),
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
        "created_at": c.get("created", c.get("created_at", "")),
    }
