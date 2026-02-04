"""Meeting Prep API Routes.

Endpoints for generating meeting preparation dashboards for stakeholders.
Aggregates status, metrics, opportunities, and questions into a single view.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meeting-prep", tags=["meeting-prep"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class StatusItem(BaseModel):
    """Single status indicator."""

    area: str
    status: str  # green, yellow, red
    notes: str


class MetricSummary(BaseModel):
    """Metric summary for meeting prep."""

    id: str
    metric_name: str
    current_value: Optional[str]
    target_value: Optional[str]
    validation_status: str
    unit: Optional[str]


class OpportunitySummary(BaseModel):
    """Opportunity summary for meeting prep."""

    id: str
    opportunity_code: str
    title: str
    total_score: int
    tier: int
    status: str
    next_step: Optional[str]
    role: str  # stakeholder's role in this opportunity


class MeetingPrepResponse(BaseModel):
    """Full meeting prep dashboard data."""

    stakeholder: dict
    status_summary: List[StatusItem]
    metrics: List[MetricSummary]
    opportunities: List[OpportunitySummary]
    questions_to_ask: List[str]
    recommended_approach: Optional[str]
    last_contact: Optional[str]
    days_since_contact: Optional[int]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _calculate_engagement_status(stakeholder: dict, insights_data: list) -> StatusItem:
    """Calculate engagement status based on stakeholder data."""
    engagement_level = stakeholder.get("engagement_level", "neutral")

    # Map engagement level to status color
    level_to_status = {
        "champion": "green",
        "supporter": "green",
        "neutral": "yellow",
        "skeptic": "red",
        "blocker": "red",
    }

    status = level_to_status.get(engagement_level, "yellow")

    # Count recent interactions
    total_interactions = stakeholder.get("total_interactions", 0)
    stakeholder.get("last_interaction")

    if total_interactions == 0:
        notes = "No interactions yet"
        status = "yellow"
    elif engagement_level == "champion":
        notes = f"Champion - {total_interactions} interactions"
    elif engagement_level == "supporter":
        notes = "Supporter - building relationship"
    elif engagement_level == "neutral":
        notes = "Neutral - needs more engagement"
    elif engagement_level == "skeptic":
        notes = "Skeptic - address concerns"
    else:
        notes = "Blocker - critical to resolve"

    return StatusItem(area="Engagement", status=status, notes=notes)


def _calculate_opportunity_clarity_status(opportunities: list) -> StatusItem:
    """Calculate opportunity clarity status."""
    if not opportunities:
        return StatusItem(area="Opportunity Clarity", status="yellow", notes="No opportunities identified yet")

    # Count by status
    active_count = sum(1 for o in opportunities if o.get("status") == "active")
    backlog_count = sum(1 for o in opportunities if o.get("status") == "backlog")
    archived_count = sum(1 for o in opportunities if o.get("status") == "archived")

    if archived_count > active_count:
        return StatusItem(
            area="Opportunity Clarity",
            status="red",
            notes=f"{archived_count} archived, {active_count} active",
        )
    elif backlog_count > active_count:
        return StatusItem(
            area="Opportunity Clarity",
            status="yellow",
            notes=f"{backlog_count} in backlog, {active_count} active",
        )
    else:
        return StatusItem(
            area="Opportunity Clarity",
            status="green",
            notes=f"{active_count} active",
        )


def _calculate_metrics_validation_status(metrics: list) -> StatusItem:
    """Calculate metrics validation status."""
    if not metrics:
        return StatusItem(area="Metrics Validated", status="red", notes="No metrics tracked yet")

    red_count = sum(1 for m in metrics if m.get("validation_status") == "red")
    yellow_count = sum(1 for m in metrics if m.get("validation_status") == "yellow")
    green_count = sum(1 for m in metrics if m.get("validation_status") == "green")

    total = len(metrics)
    validation_rate = green_count / total if total > 0 else 0

    if validation_rate >= 0.7:
        return StatusItem(area="Metrics Validated", status="green", notes=f"{green_count}/{total} validated")
    elif validation_rate >= 0.3:
        return StatusItem(
            area="Metrics Validated",
            status="yellow",
            notes=f"{red_count} unvalidated, {yellow_count} partial",
        )
    else:
        return StatusItem(area="Metrics Validated", status="red", notes=f"{red_count} need validation")


def _calculate_blockers_status(opportunities: list, insights: list) -> StatusItem:
    """Calculate blockers status from opportunities and unresolved concerns."""
    blocked_opps = [o for o in opportunities if o.get("status") == "blocked"]
    unresolved_concerns = [
        i for i in insights if i.get("insight_type") in ("concern", "objection") and not i.get("is_resolved")
    ]

    total_blockers = len(blocked_opps) + len(unresolved_concerns)

    if total_blockers == 0:
        return StatusItem(area="Blockers", status="green", notes="No active blockers")
    elif total_blockers <= 2:
        return StatusItem(
            area="Blockers",
            status="yellow",
            notes=f"{total_blockers} active ({len(blocked_opps)} opps, {len(unresolved_concerns)} concerns)",
        )
    else:
        return StatusItem(area="Blockers", status="red", notes=f"{total_blockers} blockers need resolution")


def _build_questions_list(stakeholder: dict, metrics: list, opportunities: list) -> List[str]:
    """Build prioritized list of questions to ask."""
    questions = []

    # Add stakeholder's open questions first
    open_questions = stakeholder.get("open_questions") or []
    questions.extend(open_questions)

    # Add questions from unvalidated metrics
    for metric in metrics:
        if metric.get("validation_status") in ("red", "yellow"):
            metric_questions = metric.get("questions_to_confirm") or []
            questions.extend(metric_questions)

    # Add questions from opportunities
    for opp in opportunities:
        follow_up = opp.get("follow_up_questions") or []
        questions.extend(follow_up)

    # Deduplicate while preserving order
    seen = set()
    unique_questions = []
    for q in questions:
        if q and q.lower() not in seen:
            seen.add(q.lower())
            unique_questions.append(q)

    return unique_questions[:20]  # Limit to 20 questions


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/{stakeholder_id}", response_model=MeetingPrepResponse)
async def get_meeting_prep(
    stakeholder_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Generate meeting prep dashboard for a stakeholder.

    Returns:
    - Status at a glance (engagement, opportunity clarity, metrics validation, blockers)
    - Key metrics with validation status
    - Active opportunities
    - Prioritized questions to ask
    - Recommended approach
    """
    # Get stakeholder
    stakeholder_result = (
        supabase.table("stakeholders")
        .select("*")
        .eq("id", stakeholder_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not stakeholder_result.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    stakeholder = stakeholder_result.data

    # Get stakeholder metrics
    metrics_result = (
        supabase.table("stakeholder_metrics")
        .select("*")
        .eq("stakeholder_id", stakeholder_id)
        .order("metric_category")
        .order("metric_name")
        .execute()
    )

    metrics = metrics_result.data

    # Get stakeholder opportunities (via link table)
    opp_links_result = (
        supabase.table("opportunity_stakeholder_link")
        .select("*, ai_projects(*)")
        .eq("stakeholder_id", stakeholder_id)
        .execute()
    )

    opportunities_with_role = []
    for link in opp_links_result.data:
        opp = link.get("ai_projects", {})
        if opp:
            opp["stakeholder_role"] = link.get("role", "involved")
            opportunities_with_role.append(opp)

    # Also get opportunities where stakeholder is owner
    owned_opps_result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("owner_stakeholder_id", stakeholder_id)
        .eq("client_id", current_user["client_id"])
        .execute()
    )

    # Merge owned opportunities (avoid duplicates)
    opp_ids = {o["id"] for o in opportunities_with_role}
    for opp in owned_opps_result.data:
        if opp["id"] not in opp_ids:
            opp["stakeholder_role"] = "owner"
            opportunities_with_role.append(opp)

    # Sort by score
    opportunities_with_role.sort(key=lambda x: x.get("total_score", 0), reverse=True)

    # Get stakeholder insights (for blockers calculation)
    insights_result = supabase.table("stakeholder_insights").select("*").eq("stakeholder_id", stakeholder_id).execute()

    insights = insights_result.data

    # Calculate status summary
    status_summary = [
        _calculate_engagement_status(stakeholder, insights),
        _calculate_opportunity_clarity_status(opportunities_with_role),
        _calculate_metrics_validation_status(metrics),
        _calculate_blockers_status(opportunities_with_role, insights),
    ]

    # Build questions list
    questions = _build_questions_list(stakeholder, metrics, opportunities_with_role)

    # Calculate days since contact
    days_since_contact = None
    last_contact = stakeholder.get("last_contact") or stakeholder.get("last_interaction")
    if last_contact:
        try:
            if isinstance(last_contact, str):
                # Parse the date string
                if "T" in last_contact:
                    contact_date = datetime.fromisoformat(last_contact.replace("Z", "+00:00"))
                else:
                    contact_date = datetime.strptime(last_contact, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                contact_date = last_contact

            days_since_contact = (datetime.now(timezone.utc) - contact_date).days
        except Exception as e:
            logger.warning(f"Could not parse last_contact date: {e}")

    # Format metrics for response
    metrics_summary = [
        MetricSummary(
            id=m["id"],
            metric_name=m["metric_name"],
            current_value=m.get("current_value"),
            target_value=m.get("target_value"),
            validation_status=m.get("validation_status", "red"),
            unit=m.get("unit"),
        )
        for m in metrics
    ]

    # Format opportunities for response
    opportunities_summary = [
        OpportunitySummary(
            id=o["id"],
            opportunity_code=o["opportunity_code"],
            title=o["title"],
            total_score=o.get("total_score", 0),
            tier=o.get("tier", 4),
            status=o.get("status", "backlog"),
            next_step=o.get("next_step"),
            role=o.get("stakeholder_role", "involved"),
        )
        for o in opportunities_with_role
    ]

    # Format stakeholder data
    stakeholder_data = {
        "id": stakeholder["id"],
        "name": stakeholder["name"],
        "email": stakeholder.get("email"),
        "role": stakeholder.get("role"),
        "department": stakeholder.get("department"),
        "organization": stakeholder.get("organization"),
        "priority_level": stakeholder.get("priority_level", "tier_3"),
        "engagement_level": stakeholder.get("engagement_level", "neutral"),
        "relationship_status": stakeholder.get("relationship_status", "new"),
        "sentiment_score": stakeholder.get("sentiment_score", 0),
        "ai_priorities": stakeholder.get("ai_priorities") or [],
        "pain_points": stakeholder.get("pain_points") or [],
        "win_conditions": stakeholder.get("win_conditions") or [],
    }

    return MeetingPrepResponse(
        stakeholder=stakeholder_data,
        status_summary=status_summary,
        metrics=metrics_summary,
        opportunities=opportunities_summary,
        questions_to_ask=questions,
        recommended_approach=stakeholder.get("communication_style"),
        last_contact=str(last_contact) if last_contact else None,
        days_since_contact=days_since_contact,
    )


@router.get("/")
async def list_meeting_prep_summaries(
    priority_level: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get quick meeting prep summaries for multiple stakeholders.

    Useful for seeing which stakeholders need attention.
    """
    query = (
        supabase.table("stakeholders")
        .select(
            "id, name, department, role, priority_level, engagement_level, relationship_status, last_contact, last_interaction"
        )
        .eq("client_id", current_user["client_id"])
    )

    if priority_level:
        query = query.eq("priority_level", priority_level)
    if department:
        query = query.eq("department", department)

    result = query.order("priority_level").order("name").limit(limit).execute()

    summaries = []
    for s in result.data:
        # Calculate days since contact
        days_since = None
        last_contact = s.get("last_contact") or s.get("last_interaction")
        if last_contact:
            try:
                if isinstance(last_contact, str):
                    if "T" in last_contact:
                        contact_date = datetime.fromisoformat(last_contact.replace("Z", "+00:00"))
                    else:
                        contact_date = datetime.strptime(last_contact, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    contact_date = last_contact
                days_since = (datetime.now(timezone.utc) - contact_date).days
            except Exception:
                pass

        summaries.append(
            {
                "stakeholder_id": s["id"],
                "name": s["name"],
                "department": s.get("department"),
                "role": s.get("role"),
                "priority_level": s.get("priority_level", "tier_3"),
                "engagement_level": s.get("engagement_level", "neutral"),
                "relationship_status": s.get("relationship_status", "new"),
                "days_since_contact": days_since,
                "needs_attention": days_since is None or days_since > 14,
            }
        )

    # Sort by needs_attention and priority
    summaries.sort(
        key=lambda x: (
            not x["needs_attention"],  # needs_attention first
            {"tier_1": 0, "tier_2": 1, "tier_3": 2}.get(x["priority_level"], 3),
        )
    )

    return {
        "stakeholders": summaries,
        "summary": {
            "total": len(summaries),
            "needs_attention": sum(1 for s in summaries if s["needs_attention"]),
            "tier_1": sum(1 for s in summaries if s["priority_level"] == "tier_1"),
        },
    }


@router.post("/{stakeholder_id}/mark-contacted")
async def mark_stakeholder_contacted(
    stakeholder_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Mark a stakeholder as contacted today.

    Updates last_contact date to today.
    """
    # Verify ownership
    existing = (
        supabase.table("stakeholders")
        .select("id")
        .eq("id", stakeholder_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    today = datetime.now(timezone.utc).date()

    supabase.table("stakeholders").update({"last_contact": str(today)}).eq("id", stakeholder_id).execute()

    return {"message": "Contact date updated", "last_contact": str(today)}
