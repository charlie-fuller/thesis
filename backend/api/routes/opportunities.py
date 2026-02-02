"""Opportunities API Routes.

Endpoints for managing AI implementation opportunities with 4-dimension scoring.
Supports filtering by tier, department, status, and stakeholder.

Added in v2: Related documents, conversations, and Q&A endpoints for detail modal.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import get_current_user
from database import get_supabase
from services.goal_alignment_analyzer import (
    analyze_goal_alignment,
    batch_analyze_all,
)
from services.project_chat import ask_about_project, get_project_conversations
from services.project_context import get_scoring_related_documents
from services.project_justification import (
    generate_all_justifications,
    generate_project_justifications,
    regenerate_if_scores_changed,
)
from services.project_taskmaster import chat_with_taskmaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class OpportunityCreate(BaseModel):
    """Create a new opportunity."""

    opportunity_code: str = Field(
        ..., min_length=2, max_length=10, description="Short code like F01, L02"
    )
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    department: Optional[str] = None
    owner_stakeholder_id: Optional[str] = None
    current_state: Optional[str] = None
    desired_state: Optional[str] = None
    roi_potential: Optional[int] = Field(None, ge=1, le=5)
    implementation_effort: Optional[int] = Field(None, ge=1, le=5)
    strategic_alignment: Optional[int] = Field(None, ge=1, le=5)
    stakeholder_readiness: Optional[int] = Field(None, ge=1, le=5)
    status: str = "identified"
    next_step: Optional[str] = None
    blockers: List[str] = []
    follow_up_questions: List[str] = []
    roi_indicators: dict = {}
    source_type: Optional[str] = None
    source_notes: Optional[str] = None
    scoring_confidence: Optional[int] = Field(
        None, ge=0, le=100, description="Confidence in scoring (0-100)"
    )
    confidence_questions: List[str] = Field(
        default=[], description="Questions that would raise confidence"
    )


class OpportunityUpdate(BaseModel):
    """Update an opportunity."""

    opportunity_code: Optional[str] = Field(None, min_length=2, max_length=10)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    department: Optional[str] = None
    owner_stakeholder_id: Optional[str] = None
    current_state: Optional[str] = None
    desired_state: Optional[str] = None
    roi_potential: Optional[int] = Field(None, ge=1, le=5)
    implementation_effort: Optional[int] = Field(None, ge=1, le=5)
    strategic_alignment: Optional[int] = Field(None, ge=1, le=5)
    stakeholder_readiness: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None
    next_step: Optional[str] = None
    blockers: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None
    roi_indicators: Optional[dict] = None
    source_type: Optional[str] = None
    source_notes: Optional[str] = None
    scoring_confidence: Optional[int] = Field(None, ge=0, le=100)
    confidence_questions: Optional[List[str]] = None


class OpportunityScoreUpdate(BaseModel):
    """Update just the scores for an opportunity."""

    roi_potential: Optional[int] = Field(None, ge=1, le=5)
    implementation_effort: Optional[int] = Field(None, ge=1, le=5)
    strategic_alignment: Optional[int] = Field(None, ge=1, le=5)
    stakeholder_readiness: Optional[int] = Field(None, ge=1, le=5)


class OpportunityResponse(BaseModel):
    """Opportunity response model."""

    id: str
    opportunity_code: str
    title: str
    description: Optional[str]
    department: Optional[str]
    owner_stakeholder_id: Optional[str]
    owner_name: Optional[str] = None  # Joined from stakeholders
    current_state: Optional[str]
    desired_state: Optional[str]
    roi_potential: Optional[int]
    implementation_effort: Optional[int]
    strategic_alignment: Optional[int]
    stakeholder_readiness: Optional[int]
    total_score: int
    tier: int
    status: str
    next_step: Optional[str]
    blockers: List[str]
    follow_up_questions: List[str]
    roi_indicators: dict
    source_type: Optional[str]
    source_notes: Optional[str]
    created_at: str
    updated_at: str
    # Project fields (for scoping/pilot phase)
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    # Justification fields
    opportunity_summary: Optional[str] = None
    roi_justification: Optional[str] = None
    effort_justification: Optional[str] = None
    alignment_justification: Optional[str] = None
    readiness_justification: Optional[str] = None
    # Scoring confidence fields
    scoring_confidence: Optional[int] = None  # 0-100 percentage
    confidence_questions: List[str] = []  # Questions that would raise confidence
    # Goal alignment fields
    goal_alignment_score: Optional[int] = None  # 0-100 alignment with IS strategic goals
    goal_alignment_details: Optional[dict] = None  # Pillar scores, KPI impacts, summary


class StakeholderLinkCreate(BaseModel):
    """Link a stakeholder to an opportunity."""

    stakeholder_id: str
    role: str = "involved"  # owner, champion, involved, blocker, approver
    notes: Optional[str] = None


class StakeholderLinkResponse(BaseModel):
    """Stakeholder link response."""

    id: str
    opportunity_id: str
    stakeholder_id: str
    stakeholder_name: str
    stakeholder_role: Optional[str]
    stakeholder_department: Optional[str]
    role: str
    notes: Optional[str]
    created_at: str


# ============================================================================
# DOCUMENT & CHAT MODELS (for detail modal)
# ============================================================================


class RelatedDocumentMetadata(BaseModel):
    """Metadata for a related document."""

    filename: Optional[str] = None
    page_number: Optional[int] = None
    source_type: Optional[str] = None
    storage_path: Optional[str] = None


class RelatedDocumentResponse(BaseModel):
    """A document related to an opportunity (for scoring justification)."""

    chunk_id: str
    document_id: str
    document_name: str
    relevance_score: float
    snippet: str
    metadata: RelatedDocumentMetadata


class AskQuestionRequest(BaseModel):
    """Request to ask a question about an opportunity."""

    question: str = Field(..., min_length=1, max_length=1000)


class AskQuestionResponse(BaseModel):
    """Response to a question about an opportunity."""

    response: str
    sources: List[RelatedDocumentResponse]


class ConversationResponse(BaseModel):
    """A Q&A conversation entry for an opportunity."""

    id: str
    question: str
    response: str
    source_documents: List[dict]
    created_at: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _format_opportunity(opp: dict, owner_name: Optional[str] = None) -> dict:
    """Format opportunity for response."""
    return {
        "id": opp["id"],
        "opportunity_code": opp["opportunity_code"],
        "title": opp["title"],
        "description": opp.get("description"),
        "department": opp.get("department"),
        "owner_stakeholder_id": opp.get("owner_stakeholder_id"),
        "owner_name": owner_name,
        "current_state": opp.get("current_state"),
        "desired_state": opp.get("desired_state"),
        "roi_potential": opp.get("roi_potential"),
        "implementation_effort": opp.get("implementation_effort"),
        "strategic_alignment": opp.get("strategic_alignment"),
        "stakeholder_readiness": opp.get("stakeholder_readiness"),
        "total_score": opp.get("total_score", 0),
        "tier": opp.get("tier", 4),
        "status": opp.get("status", "identified"),
        "next_step": opp.get("next_step"),
        "blockers": opp.get("blockers") or [],
        "follow_up_questions": opp.get("follow_up_questions") or [],
        "roi_indicators": opp.get("roi_indicators") or {},
        "source_type": opp.get("source_type"),
        "source_notes": opp.get("source_notes"),
        "created_at": opp["created_at"],
        "updated_at": opp.get("updated_at", opp["created_at"]),
        # Project fields
        "project_name": opp.get("project_name"),
        "project_description": opp.get("project_description"),
        # Justification fields
        "opportunity_summary": opp.get("opportunity_summary"),
        "roi_justification": opp.get("roi_justification"),
        "effort_justification": opp.get("effort_justification"),
        "alignment_justification": opp.get("alignment_justification"),
        "readiness_justification": opp.get("readiness_justification"),
        # Scoring confidence fields
        "scoring_confidence": opp.get("scoring_confidence"),
        "confidence_questions": opp.get("confidence_questions") or [],
        # Goal alignment fields
        "goal_alignment_score": opp.get("goal_alignment_score"),
        "goal_alignment_details": opp.get("goal_alignment_details"),
    }


async def _get_owner_names(supabase, opportunity_ids: List[str]) -> dict:
    """Get owner names for a list of opportunities."""
    if not opportunity_ids:
        return {}

    # Get opportunities with owner IDs
    result = (
        supabase.table("ai_projects")
        .select("id, owner_stakeholder_id")
        .in_("id", opportunity_ids)
        .execute()
    )

    owner_ids = [o["owner_stakeholder_id"] for o in result.data if o.get("owner_stakeholder_id")]

    if not owner_ids:
        return {}

    # Get stakeholder names
    stakeholders = supabase.table("stakeholders").select("id, name").in_("id", owner_ids).execute()

    stakeholder_map = {s["id"]: s["name"] for s in stakeholders.data}

    # Map opportunity ID to owner name
    return {
        o["id"]: stakeholder_map.get(o["owner_stakeholder_id"])
        for o in result.data
        if o.get("owner_stakeholder_id")
    }


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================


@router.get("/", response_model=List[OpportunityResponse])
async def list_opportunities(
    department: Optional[str] = None,
    tier: Optional[int] = Query(None, ge=1, le=4),
    status: Optional[str] = None,
    owner_stakeholder_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List all opportunities for the current client.

    Supports filtering by department, tier, status, and owner.
    """
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])

    if department:
        query = query.eq("department", department)
    if tier:
        query = query.eq("tier", tier)
    if status:
        query = query.eq("status", status)
    if owner_stakeholder_id:
        query = query.eq("owner_stakeholder_id", owner_stakeholder_id)

    result = query.order("total_score", desc=True).range(offset, offset + limit - 1).execute()

    # Get owner names
    opp_ids = [o["id"] for o in result.data]
    owner_names = await _get_owner_names(supabase, opp_ids)

    return [_format_opportunity(o, owner_names.get(o["id"])) for o in result.data]


