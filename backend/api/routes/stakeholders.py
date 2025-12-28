"""
Stakeholders API Routes

Endpoints for managing stakeholders and their insights.
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
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
        created_at=s["created_at"]
    )