@router.get("/by-tier")
async def get_opportunities_by_tier(
    department: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get opportunities grouped by tier.

    Returns a dict with tier keys (1-4) and lists of opportunities.
    """
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])

    if department:
        query = query.eq("department", department)
    if status:
        query = query.eq("status", status)

    result = query.order("total_score", desc=True).execute()

    # Get owner names
    opp_ids = [o["id"] for o in result.data]
    owner_names = await _get_owner_names(supabase, opp_ids)

    # Group by tier
    grouped = {1: [], 2: [], 3: [], 4: []}
    for opp in result.data:
        tier = opp.get("tier", 4)
        grouped[tier].append(_format_opportunity(opp, owner_names.get(opp["id"])))

    return {
        "tier_1": grouped[1],
        "tier_2": grouped[2],
        "tier_3": grouped[3],
        "tier_4": grouped[4],
        "summary": {
            "tier_1_count": len(grouped[1]),
            "tier_2_count": len(grouped[2]),
            "tier_3_count": len(grouped[3]),
            "tier_4_count": len(grouped[4]),
            "total": len(result.data),
        },
    }


@router.get("/by-department")
async def get_opportunities_by_department(
    tier: Optional[int] = Query(None, ge=1, le=4),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get opportunities grouped by department."""
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])

    if tier:
        query = query.eq("tier", tier)
    if status:
        query = query.eq("status", status)

    result = query.order("total_score", desc=True).execute()

    # Get owner names
    opp_ids = [o["id"] for o in result.data]
    owner_names = await _get_owner_names(supabase, opp_ids)

    # Group by department
    grouped = {}
    for opp in result.data:
        dept = opp.get("department") or "unassigned"
        if dept not in grouped:
            grouped[dept] = []
        grouped[dept].append(_format_opportunity(opp, owner_names.get(opp["id"])))

    return {"departments": grouped, "summary": {dept: len(opps) for dept, opps in grouped.items()}}


@router.get("/top")
async def get_top_opportunities(
    limit: int = Query(10, ge=1, le=50),
    exclude_status: Optional[str] = "completed",
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get top opportunities by score.

    Excludes completed opportunities by default.
    """
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])

    if exclude_status:
        query = query.neq("status", exclude_status)

    result = query.order("total_score", desc=True).limit(limit).execute()

    # Get owner names
    opp_ids = [o["id"] for o in result.data]
    owner_names = await _get_owner_names(supabase, opp_ids)

    return [_format_opportunity(o, owner_names.get(o["id"])) for o in result.data]


@router.get("/blocked")
async def get_blocked_opportunities(
    current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get all blocked opportunities."""
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("client_id", current_user["client_id"])
        .eq("status", "blocked")
        .order("total_score", desc=True)
        .execute()
    )

    # Get owner names
    opp_ids = [o["id"] for o in result.data]
    owner_names = await _get_owner_names(supabase, opp_ids)

    return [_format_opportunity(o, owner_names.get(o["id"])) for o in result.data]


@router.get("/summary")
async def get_opportunities_summary(
    current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get a summary of all opportunities.

    Returns counts by tier, status, and department.
    """
    result = (
        supabase.table("ai_projects")
        .select("tier, status, department")
        .eq("client_id", current_user["client_id"])
        .execute()
    )

    # Count by tier
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    status_counts = {}
    dept_counts = {}

    for opp in result.data:
        # Tier
        tier = opp.get("tier", 4)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Status
        status = opp.get("status", "identified")
        status_counts[status] = status_counts.get(status, 0) + 1

        # Department
        dept = opp.get("department") or "unassigned"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    return {
        "total": len(result.data),
        "by_tier": tier_counts,
        "by_status": status_counts,
        "by_department": dept_counts,
    }


# ============================================================================
# DOCUMENT & CHAT ENDPOINTS (for detail modal)
# ============================================================================
# NOTE: These must be defined BEFORE /{opportunity_id} to avoid routing conflicts


@router.get("/{opportunity_id}/related-documents", response_model=List[RelatedDocumentResponse])
async def get_opportunity_related_documents(
    opportunity_id: str,
    limit: int = Query(8, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get documents related to an opportunity's scoring.

    Performs vector search using the opportunity's context (title, description,
    current/desired state, ROI indicators) to find knowledge base documents
    that support or explain the scoring rationale.

    Documents are sorted by relevance score (highest first).
    """
    # Fetch the full opportunity
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Get scoring-relevant documents
    related_docs = get_scoring_related_documents(
        opportunity=result.data,
        client_id=current_user["client_id"],
        limit=limit,
        min_similarity=0.25,
    )

    return related_docs


@router.get("/{opportunity_id}/conversations", response_model=List[ConversationResponse])
async def get_opportunity_conversation_history(
    opportunity_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get Q&A conversation history for an opportunity.

    Returns conversations newest first.
    """
    # Verify opportunity exists and belongs to client
    opp = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Get conversations
    conversations = await get_project_conversations(
        opportunity_id=opportunity_id,
        client_id=current_user["client_id"],
        limit=limit,
        offset=offset,
    )

    return conversations


@router.post("/{opportunity_id}/ask", response_model=AskQuestionResponse)
async def ask_question_about_opportunity(
    opportunity_id: str,
    request: AskQuestionRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Ask a question about an opportunity.

    Uses AI to answer based on:
    - The opportunity's details (title, description, scores, status, etc.)
    - Related documents from the knowledge base

    The conversation is stored and can be retrieved later via
    GET /{opportunity_id}/conversations.
    """
    # Verify opportunity exists and belongs to client
    opp = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        result = await ask_about_project(
            opportunity_id=opportunity_id,
            question=request.question,
            client_id=current_user["client_id"],
            user_id=current_user["id"],
        )

        # Format sources for response model
        formatted_sources = []
        for source in result.get("sources", []):
            formatted_sources.append(
                {
                    "chunk_id": source.get("chunk_id", ""),
                    "document_id": source.get("document_id", ""),
                    "document_name": source.get("document_name", "Unknown"),
                    "relevance_score": source.get("relevance_score", 0.0),
                    "snippet": source.get("snippet", ""),
                    "metadata": source.get("metadata", {}),
                }
            )

        return {"response": result["response"], "sources": formatted_sources}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error answering question about opportunity: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question") from e


# ============================================================================
# TASKMASTER CHAT ENDPOINT
# ============================================================================


class TaskmasterChatRequest(BaseModel):
    """Request to chat with Taskmaster about an opportunity/project."""

    message: str = Field(..., min_length=1, max_length=2000)


class TaskmasterChatResponse(BaseModel):
    """Response from Taskmaster chat."""

    response: str
    tasks_created: int
    task_titles: List[str]


@router.post("/{opportunity_id}/taskmaster-chat", response_model=TaskmasterChatResponse)
async def taskmaster_chat_for_opportunity(
    opportunity_id: str,
    request: TaskmasterChatRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Chat with Taskmaster to break down an opportunity/project into tasks.

    Taskmaster will:
    - Respond with task suggestions based on the project context
    - Extract concrete tasks from the conversation
    - Create task_candidates linked to this opportunity
    - Tasks appear in the Discovery Inbox for review

    Only available for opportunities that have a project_name (i.e., are active projects).
    """
    # Verify opportunity exists, belongs to client, and is a project
    opp = (
        supabase.table("ai_projects")
        .select("id, project_name")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if not opp.data.get("project_name"):
        raise HTTPException(
            status_code=400,
            detail="Taskmaster is only available for opportunities that have been converted to projects",
        )

    try:
        result = await chat_with_taskmaster(
            opportunity_id=opportunity_id,
            message=request.message,
            client_id=current_user["client_id"],
            user_id=current_user["id"],
            supabase=supabase,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in Taskmaster chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Taskmaster chat") from e


# ============================================================================
# JUSTIFICATION GENERATION ENDPOINTS
# ============================================================================


@router.post("/{opportunity_id}/generate-justifications")
async def generate_justifications_for_opportunity(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Generate AI-powered justifications for an opportunity's scores.

    Creates:
    - A 3-4 sentence opportunity summary
    - A 3-4 sentence justification for each scoring dimension

    This is automatically called when scores are updated, but can also
    be triggered manually to regenerate justifications.
    """
    # Verify opportunity exists and belongs to client
    opp = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        justifications = await generate_project_justifications(
            opportunity_id=opportunity_id, client_id=current_user["client_id"]
        )
        return {
            "message": "Justifications generated successfully",
            "justifications": justifications,
        }
    except Exception as e:
        logger.error(f"Failed to generate justifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate justifications") from e


@router.post("/generate-all-justifications")
async def generate_all_opportunity_justifications(
    current_user: dict = Depends(get_current_user),
):
    """Generate justifications for all opportunities belonging to the current client.

    This is useful for backfilling justifications for existing opportunities
    or regenerating all justifications after significant changes.

    Returns counts of successful and failed generations.
    """
    try:
        result = await generate_all_justifications(client_id=current_user["client_id"])
        return result
    except Exception as e:
        logger.error(f"Failed to generate all justifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate justifications") from e


# ============================================================================
# GOAL ALIGNMENT ANALYSIS ENDPOINTS
# ============================================================================


@router.post("/analyze-goal-alignment/all")
async def analyze_all_goal_alignment(
    current_user: dict = Depends(get_current_user),
):
    """Analyze goal alignment for all opportunities belonging to the current client.

    Evaluates each opportunity against IS team FY27 strategic goals:
    - Decision-Ready Customer Journey (0-25 pts)
    - Maximize Business Systems & AI Value (0-25 pts)
    - Data-First Digital Workforce (0-25 pts)
    - High-Trust IS Culture (0-25 pts)

    Returns counts, average score, and distribution across alignment levels.
    """
    try:
        result = await batch_analyze_all(client_id=current_user["client_id"])
        return result
    except Exception as e:
        logger.error(f"Failed to analyze goal alignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze goal alignment") from e


@router.post("/{opportunity_id}/analyze-goal-alignment")
async def analyze_opportunity_goal_alignment(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Analyze a single opportunity's alignment with IS team strategic goals.

    Produces:
    - Total alignment score (0-100)
    - Individual pillar scores (0-25 each) with rationale
    - Impacted KPIs
    - Summary of strategic alignment

    Alignment levels:
    - 80-100: High alignment - directly advances strategic goals
    - 60-79: Moderate alignment - strong indirect support
    - 40-59: Low alignment - tangential connection
    - 0-39: Minimal alignment - limited strategic value
    """
    # Verify opportunity exists and belongs to client
    opp = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        score, details = await analyze_goal_alignment(
            opportunity_id=opportunity_id, client_id=current_user["client_id"]
        )
        return {
            "opportunity_id": opportunity_id,
            "goal_alignment_score": score,
            "goal_alignment_details": details,
            "level": (
                "high"
                if score >= 80
                else "moderate"
                if score >= 60
                else "low"
                if score >= 40
                else "minimal"
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze goal alignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze goal alignment") from e


# ============================================================================
# SINGLE OPPORTUNITY ENDPOINTS
# ============================================================================


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get a single opportunity by ID."""
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Get owner name if exists
    owner_name = None
    if result.data.get("owner_stakeholder_id"):
        owner_result = (
            supabase.table("stakeholders")
            .select("name")
            .eq("id", result.data["owner_stakeholder_id"])
            .single()
            .execute()
        )
        if owner_result.data:
            owner_name = owner_result.data["name"]

    return _format_opportunity(result.data, owner_name)


@router.post("/", response_model=OpportunityResponse)
async def create_opportunity(
    opportunity: OpportunityCreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Create a new opportunity."""
    data = {
        "client_id": current_user["client_id"],
        "opportunity_code": opportunity.opportunity_code.upper(),
        "title": opportunity.title,
        "description": opportunity.description,
        "department": opportunity.department,
        "owner_stakeholder_id": opportunity.owner_stakeholder_id,
        "current_state": opportunity.current_state,
        "desired_state": opportunity.desired_state,
        "roi_potential": opportunity.roi_potential,
        "implementation_effort": opportunity.implementation_effort,
        "strategic_alignment": opportunity.strategic_alignment,
        "stakeholder_readiness": opportunity.stakeholder_readiness,
        "status": opportunity.status,
        "next_step": opportunity.next_step,
        "blockers": opportunity.blockers,
        "follow_up_questions": opportunity.follow_up_questions,
        "roi_indicators": opportunity.roi_indicators,
        "source_type": opportunity.source_type,
        "source_notes": opportunity.source_notes,
    }

    try:
        result = supabase.table("ai_projects").insert(data).execute()
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Opportunity code {opportunity.opportunity_code} already exists",
            )
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e

    created_opp = result.data[0]

    # Generate justifications if scores are provided
    has_scores = any(
        [
            opportunity.roi_potential,
            opportunity.implementation_effort,
            opportunity.strategic_alignment,
            opportunity.stakeholder_readiness,
        ]
    )
    if has_scores:
        try:
            await generate_project_justifications(
                opportunity_id=created_opp["id"], client_id=current_user["client_id"]
            )
            # Refetch to get updated justifications
            updated = (
                supabase.table("ai_projects")
                .select("*")
                .eq("id", created_opp["id"])
                .single()
                .execute()
            )
            created_opp = updated.data
        except Exception as e:
            logger.warning(f"Failed to generate justifications on create: {e}")

    return _format_opportunity(created_opp)


@router.patch("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    update: OpportunityUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update an opportunity."""
    # Verify ownership
    existing = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Build update dict
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    if update_data.get("opportunity_code"):
        update_data["opportunity_code"] = update_data["opportunity_code"].upper()

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("ai_projects").update(update_data).eq("id", opportunity_id).execute()

    return _format_opportunity(result.data[0])


@router.patch("/{opportunity_id}/scores", response_model=OpportunityResponse)
async def update_opportunity_scores(
    opportunity_id: str,
    scores: OpportunityScoreUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update just the scores for an opportunity.

    Convenience endpoint for quick score updates without touching other fields.
    Automatically regenerates justifications when scores change.
    """
    # Get existing opportunity with current scores
    existing = (
        supabase.table("ai_projects")
        .select(
            "id, roi_potential, implementation_effort, strategic_alignment, stakeholder_readiness"
        )
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    old_scores = existing.data
    update_data = {k: v for k, v in scores.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No scores to update")

    result = supabase.table("ai_projects").update(update_data).eq("id", opportunity_id).execute()

    updated_opp = result.data[0]

    # Regenerate justifications if scores changed
    try:
        regenerated = await regenerate_if_scores_changed(
            opportunity_id=opportunity_id,
            old_scores=old_scores,
            new_scores=update_data,
            client_id=current_user["client_id"],
        )
        if regenerated:
            # Refetch to get updated justifications
            refreshed = (
                supabase.table("ai_projects")
                .select("*")
                .eq("id", opportunity_id)
                .single()
                .execute()
            )
            updated_opp = refreshed.data
    except Exception as e:
        logger.warning(f"Failed to regenerate justifications on score update: {e}")

    return _format_opportunity(updated_opp)


class StatusUpdateRequest(BaseModel):
    """Update opportunity status with optional project name."""

    status: str
    next_step: Optional[str] = None
    project_name: Optional[str] = None
    project_description: Optional[str] = None


@router.patch("/{opportunity_id}/status")
async def update_opportunity_status(
    opportunity_id: str,
    request: StatusUpdateRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update opportunity status.

    Valid statuses: identified, scoping, pilot, scaling, completed, blocked

    When moving to 'scoping' or 'pilot', a project_name is required
    if not already set on the opportunity.
    """
    valid_statuses = ["identified", "scoping", "pilot", "scaling", "completed", "blocked"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    # Verify ownership and get current data
    existing = (
        supabase.table("ai_projects")
        .select("id, project_name, status")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Require project_name when moving to scoping or pilot
    requires_project_name = request.status in ["scoping", "pilot"]
    has_project_name = existing.data.get("project_name") or request.project_name

    if requires_project_name and not has_project_name:
        raise HTTPException(
            status_code=400,
            detail="project_name is required when moving to scoping or pilot status",
        )

    update_data = {"status": request.status}
    if request.next_step is not None:
        update_data["next_step"] = request.next_step
    if request.project_name:
        update_data["project_name"] = request.project_name
    if request.project_description:
        update_data["project_description"] = request.project_description

    result = supabase.table("ai_projects").update(update_data).eq("id", opportunity_id).execute()

    return _format_opportunity(result.data[0])


@router.delete("/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Delete an opportunity."""
    # Verify ownership
    existing = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    supabase.table("ai_projects").delete().eq("id", opportunity_id).execute()

    return {"message": "Opportunity deleted"}


# ============================================================================
# STAKEHOLDER LINK ENDPOINTS
# ============================================================================


@router.get("/{opportunity_id}/stakeholders", response_model=List[StakeholderLinkResponse])
async def get_opportunity_stakeholders(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get all stakeholders linked to an opportunity."""
    # Verify opportunity exists and belongs to client
    opp = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Get links with stakeholder info
    result = (
        supabase.table("opportunity_stakeholder_link")
        .select("*, stakeholders(name, role, department)")
        .eq("opportunity_id", opportunity_id)
        .execute()
    )

    return [
        {
            "id": link["id"],
            "opportunity_id": link["opportunity_id"],
            "stakeholder_id": link["stakeholder_id"],
            "stakeholder_name": link["stakeholders"]["name"] if link.get("stakeholders") else None,
            "stakeholder_role": link["stakeholders"]["role"] if link.get("stakeholders") else None,
            "stakeholder_department": link["stakeholders"]["department"]
            if link.get("stakeholders")
            else None,
            "role": link["role"],
            "notes": link.get("notes"),
            "created_at": link["created_at"],
        }
        for link in result.data
    ]


@router.post("/{opportunity_id}/stakeholders", response_model=StakeholderLinkResponse)
async def link_stakeholder_to_opportunity(
    opportunity_id: str,
    link: StakeholderLinkCreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Link a stakeholder to an opportunity."""
    # Verify opportunity exists
    opp = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Verify stakeholder exists
    stakeholder = (
        supabase.table("stakeholders")
        .select("id, name, role, department")
        .eq("id", link.stakeholder_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not stakeholder.data:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Create link
    try:
        result = (
            supabase.table("opportunity_stakeholder_link")
            .insert(
                {
                    "opportunity_id": opportunity_id,
                    "stakeholder_id": link.stakeholder_id,
                    "role": link.role,
                    "notes": link.notes,
                }
            )
            .execute()
        )
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=409, detail="Stakeholder already linked to this opportunity"
            )
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e

    return {
        "id": result.data[0]["id"],
        "opportunity_id": opportunity_id,
        "stakeholder_id": link.stakeholder_id,
        "stakeholder_name": stakeholder.data["name"],
        "stakeholder_role": stakeholder.data.get("role"),
        "stakeholder_department": stakeholder.data.get("department"),
        "role": link.role,
        "notes": link.notes,
        "created_at": result.data[0]["created_at"],
    }


@router.delete("/{opportunity_id}/stakeholders/{stakeholder_id}")
async def unlink_stakeholder_from_opportunity(
    opportunity_id: str,
    stakeholder_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Remove a stakeholder link from an opportunity."""
    # Verify opportunity exists
    opp = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not opp.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    supabase.table("opportunity_stakeholder_link").delete().eq("opportunity_id", opportunity_id).eq(
        "stakeholder_id", stakeholder_id
    ).execute()

    return {"message": "Stakeholder unlinked from opportunity"}


# ============================================================================
# OPPORTUNITY CANDIDATES ENDPOINTS
# ============================================================================


class OpportunityCandidateResponse(BaseModel):
    """Opportunity candidate response model."""

    id: str
    title: str
    description: Optional[str]
    department: Optional[str]
    source_document_id: Optional[str]
    source_document_name: Optional[str]
    source_text: Optional[str]
    suggested_roi_potential: Optional[int]
    suggested_effort: Optional[int]
    suggested_alignment: Optional[int]
    suggested_readiness: Optional[int]
    potential_impact: Optional[str]
    related_stakeholder_names: Optional[List[str]]
    status: str
    confidence: str
    matched_opportunity_id: Optional[str]
    match_confidence: Optional[float]
    match_reason: Optional[str]
    created_at: str


class OpportunityCandidateAccept(BaseModel):
    """Accept an opportunity candidate, optionally overriding fields."""

    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    roi_potential: Optional[int] = Field(None, ge=1, le=5)
    implementation_effort: Optional[int] = Field(None, ge=1, le=5)
    strategic_alignment: Optional[int] = Field(None, ge=1, le=5)
    stakeholder_readiness: Optional[int] = Field(None, ge=1, le=5)
    link_to_existing: bool = (
        False  # If true, link source to existing opportunity instead of creating new
    )


class OpportunityCandidateReject(BaseModel):
    """Reject an opportunity candidate with reason."""

    reason: Optional[str] = None


@router.get("/candidates/list", response_model=List[OpportunityCandidateResponse])
async def list_project_candidates(
    status: str = "pending",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List opportunity candidates for review.

    Candidates are extracted from meeting documents and await user review
    before becoming real opportunities.
    """
    query = (
        supabase.table("project_candidates")
        .select("*")
        .eq("client_id", current_user["client_id"])
        .eq("status", status)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )

    result = query.execute()

    return [
        {
            "id": c["id"],
            "title": c["title"],
            "description": c.get("description"),
            "department": c.get("department"),
            "source_document_id": c.get("source_document_id"),
            "source_document_name": c.get("source_document_name"),
            "source_text": c.get("source_text"),
            "suggested_roi_potential": c.get("suggested_roi_potential"),
            "suggested_effort": c.get("suggested_effort"),
            "suggested_alignment": c.get("suggested_alignment"),
            "suggested_readiness": c.get("suggested_readiness"),
            "potential_impact": c.get("potential_impact"),
            "related_stakeholder_names": c.get("related_stakeholder_names") or [],
            "status": c["status"],
            "confidence": c.get("confidence", "medium"),
            "matched_opportunity_id": c.get("matched_opportunity_id"),
            "match_confidence": c.get("match_confidence"),
            "match_reason": c.get("match_reason"),
            "created_at": c["created_at"],
        }
        for c in result.data
    ]


@router.get("/candidates/count")
async def get_project_candidates_count(
    current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get count of pending opportunity candidates.

    Used for dashboard badge display.
    """
    result = (
        supabase.table("project_candidates")
        .select("id", count="exact")
        .eq("client_id", current_user["client_id"])
        .eq("status", "pending")
        .execute()
    )

    return {"count": result.count or 0}


@router.post("/candidates/{candidate_id}/accept", response_model=OpportunityResponse)
async def accept_opportunity_candidate(
    candidate_id: str,
    accept_data: OpportunityCandidateAccept = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Accept an opportunity candidate, creating a new opportunity.

    If the candidate has a matched_opportunity_id and link_to_existing is True,
    the source document will be linked to the existing opportunity instead
    of creating a new one.
    """
    if accept_data is None:
        accept_data = OpportunityCandidateAccept()

    # Get the candidate
    candidate = (
        supabase.table("project_candidates")
        .select("*")
        .eq("id", candidate_id)
        .eq("client_id", current_user["client_id"])
        .eq("status", "pending")
        .single()
        .execute()
    )

    if not candidate.data:
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    cand = candidate.data
    now = datetime.now(timezone.utc).isoformat()

    # If linking to existing opportunity
    if accept_data.link_to_existing and cand.get("matched_opportunity_id"):
        # Just update the existing opportunity's source_notes with this new info
        existing_opp = (
            supabase.table("ai_projects")
            .select("*")
            .eq("id", cand["matched_opportunity_id"])
            .single()
            .execute()
        )

        if existing_opp.data:
            # Append source info to notes
            existing_notes = existing_opp.data.get("source_notes") or ""
            new_notes = f"{existing_notes}\n\nLinked from: {cand.get('source_document_name', 'Document')}\nQuote: {cand.get('source_text', '')[:200]}"

            supabase.table("ai_projects").update({"source_notes": new_notes.strip()}).eq(
                "id", cand["matched_opportunity_id"]
            ).execute()

            # Mark candidate as accepted
            supabase.table("project_candidates").update(
                {
                    "status": "accepted",
                    "accepted_at": now,
                    "accepted_by": current_user["id"],
                    "created_opportunity_id": cand["matched_opportunity_id"],
                }
            ).eq("id", candidate_id).execute()

            return _format_opportunity(existing_opp.data)

    # Create new opportunity
    dept = accept_data.department or cand.get("department") or "General"
    dept_prefix = dept[0].upper() if dept else "G"

    # Get next opportunity code using RPC (avoids PostgREST ilike issues)
    try:
        existing_codes = supabase.rpc(
            "count_opportunity_codes_by_prefix",
            {"p_client_id": current_user["client_id"], "p_prefix": dept_prefix},
        ).execute()
        code_count = existing_codes.data[0].get("code_count", 0) if existing_codes.data else 0
    except Exception as rpc_err:
        logger.warning(f"RPC count_opportunity_codes_by_prefix failed: {rpc_err}")
        code_count = 0

    next_num = code_count + 1
    opp_code = f"{dept_prefix}{next_num:02d}"

    opp_data = {
        "client_id": current_user["client_id"],
        "opportunity_code": opp_code,
        "title": accept_data.title or cand["title"],
        "description": accept_data.description or cand.get("description"),
        "department": dept,
        "roi_potential": accept_data.roi_potential or cand.get("suggested_roi_potential") or 3,
        "implementation_effort": accept_data.implementation_effort
        or cand.get("suggested_effort")
        or 3,
        "strategic_alignment": accept_data.strategic_alignment
        or cand.get("suggested_alignment")
        or 3,
        "stakeholder_readiness": accept_data.stakeholder_readiness
        or cand.get("suggested_readiness")
        or 3,
        "status": "identified",
        "source_type": "meeting",
        "source_id": cand.get("source_document_id"),
        "source_notes": cand.get("source_text"),
        "created_at": now,
    }

    try:
        result = supabase.table("ai_projects").insert(opp_data).execute()
        new_opp = result.data[0]

        # Mark candidate as accepted
        supabase.table("project_candidates").update(
            {
                "status": "accepted",
                "accepted_at": now,
                "accepted_by": current_user["id"],
                "created_opportunity_id": new_opp["id"],
            }
        ).eq("id", candidate_id).execute()

        # Generate justifications for the new opportunity
        try:
            await generate_project_justifications(
                opportunity_id=new_opp["id"], client_id=current_user["client_id"]
            )
            # Refetch to get updated justifications
            updated = (
                supabase.table("ai_projects").select("*").eq("id", new_opp["id"]).single().execute()
            )
            new_opp = updated.data
        except Exception as e:
            logger.warning(f"Failed to generate justifications for accepted candidate: {e}")

        return _format_opportunity(new_opp)

    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Opportunity code already exists") from e
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/candidates/{candidate_id}/reject")
async def reject_opportunity_candidate(
    candidate_id: str,
    reject_data: OpportunityCandidateReject = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Reject an opportunity candidate.

    Optionally provide a reason for rejection.
    """
    if reject_data is None:
        reject_data = OpportunityCandidateReject()

    # Verify candidate exists and is pending
    candidate = (
        supabase.table("project_candidates")
        .select("id")
        .eq("id", candidate_id)
        .eq("client_id", current_user["client_id"])
        .eq("status", "pending")
        .single()
        .execute()
    )

    if not candidate.data:
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    now = datetime.now(timezone.utc).isoformat()

    supabase.table("project_candidates").update(
        {
            "status": "rejected",
            "rejected_at": now,
            "rejected_by": current_user["id"],
            "rejection_reason": reject_data.reason,
        }
    ).eq("id", candidate_id).execute()

    return {"message": "Candidate rejected"}


class LinkOpportunityCandidateRequest(BaseModel):
    """Request body for linking a candidate to an existing opportunity."""

    opportunity_id: str


@router.post("/candidates/{candidate_id}/link")
async def link_opportunity_candidate(
    candidate_id: str,
    body: LinkOpportunityCandidateRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Link an opportunity candidate to an existing opportunity instead of creating a new one.

    This is used when a duplicate is detected and the user wants to associate
    the candidate's context with an existing opportunity rather than creating a new one.
    """
    client_id = current_user.get("client_id")
    user_id = current_user["id"]

    # Verify candidate exists and is pending
    candidate_result = (
        supabase.table("project_candidates")
        .select("*")
        .eq("id", candidate_id)
        .eq("client_id", client_id)
        .eq("status", "pending")
        .single()
        .execute()
    )

    if not candidate_result.data:
        raise HTTPException(status_code=404, detail="Candidate not found or already processed")

    candidate = candidate_result.data

    # Verify target opportunity exists
    opp_result = (
        supabase.table("ai_projects")
        .select("id, title, project_name, description")
        .eq("id", body.opportunity_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    if not opp_result.data:
        raise HTTPException(status_code=404, detail="Target opportunity not found")

    opportunity = opp_result.data

    # Append candidate context to the existing opportunity's description
    existing_desc = opportunity.get("description") or ""
    candidate_source = candidate.get("source_document_name") or ""
    candidate_quote = candidate.get("source_text") or ""

    if candidate_source or candidate_quote:
        linked_note = f"\n\n---\nLinked from: {candidate_source}"
        if candidate_quote:
            linked_note += f'\nQuote: "{candidate_quote[:200]}..."'
        new_description = existing_desc + linked_note

        supabase.table("ai_projects").update({"description": new_description}).eq(
            "id", body.opportunity_id
        ).execute()

    # Mark candidate as accepted with reference to the linked opportunity
    now = datetime.now(timezone.utc).isoformat()
    supabase.table("project_candidates").update(
        {
            "status": "accepted",
            "created_opportunity_id": body.opportunity_id,
            "accepted_at": now,
            "accepted_by": user_id,
        }
    ).eq("id", candidate_id).execute()

    logger.info(
        f"Opportunity candidate {candidate_id} linked to existing opportunity {body.opportunity_id}"
    )

    return {
        "success": True,
        "linked_opportunity_id": body.opportunity_id,
        "linked_opportunity_title": opportunity.get("title") or opportunity.get("project_name"),
        "message": "Linked to existing opportunity",
    }


# ============================================================================
# CONFIDENCE EVALUATION ENDPOINTS
# ============================================================================


@router.post("/evaluate-confidence")
async def evaluate_all_confidence(
    current_user: dict = Depends(get_current_user),
):
    """Evaluate confidence scores for all opportunities.

    Uses a rubric based on information completeness:
    - 80-100%: High confidence - scores well-supported
    - 60-79%: Moderate confidence - some assumptions
    - 40-59%: Low confidence - significant unknowns
    - 0-39%: Very low confidence - mostly speculative

    Returns distribution and average confidence.
    """
    from services.project_confidence import evaluate_all_opportunities

    try:
        result = await evaluate_all_opportunities(current_user["client_id"])
        return result
    except Exception as e:
        logger.error(f"Failed to evaluate confidence: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{opportunity_id}/evaluate-confidence")
async def evaluate_single_confidence(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Evaluate and update confidence score for a single opportunity."""
    from services.project_confidence import evaluate_opportunity_confidence

    # Fetch opportunity
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("id", opportunity_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opportunity = result.data

    # Evaluate confidence
    confidence, questions = evaluate_opportunity_confidence(opportunity)

    # Update in database
    supabase.table("ai_projects").update(
        {
            "scoring_confidence": confidence,
            "confidence_questions": questions,
        }
    ).eq("id", opportunity_id).execute()

    return {
        "opportunity_id": opportunity_id,
        "scoring_confidence": confidence,
        "confidence_questions": questions,
        "level": (
            "high"
            if confidence >= 80
            else "moderate"
            if confidence >= 60
            else "low"
            if confidence >= 40
            else "very_low"
        ),
    }
