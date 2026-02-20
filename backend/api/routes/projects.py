"""Projects API Routes.

Endpoints for managing AI implementation projects with 4-dimension scoring.
Supports filtering by tier, department, status, and stakeholder.

Added in v2: Related documents, conversations, and Q&A endpoints for detail modal.

Note: This replaces the old /api/opportunities endpoints. The frontend should be
updated to use /api/projects instead.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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
from services.task_kraken import (
    evaluate_project_tasks,
    execute_approved_tasks,
)
from services.task_kraken import (
    get_evaluation as get_kraken_evaluation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class ProjectCreate(BaseModel):
    """Create a new project."""

    project_code: str = Field(..., min_length=2, max_length=10, description="Short code like F01, L02")
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
    status: str = "backlog"
    next_step: Optional[str] = None
    blockers: List[str] = []
    follow_up_questions: List[str] = []
    roi_indicators: dict = {}
    source_type: Optional[str] = None
    source_id: Optional[str] = None  # e.g., initiative_id for initiative_chat source
    source_notes: Optional[str] = None
    initiative_ids: List[str] = Field(default=[], description="List of linked DISCo initiative IDs")
    scoring_confidence: Optional[int] = Field(None, ge=0, le=100, description="Confidence in scoring (0-100)")
    confidence_questions: List[str] = Field(default=[], description="Questions that would raise confidence")


class ProjectUpdate(BaseModel):
    """Update a project."""

    project_code: Optional[str] = Field(None, min_length=2, max_length=10)
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
    source_id: Optional[str] = None
    source_notes: Optional[str] = None
    initiative_ids: Optional[List[str]] = None
    scoring_confidence: Optional[int] = Field(None, ge=0, le=100)
    confidence_questions: Optional[List[str]] = None
    display_order: Optional[int] = None
    goal_alignment_details: Optional[dict] = None


class ProjectScoreUpdate(BaseModel):
    """Update just the scores for a project."""

    roi_potential: Optional[int] = Field(None, ge=1, le=5)
    implementation_effort: Optional[int] = Field(None, ge=1, le=5)
    strategic_alignment: Optional[int] = Field(None, ge=1, le=5)
    stakeholder_readiness: Optional[int] = Field(None, ge=1, le=5)


class ProjectResponse(BaseModel):
    """Project response model."""

    id: str
    project_code: str
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
    source_id: Optional[str] = None  # Links to initiative, document, etc.
    source_notes: Optional[str]
    initiative_ids: List[str] = []  # Linked DISCo initiatives
    created_at: str
    updated_at: str
    # Project fields (for scoping/pilot phase)
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    # Justification fields
    project_summary: Optional[str] = None
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
    # Display order for manual sorting
    display_order: int = 0


class StakeholderLinkCreate(BaseModel):
    """Link a stakeholder to a project."""

    stakeholder_id: str
    role: str = "involved"  # owner, champion, involved, blocker, approver
    notes: Optional[str] = None


class StakeholderLinkResponse(BaseModel):
    """Stakeholder link response."""

    id: str
    project_id: str
    stakeholder_id: str
    stakeholder_name: str
    stakeholder_role: Optional[str]
    stakeholder_department: Optional[str]
    role: str
    notes: Optional[str]
    created_at: str


# ============================================================================
# KRAKEN MODELS
# ============================================================================


class KrakenExecuteRequest(BaseModel):
    """Request to execute approved tasks via Kraken."""

    task_ids: List[str] = Field(..., min_length=1, description="Task IDs approved for execution")


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
    """A document related to a project (for scoring justification)."""

    chunk_id: str
    document_id: str
    document_name: str
    relevance_score: float
    snippet: str
    metadata: RelatedDocumentMetadata


class AskQuestionRequest(BaseModel):
    """Request to ask a question about a project."""

    question: str = Field(..., min_length=1, max_length=1000)


class AskQuestionResponse(BaseModel):
    """Response to a question about a project."""

    response: str
    sources: List[RelatedDocumentResponse]


class ConversationResponse(BaseModel):
    """A Q&A conversation entry for a project."""

    id: str
    question: str
    response: str
    source_documents: List[dict]
    created_at: str


class LinkedDocumentResponse(BaseModel):
    """A document manually linked to a project."""

    id: str  # Link ID
    document_id: str
    document_name: str
    title: Optional[str] = None
    linked_at: str
    linked_by: Optional[str] = None
    notes: Optional[str] = None


class LinkDocumentsRequest(BaseModel):
    """Request to link documents to a project."""

    document_ids: List[str] = Field(..., min_items=1)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _format_project(proj: dict, owner_name: Optional[str] = None) -> dict:
    """Format project for response."""
    return {
        "id": proj["id"],
        "project_code": proj["project_code"],
        "title": proj["title"],
        "description": proj.get("description"),
        "department": proj.get("department"),
        "owner_stakeholder_id": proj.get("owner_stakeholder_id"),
        "owner_name": owner_name,
        "current_state": proj.get("current_state"),
        "desired_state": proj.get("desired_state"),
        "roi_potential": proj.get("roi_potential"),
        "implementation_effort": proj.get("implementation_effort"),
        "strategic_alignment": proj.get("strategic_alignment"),
        "stakeholder_readiness": proj.get("stakeholder_readiness"),
        "total_score": proj.get("total_score", 0),
        "tier": proj.get("tier", 4),
        "status": proj.get("status", "backlog"),
        "next_step": proj.get("next_step"),
        "blockers": proj.get("blockers") or [],
        "follow_up_questions": proj.get("follow_up_questions") or [],
        "roi_indicators": proj.get("roi_indicators") or {},
        "source_type": proj.get("source_type"),
        "source_id": proj.get("source_id"),
        "source_notes": proj.get("source_notes"),
        "initiative_ids": proj.get("initiative_ids") or [],
        "created_at": proj["created_at"],
        "updated_at": proj.get("updated_at", proj["created_at"]),
        # Project fields
        "project_name": proj.get("project_name"),
        "project_description": proj.get("project_description"),
        # Justification fields
        "project_summary": proj.get("project_summary"),
        "roi_justification": proj.get("roi_justification"),
        "effort_justification": proj.get("effort_justification"),
        "alignment_justification": proj.get("alignment_justification"),
        "readiness_justification": proj.get("readiness_justification"),
        # Scoring confidence fields
        "scoring_confidence": proj.get("scoring_confidence"),
        "confidence_questions": proj.get("confidence_questions") or [],
        # Goal alignment fields
        "goal_alignment_score": proj.get("goal_alignment_score"),
        "goal_alignment_details": proj.get("goal_alignment_details"),
    }


async def _get_owner_names(supabase, project_ids: List[str]) -> dict:
    """Get owner names for a list of projects."""
    if not project_ids:
        return {}

    # Get projects with owner IDs
    result = supabase.table("ai_projects").select("id, owner_stakeholder_id").in_("id", project_ids).execute()

    owner_ids = [p["owner_stakeholder_id"] for p in result.data if p.get("owner_stakeholder_id")]

    if not owner_ids:
        return {}

    # Get stakeholder names
    stakeholders = supabase.table("stakeholders").select("id, name").in_("id", owner_ids).execute()

    stakeholder_map = {s["id"]: s["name"] for s in stakeholders.data}

    # Map project ID to owner name
    return {
        p["id"]: stakeholder_map.get(p["owner_stakeholder_id"]) for p in result.data if p.get("owner_stakeholder_id")
    }


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        from uuid import UUID

        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


async def _resolve_initiative_id(initiative_id: str, supabase) -> Optional[str]:
    """Resolve an initiative ID (UUID or name) to its UUID."""
    if _is_valid_uuid(initiative_id):
        return initiative_id

    # Look up by name (use maybe_single to avoid exception on 0 rows)
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiatives").select("id").eq("name", initiative_id).maybe_single().execute()
        )
        return result.data["id"] if result.data else None
    except Exception:
        return None


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    department: Optional[str] = None,
    tier: Optional[int] = Query(None, ge=1, le=4),
    status: Optional[str] = None,
    owner_stakeholder_id: Optional[str] = None,
    initiative_id: Optional[str] = Query(None, description="Filter by linked initiative ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List all projects for the current client.

    Supports filtering by department, tier, status, owner, and initiative.
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
    if initiative_id:
        # Resolve initiative_id if it's a name
        resolved_id = await _resolve_initiative_id(initiative_id, supabase)
        if resolved_id:
            query = query.contains("initiative_ids", [resolved_id])
        else:
            # Initiative not found, return empty results
            return []

    result = query.order("total_score", desc=True).range(offset, offset + limit - 1).execute()

    # Get owner names
    proj_ids = [p["id"] for p in result.data]
    owner_names = await _get_owner_names(supabase, proj_ids)

    return [_format_project(p, owner_names.get(p["id"])) for p in result.data]


@router.get("/by-tier")
async def get_projects_by_tier(
    department: Optional[str] = None,
    status: Optional[str] = None,
    max_per_tier: int = Query(50, ge=1, le=200, description="Max projects per tier"),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get projects grouped by tier.

    Returns a dict with tier keys (1-4) and lists of projects.
    Use max_per_tier to limit results (default 50 per tier, max 200).
    """
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])

    if department:
        query = query.eq("department", department)
    if status:
        query = query.eq("status", status)

    # Limit total results to prevent OOM (4 tiers * max_per_tier)
    result = query.order("total_score", desc=True).limit(max_per_tier * 4).execute()

    # Get owner names
    proj_ids = [p["id"] for p in result.data]
    owner_names = await _get_owner_names(supabase, proj_ids)

    # Group by tier (respecting max_per_tier limit)
    grouped = {1: [], 2: [], 3: [], 4: []}
    for proj in result.data:
        tier = proj.get("tier", 4)
        if len(grouped[tier]) < max_per_tier:
            grouped[tier].append(_format_project(proj, owner_names.get(proj["id"])))

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
async def get_projects_by_department(
    tier: Optional[int] = Query(None, ge=1, le=4),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get projects grouped by department."""
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])

    if tier:
        query = query.eq("tier", tier)
    if status:
        query = query.eq("status", status)

    result = query.order("total_score", desc=True).execute()

    # Get owner names
    proj_ids = [p["id"] for p in result.data]
    owner_names = await _get_owner_names(supabase, proj_ids)

    # Group by department
    grouped = {}
    for proj in result.data:
        dept = proj.get("department") or "unassigned"
        if dept not in grouped:
            grouped[dept] = []
        grouped[dept].append(_format_project(proj, owner_names.get(proj["id"])))

    return {
        "departments": grouped,
        "summary": {dept: len(projs) for dept, projs in grouped.items()},
    }


@router.get("/top")
async def get_top_projects(
    limit: int = Query(10, ge=1, le=50),
    exclude_status: Optional[str] = "completed",
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get top projects by score.

    Excludes completed projects by default.
    """
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])

    if exclude_status:
        query = query.neq("status", exclude_status)

    result = query.order("total_score", desc=True).limit(limit).execute()

    # Get owner names
    proj_ids = [p["id"] for p in result.data]
    owner_names = await _get_owner_names(supabase, proj_ids)

    return [_format_project(p, owner_names.get(p["id"])) for p in result.data]


@router.get("/blocked")
async def get_blocked_projects(current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)):
    """Get all blocked projects."""
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("client_id", current_user["client_id"])
        .eq("status", "blocked")
        .order("total_score", desc=True)
        .execute()
    )

    # Get owner names
    proj_ids = [p["id"] for p in result.data]
    owner_names = await _get_owner_names(supabase, proj_ids)

    return [_format_project(p, owner_names.get(p["id"])) for p in result.data]


@router.get("/summary")
async def get_projects_summary(current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)):
    """Get a summary of all projects.

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

    for proj in result.data:
        # Tier
        tier = proj.get("tier", 4)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Status
        status = proj.get("status", "backlog")
        status_counts[status] = status_counts.get(status, 0) + 1

        # Department
        dept = proj.get("department") or "unassigned"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    return {
        "total": len(result.data),
        "by_tier": tier_counts,
        "by_status": status_counts,
        "by_department": dept_counts,
    }


# ============================================================================
# DISCO AGENT ENDPOINTS (for project-level agent runs)
# ============================================================================


class ProjectAgentRunRequest(BaseModel):
    """Request to run a DISCO agent on a project."""

    agent_type: str
    document_ids: Optional[List[str]] = None
    kb_tags: Optional[List[str]] = None


@router.post("/{project_id}/agents/run")
async def run_project_agent(
    project_id: str,
    data: ProjectAgentRunRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Run a DISCO agent on a project with streaming response."""
    from services.disco import run_agent

    # Verify project exists and user has access
    client_id = current_user.get("client_id")
    if not client_id:
        from database import get_default_client_id

        client_id = get_default_client_id()

    project = (
        supabase.table("ai_projects").select("id").eq("id", project_id).eq("client_id", client_id).single().execute()
    )
    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_stream():
        # Send initial padding to force proxy buffer flush
        yield ": " + " " * 2048 + "\n\n"

        try:
            agent_gen = run_agent(
                project_id=project_id,
                agent_type=data.agent_type,
                user_id=current_user["id"],
                document_ids=data.document_ids,
                kb_tags=data.kb_tags,
            )

            async for event in agent_gen:
                event_type = event.get("type", "unknown")
                event_data = event.get("data", "")

                if event_type == "content":
                    yield f"data: {event_data}\n\n"
                elif event_type == "keepalive":
                    yield ": keepalive\n\n"
                elif event_type == "status":
                    yield f"event: status\ndata: {event_data}\n\n"
                elif event_type == "complete":
                    yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == "error":
                    yield f"event: error\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Project agent stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


@router.get("/{project_id}/agents/outputs")
async def get_project_agent_outputs(
    project_id: str,
    agent_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get all agent outputs for a project."""
    client_id = current_user.get("client_id")
    if not client_id:
        from database import get_default_client_id

        client_id = get_default_client_id()

    # Verify project access
    project = (
        supabase.table("ai_projects").select("id").eq("id", project_id).eq("client_id", client_id).single().execute()
    )
    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")

    query = (
        supabase.table("disco_outputs")
        .select(
            "id, agent_type, version, title, recommendation, confidence_level, executive_summary, content_markdown, content_structured, source_outputs, created_at, triage_suggestions"
        )
        .eq("project_id", project_id)
        .order("created_at", desc=True)
    )

    if agent_type:
        query = query.eq("agent_type", agent_type)

    result = query.execute()

    return {"success": True, "outputs": result.data or []}


@router.get("/{project_id}/agents/outputs/latest/{agent_type}")
async def get_project_agent_latest_output(
    project_id: str,
    agent_type: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get the latest output of a specific agent type for a project."""
    client_id = current_user.get("client_id")
    if not client_id:
        from database import get_default_client_id

        client_id = get_default_client_id()

    # Verify project access
    project = (
        supabase.table("ai_projects").select("id").eq("id", project_id).eq("client_id", client_id).single().execute()
    )
    if not project.data:
        raise HTTPException(status_code=404, detail="Project not found")

    result = (
        supabase.table("disco_outputs")
        .select(
            "id, agent_type, version, title, recommendation, confidence_level, executive_summary, content_markdown, content_structured, source_outputs, created_at, triage_suggestions"
        )
        .eq("project_id", project_id)
        .eq("agent_type", agent_type)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        return {"success": True, "output": None}

    return {"success": True, "output": result.data[0]}


# ============================================================================
# DOCUMENT & CHAT ENDPOINTS (for detail modal)
# ============================================================================
# NOTE: These must be defined BEFORE /{project_id} to avoid routing conflicts


@router.get("/{project_id}/related-documents", response_model=List[RelatedDocumentResponse])
async def get_project_related_documents(
    project_id: str,
    limit: int = Query(8, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get documents related to a project's scoring.

    Performs vector search using the project's context (title, description,
    current/desired state, ROI indicators) to find knowledge base documents
    that support or explain the scoring rationale.

    Documents are sorted by relevance score (highest first).
    """
    # Fetch the full project
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get scoring-relevant documents
    related_docs = get_scoring_related_documents(
        project=result.data, client_id=current_user["client_id"], limit=limit, min_similarity=0.25
    )

    return related_docs


# ============================================================================
# LINKED DOCUMENTS ENDPOINTS
# ============================================================================


@router.get("/{project_id}/documents", response_model=List[LinkedDocumentResponse])
async def get_project_linked_documents(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get documents manually linked to a project.

    Returns documents linked via the project_documents junction table,
    sorted by linked_at descending (most recent first).
    """
    if not current_user.get("client_id"):
        raise HTTPException(status_code=401, detail="User profile not found")
    # Verify project exists and belongs to client
    project_result = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get linked documents with document details
    result = (
        supabase.table("project_documents")
        .select("id, document_id, linked_at, linked_by, notes, documents(filename, title)")
        .eq("project_id", project_id)
        .order("linked_at", desc=True)
        .execute()
    )

    linked_docs = []
    for row in result.data or []:
        doc_info = row.get("documents", {}) or {}
        linked_docs.append(
            LinkedDocumentResponse(
                id=row["id"],
                document_id=row["document_id"],
                document_name=doc_info.get("filename", "Unknown"),
                title=doc_info.get("title"),
                linked_at=row["linked_at"],
                linked_by=row.get("linked_by"),
                notes=row.get("notes"),
            )
        )

    return linked_docs


@router.post("/{project_id}/documents/link")
async def link_documents_to_project(
    project_id: str,
    request: LinkDocumentsRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Link KB documents to a project.

    Creates links in the project_documents junction table.
    Duplicates are handled gracefully (upsert).
    """
    # Verify project exists and belongs to client
    project_result = (
        supabase.table("ai_projects")
        .select("id, title")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    user_id = current_user["id"]
    linked_count = 0
    errors = []

    for doc_id in request.document_ids:
        try:
            # Verify document exists
            doc_result = supabase.table("documents").select("id, filename").eq("id", doc_id).single().execute()

            if not doc_result.data:
                errors.append({"document_id": doc_id, "error": "Document not found"})
                continue

            # Create link (upsert to handle duplicates)
            supabase.table("project_documents").upsert(
                {
                    "project_id": project_id,
                    "document_id": doc_id,
                    "linked_by": user_id,
                },
                on_conflict="project_id,document_id",
            ).execute()

            linked_count += 1

        except Exception as e:
            logger.error(f"Error linking document {doc_id} to project {project_id}: {e}")
            errors.append({"document_id": doc_id, "error": str(e)})

    return {
        "success": True,
        "linked_count": linked_count,
        "errors": errors if errors else None,
    }


@router.delete("/{project_id}/documents/{document_id}")
async def unlink_document_from_project(
    project_id: str,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Unlink a document from a project.

    Removes the link from project_documents but does not delete the document from KB.
    """
    # Verify project exists and belongs to client
    project_result = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete the link
    result = (
        supabase.table("project_documents")
        .delete()
        .eq("project_id", project_id)
        .eq("document_id", document_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Document link not found")

    return {"success": True, "message": "Document unlinked from project"}


@router.get("/{project_id}/conversations", response_model=List[ConversationResponse])
async def get_project_conversation_history(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get Q&A conversation history for a project.

    Returns conversations newest first.
    """
    if not current_user.get("client_id"):
        raise HTTPException(status_code=401, detail="User profile not found")
    # Verify project exists and belongs to client
    proj = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get conversations
    conversations = await get_project_conversations(
        project_id=project_id, client_id=current_user["client_id"], limit=limit, offset=offset
    )

    return conversations


@router.post("/{project_id}/ask", response_model=AskQuestionResponse, deprecated=True)
async def ask_question_about_project(
    project_id: str,
    request: AskQuestionRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Ask a question about a project.

    DEPRECATED: Use the unified chat interface at /chat?project_id={project_id} instead.
    This endpoint will be removed in a future release.

    Uses AI to answer based on:
    - The project's details (title, description, scores, status, etc.)
    - Related documents from the knowledge base

    The conversation is stored and can be retrieved later via
    GET /{project_id}/conversations.
    """
    logger.warning(f"Deprecated endpoint /projects/{project_id}/ask called. Use /chat?project_id={project_id} instead.")
    # Verify project exists and belongs to client
    proj = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = await ask_about_project(
            project_id=project_id,
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
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error answering question about project: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question") from e


# ============================================================================
# TASKMASTER CHAT ENDPOINT
# ============================================================================


class TaskmasterChatRequest(BaseModel):
    """Request to chat with Taskmaster about a project."""

    message: str = Field(..., min_length=1, max_length=2000)


class TaskmasterChatResponse(BaseModel):
    """Response from Taskmaster chat."""

    response: str
    tasks_created: int
    task_titles: List[str]


@router.post("/{project_id}/taskmaster-chat", response_model=TaskmasterChatResponse)
async def taskmaster_chat_for_project(
    project_id: str,
    request: TaskmasterChatRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Chat with Taskmaster to break down a project into tasks.

    Taskmaster will:
    - Respond with task suggestions based on the project context
    - Extract concrete tasks from the conversation
    - Create task_candidates linked to this project
    - Tasks appear in the Discovery Inbox for review

    Only available for active projects.
    """
    # Verify project exists, belongs to client, and is active
    proj = (
        supabase.table("ai_projects")
        .select("id, project_name, status")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    if not proj.data.get("project_name") and proj.data.get("status") != "active":
        raise HTTPException(
            status_code=400,
            detail="Taskmaster is only available for active projects",
        )

    try:
        result = await chat_with_taskmaster(
            project_id=project_id,
            message=request.message,
            client_id=current_user["client_id"],
            user_id=current_user["id"],
            supabase=supabase,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error in Taskmaster chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Taskmaster chat") from e


# ============================================================================
# JUSTIFICATION GENERATION ENDPOINTS
# ============================================================================


@router.post("/{project_id}/generate-justifications")
async def generate_justifications_for_project(
    project_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Generate AI-powered justifications for a project's scores.

    Creates:
    - A 3-4 sentence project summary
    - A 3-4 sentence justification for each scoring dimension

    This is automatically called when scores are updated, but can also
    be triggered manually to regenerate justifications.
    """
    # Verify project exists and belongs to client
    proj = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        justifications = await generate_project_justifications(
            project_id=project_id, client_id=current_user["client_id"]
        )
        return {
            "message": "Justifications generated successfully",
            "justifications": justifications,
        }
    except Exception as e:
        logger.error(f"Failed to generate justifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate justifications") from e


@router.post("/generate-all-justifications")
async def generate_all_project_justifications(
    current_user: dict = Depends(get_current_user),
):
    """Generate justifications for all projects belonging to the current client.

    This is useful for backfilling justifications for existing projects
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
    """Analyze goal alignment for all projects belonging to the current client.

    Evaluates each project against IS team FY27 strategic goals:
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


@router.post("/{project_id}/analyze-goal-alignment")
async def analyze_project_goal_alignment(
    project_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Analyze a single project's alignment with IS team strategic goals.

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
    # Verify project exists and belongs to client
    proj = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        score, details = await analyze_goal_alignment(project_id=project_id, client_id=current_user["client_id"])
        return {
            "project_id": project_id,
            "goal_alignment_score": score,
            "goal_alignment_details": details,
            "level": ("high" if score >= 80 else "moderate" if score >= 60 else "low" if score >= 40 else "minimal"),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Failed to analyze goal alignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze goal alignment") from e


# ============================================================================
# SINGLE PROJECT ENDPOINTS
# ============================================================================


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)):
    """Get a single project by ID."""
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")

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

    return _format_project(result.data, owner_name)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Create a new project."""
    data = {
        "client_id": current_user["client_id"],
        "project_code": project.project_code.upper(),
        "title": project.title,
        "description": project.description,
        "department": project.department,
        "owner_stakeholder_id": project.owner_stakeholder_id,
        "current_state": project.current_state,
        "desired_state": project.desired_state,
        "roi_potential": project.roi_potential,
        "implementation_effort": project.implementation_effort,
        "strategic_alignment": project.strategic_alignment,
        "stakeholder_readiness": project.stakeholder_readiness,
        "status": project.status,
        "next_step": project.next_step,
        "blockers": project.blockers,
        "follow_up_questions": project.follow_up_questions,
        "roi_indicators": project.roi_indicators,
        "source_type": project.source_type,
        "source_id": project.source_id,
        "source_notes": project.source_notes,
        "initiative_ids": project.initiative_ids or [],
    }

    try:
        result = supabase.table("ai_projects").insert(data).execute()
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail=f"Project code {project.project_code} already exists") from None
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e

    created_proj = result.data[0]

    # Generate justifications if scores are provided
    has_scores = any(
        [
            project.roi_potential,
            project.implementation_effort,
            project.strategic_alignment,
            project.stakeholder_readiness,
        ]
    )
    if has_scores:
        try:
            await generate_project_justifications(project_id=created_proj["id"], client_id=current_user["client_id"])
            # Refetch to get updated justifications
            updated = supabase.table("ai_projects").select("*").eq("id", created_proj["id"]).single().execute()
            created_proj = updated.data
        except Exception as e:
            logger.warning(f"Failed to generate justifications on create: {e}")

    # Evaluate confidence score (fast rubric check, no AI call)
    try:
        from services.project_confidence import evaluate_project_confidence

        confidence, questions = evaluate_project_confidence(created_proj)
        supabase.table("ai_projects").update(
            {
                "scoring_confidence": confidence,
                "confidence_questions": questions,
            }
        ).eq("id", created_proj["id"]).execute()
        # Refetch to include confidence in response
        updated = supabase.table("ai_projects").select("*").eq("id", created_proj["id"]).single().execute()
        created_proj = updated.data
    except Exception as e:
        logger.warning(f"Failed to evaluate confidence on create: {e}")

    return _format_project(created_proj)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update a project."""
    # Verify ownership
    existing = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build update dict
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    if update_data.get("project_code"):
        update_data["project_code"] = update_data["project_code"].upper()

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("ai_projects").update(update_data).eq("id", project_id).execute()

    return _format_project(result.data[0])


@router.patch("/{project_id}/scores", response_model=ProjectResponse)
async def update_project_scores(
    project_id: str,
    scores: ProjectScoreUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update just the scores for a project.

    Convenience endpoint for quick score updates without touching other fields.
    Automatically regenerates justifications when scores change.
    """
    # Get existing project with current scores
    existing = (
        supabase.table("ai_projects")
        .select("id, roi_potential, implementation_effort, strategic_alignment, stakeholder_readiness")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")

    old_scores = existing.data
    update_data = {k: v for k, v in scores.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No scores to update")

    result = supabase.table("ai_projects").update(update_data).eq("id", project_id).execute()

    updated_proj = result.data[0]

    # Regenerate justifications if scores changed
    try:
        regenerated = await regenerate_if_scores_changed(
            project_id=project_id,
            old_scores=old_scores,
            new_scores=update_data,
            client_id=current_user["client_id"],
        )
        if regenerated:
            # Refetch to get updated justifications
            refreshed = supabase.table("ai_projects").select("*").eq("id", project_id).single().execute()
            updated_proj = refreshed.data
    except Exception as e:
        logger.warning(f"Failed to regenerate justifications on score update: {e}")

    return _format_project(updated_proj)


class StatusUpdateRequest(BaseModel):
    """Update project status with optional project name."""

    status: str
    next_step: Optional[str] = None
    project_name: Optional[str] = None
    project_description: Optional[str] = None


@router.patch("/{project_id}/status")
async def update_project_status(
    project_id: str,
    request: StatusUpdateRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Update project status.

    Valid statuses: backlog, active, completed, archived
    """
    valid_statuses = ["backlog", "active", "completed", "archived"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    # Verify ownership and get current data
    existing = (
        supabase.table("ai_projects")
        .select("id, project_name, status")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = {"status": request.status}
    if request.next_step is not None:
        update_data["next_step"] = request.next_step
    # Allow explicitly setting project_name (including to null for deactivation)
    if request.project_name is not None:
        update_data["project_name"] = request.project_name if request.project_name else None
    if request.project_description:
        update_data["project_description"] = request.project_description

    result = supabase.table("ai_projects").update(update_data).eq("id", project_id).execute()

    return _format_project(result.data[0])


@router.delete("/{project_id}")
async def delete_project(
    project_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Delete a project."""
    # Verify ownership
    existing = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Project not found")

    supabase.table("ai_projects").delete().eq("id", project_id).execute()

    return {"message": "Project deleted"}


# ============================================================================
# STAKEHOLDER LINK ENDPOINTS
# ============================================================================


@router.get("/{project_id}/stakeholders", response_model=List[StakeholderLinkResponse])
async def get_project_stakeholders(
    project_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Get all stakeholders linked to a project."""
    if not current_user.get("client_id"):
        raise HTTPException(status_code=401, detail="User profile not found")
    # Verify project exists and belongs to client
    proj = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get links with stakeholder info
    result = (
        supabase.table("project_stakeholder_link")
        .select("*, stakeholders(name, role, department)")
        .eq("project_id", project_id)
        .execute()
    )

    return [
        {
            "id": link["id"],
            "project_id": link["project_id"],
            "stakeholder_id": link["stakeholder_id"],
            "stakeholder_name": link["stakeholders"]["name"] if link.get("stakeholders") else None,
            "stakeholder_role": link["stakeholders"]["role"] if link.get("stakeholders") else None,
            "stakeholder_department": link["stakeholders"]["department"] if link.get("stakeholders") else None,
            "role": link["role"],
            "notes": link.get("notes"),
            "created_at": link["created_at"],
        }
        for link in result.data
    ]


@router.post("/{project_id}/stakeholders", response_model=StakeholderLinkResponse)
async def link_stakeholder_to_project(
    project_id: str,
    link: StakeholderLinkCreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Link a stakeholder to a project."""
    # Verify project exists
    proj = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

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
            supabase.table("project_stakeholder_link")
            .insert(
                {
                    "project_id": project_id,
                    "stakeholder_id": link.stakeholder_id,
                    "role": link.role,
                    "notes": link.notes,
                }
            )
            .execute()
        )
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Stakeholder already linked to this project") from None
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e

    return {
        "id": result.data[0]["id"],
        "project_id": project_id,
        "stakeholder_id": link.stakeholder_id,
        "stakeholder_name": stakeholder.data["name"],
        "stakeholder_role": stakeholder.data.get("role"),
        "stakeholder_department": stakeholder.data.get("department"),
        "role": link.role,
        "notes": link.notes,
        "created_at": result.data[0]["created_at"],
    }


@router.delete("/{project_id}/stakeholders/{stakeholder_id}")
async def unlink_stakeholder_from_project(
    project_id: str,
    stakeholder_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Remove a stakeholder link from a project."""
    # Verify project exists
    proj = (
        supabase.table("ai_projects")
        .select("id")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not proj.data:
        raise HTTPException(status_code=404, detail="Project not found")

    supabase.table("project_stakeholder_link").delete().eq("project_id", project_id).eq(
        "stakeholder_id", stakeholder_id
    ).execute()

    return {"message": "Stakeholder unlinked from project"}


# ============================================================================
# PROJECT CANDIDATES ENDPOINTS
# ============================================================================


class ProjectCandidateResponse(BaseModel):
    """Project candidate response model."""

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
    matched_project_id: Optional[str]
    match_confidence: Optional[float]
    match_reason: Optional[str]
    created_at: str


class ProjectCandidateAccept(BaseModel):
    """Accept a project candidate, optionally overriding fields."""

    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    roi_potential: Optional[int] = Field(None, ge=1, le=5)
    implementation_effort: Optional[int] = Field(None, ge=1, le=5)
    strategic_alignment: Optional[int] = Field(None, ge=1, le=5)
    stakeholder_readiness: Optional[int] = Field(None, ge=1, le=5)
    link_to_existing: bool = False  # If true, link source to existing project instead of creating new


class ProjectCandidateReject(BaseModel):
    """Reject a project candidate with reason."""

    reason: Optional[str] = None


@router.get("/candidates/list", response_model=List[ProjectCandidateResponse])
async def list_project_candidates(
    status: str = "pending",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """List project candidates for review.

    Candidates are extracted from meeting documents and await user review
    before becoming real projects.
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
            "matched_project_id": c.get("matched_project_id"),
            "match_confidence": c.get("match_confidence"),
            "match_reason": c.get("match_reason"),
            "created_at": c["created_at"],
        }
        for c in result.data
    ]


@router.get("/candidates/count")
async def get_project_candidates_count(current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)):
    """Get count of pending project candidates.

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


@router.post("/candidates/{candidate_id}/accept", response_model=ProjectResponse)
async def accept_project_candidate(
    candidate_id: str,
    accept_data: ProjectCandidateAccept = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Accept a project candidate, creating a new project.

    If the candidate has a matched_project_id and link_to_existing is True,
    the source document will be linked to the existing project instead
    of creating a new one.
    """
    if accept_data is None:
        accept_data = ProjectCandidateAccept()

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

    # If linking to existing project
    if accept_data.link_to_existing and cand.get("matched_project_id"):
        # Just update the existing project's source_notes with this new info
        existing_proj = (
            supabase.table("ai_projects").select("*").eq("id", cand["matched_project_id"]).single().execute()
        )

        if existing_proj.data:
            # Append source info to notes
            existing_notes = existing_proj.data.get("source_notes") or ""
            new_notes = f"{existing_notes}\n\nLinked from: {cand.get('source_document_name', 'Document')}\nQuote: {cand.get('source_text', '')[:200]}"

            supabase.table("ai_projects").update({"source_notes": new_notes.strip()}).eq(
                "id", cand["matched_project_id"]
            ).execute()

            # Mark candidate as accepted
            supabase.table("project_candidates").update(
                {
                    "status": "accepted",
                    "accepted_at": now,
                    "accepted_by": current_user["id"],
                    "created_project_id": cand["matched_project_id"],
                }
            ).eq("id", candidate_id).execute()

            return _format_project(existing_proj.data)

    # Create new project
    dept = accept_data.department or cand.get("department") or "General"
    dept_prefix = dept[0].upper() if dept else "G"

    # Get next project code using RPC (avoids PostgREST ilike issues)
    try:
        existing_codes = supabase.rpc(
            "count_project_codes_by_prefix",
            {"p_client_id": current_user["client_id"], "p_prefix": dept_prefix},
        ).execute()
        code_count = existing_codes.data[0].get("code_count", 0) if existing_codes.data else 0
    except Exception as rpc_err:
        logger.warning(f"RPC count_project_codes_by_prefix failed: {rpc_err}")
        code_count = 0

    next_num = code_count + 1
    proj_code = f"{dept_prefix}{next_num:02d}"

    proj_data = {
        "client_id": current_user["client_id"],
        "project_code": proj_code,
        "title": accept_data.title or cand["title"],
        "description": accept_data.description or cand.get("description"),
        "department": dept,
        "roi_potential": accept_data.roi_potential or cand.get("suggested_roi_potential") or 3,
        "implementation_effort": accept_data.implementation_effort or cand.get("suggested_effort") or 3,
        "strategic_alignment": accept_data.strategic_alignment or cand.get("suggested_alignment") or 3,
        "stakeholder_readiness": accept_data.stakeholder_readiness or cand.get("suggested_readiness") or 3,
        "status": "backlog",
        "source_type": "meeting",
        "source_id": cand.get("source_document_id"),
        "source_notes": cand.get("source_text"),
        "created_at": now,
    }

    try:
        result = supabase.table("ai_projects").insert(proj_data).execute()
        new_proj = result.data[0]

        # Mark candidate as accepted
        supabase.table("project_candidates").update(
            {
                "status": "accepted",
                "accepted_at": now,
                "accepted_by": current_user["id"],
                "created_project_id": new_proj["id"],
            }
        ).eq("id", candidate_id).execute()

        # Generate justifications for the new project
        try:
            await generate_project_justifications(project_id=new_proj["id"], client_id=current_user["client_id"])
            # Refetch to get updated justifications
            updated = supabase.table("ai_projects").select("*").eq("id", new_proj["id"]).single().execute()
            new_proj = updated.data
        except Exception as e:
            logger.warning(f"Failed to generate justifications for accepted candidate: {e}")

        return _format_project(new_proj)

    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Project code already exists") from e
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/candidates/{candidate_id}/reject")
async def reject_project_candidate(
    candidate_id: str,
    reject_data: ProjectCandidateReject = None,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Reject a project candidate.

    Optionally provide a reason for rejection.
    """
    if reject_data is None:
        reject_data = ProjectCandidateReject()

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


class LinkProjectCandidateRequest(BaseModel):
    """Request body for linking a candidate to an existing project."""

    project_id: str


@router.post("/candidates/{candidate_id}/link")
async def link_project_candidate(
    candidate_id: str,
    body: LinkProjectCandidateRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Link a project candidate to an existing project instead of creating a new one.

    This is used when a duplicate is detected and the user wants to associate
    the candidate's context with an existing project rather than creating a new one.
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

    # Verify target project exists
    proj_result = (
        supabase.table("ai_projects")
        .select("id, title, project_name, description")
        .eq("id", body.project_id)
        .eq("client_id", client_id)
        .single()
        .execute()
    )

    if not proj_result.data:
        raise HTTPException(status_code=404, detail="Target project not found")

    project = proj_result.data

    # Append candidate context to the existing project's description
    existing_desc = project.get("description") or ""
    candidate_source = candidate.get("source_document_name") or ""
    candidate_quote = candidate.get("source_text") or ""

    if candidate_source or candidate_quote:
        linked_note = f"\n\n---\nLinked from: {candidate_source}"
        if candidate_quote:
            linked_note += f'\nQuote: "{candidate_quote[:200]}..."'
        new_description = existing_desc + linked_note

        supabase.table("ai_projects").update({"description": new_description}).eq("id", body.project_id).execute()

    # Mark candidate as accepted with reference to the linked project
    now = datetime.now(timezone.utc).isoformat()
    supabase.table("project_candidates").update(
        {
            "status": "accepted",
            "created_project_id": body.project_id,
            "accepted_at": now,
            "accepted_by": user_id,
        }
    ).eq("id", candidate_id).execute()

    logger.info(f"Project candidate {candidate_id} linked to existing project {body.project_id}")

    return {
        "success": True,
        "linked_project_id": body.project_id,
        "linked_project_title": project.get("title") or project.get("project_name"),
        "message": "Linked to existing project",
    }


# ============================================================================
# CONFIDENCE EVALUATION ENDPOINTS
# ============================================================================


@router.post("/evaluate-confidence")
async def evaluate_all_confidence(
    current_user: dict = Depends(get_current_user),
):
    """Evaluate confidence scores for all projects.

    Uses a rubric based on information completeness:
    - 80-100%: High confidence - scores well-supported
    - 60-79%: Moderate confidence - some assumptions
    - 40-59%: Low confidence - significant unknowns
    - 0-39%: Very low confidence - mostly speculative

    Returns distribution and average confidence.
    """
    from services.project_confidence import evaluate_all_projects

    try:
        result = await evaluate_all_projects(current_user["client_id"])
        return result
    except Exception as e:
        logger.error(f"Failed to evaluate confidence: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{project_id}/evaluate-confidence")
async def evaluate_single_confidence(
    project_id: str, current_user: dict = Depends(get_current_user), supabase=Depends(get_supabase)
):
    """Evaluate and update confidence score for a single project."""
    from services.project_confidence import evaluate_project_confidence

    # Fetch project
    result = (
        supabase.table("ai_projects")
        .select("*")
        .eq("id", project_id)
        .eq("client_id", current_user["client_id"])
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")

    project = result.data

    # Evaluate confidence
    confidence, questions = evaluate_project_confidence(project)

    # Update in database
    supabase.table("ai_projects").update(
        {
            "scoring_confidence": confidence,
            "confidence_questions": questions,
        }
    ).eq("id", project_id).execute()

    return {
        "project_id": project_id,
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


# ============================================================================
# KRAKEN ENDPOINTS - Task Evaluation & Autonomous Execution
# ============================================================================


@router.post("/{project_id}/kraken/evaluate")
async def kraken_evaluate_tasks(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Phase 1: Evaluate project tasks for agentic workability. Returns SSE stream."""
    client_id = current_user.get("client_id")
    if not client_id:
        # Fall back to default client
        from database import get_default_client_id

        client_id = get_default_client_id()

    async def event_stream():
        try:
            async for event in evaluate_project_tasks(
                project_id=project_id,
                client_id=client_id,
                user_id=current_user["id"],
                supabase=supabase,
            ):
                event_type = event.get("type", "unknown")
                event_data = event.get("data", "")

                if isinstance(event_data, dict):
                    yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
                else:
                    yield f"event: {event_type}\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Kraken evaluation stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


@router.post("/{project_id}/kraken/execute")
async def kraken_execute_tasks(
    project_id: str,
    body: KrakenExecuteRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Phase 2: Execute approved tasks. Returns SSE stream."""
    client_id = current_user.get("client_id")
    if not client_id:
        from database import get_default_client_id

        client_id = get_default_client_id()

    async def event_stream():
        try:
            async for event in execute_approved_tasks(
                project_id=project_id,
                task_ids=body.task_ids,
                client_id=client_id,
                user_id=current_user["id"],
                supabase=supabase,
            ):
                event_type = event.get("type", "unknown")
                event_data = event.get("data", "")

                if isinstance(event_data, dict):
                    yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
                else:
                    yield f"event: {event_type}\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Kraken execution stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


@router.get("/{project_id}/kraken/evaluation")
async def kraken_get_evaluation(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    """Get stored evaluation results for a project."""
    client_id = current_user.get("client_id")
    if not client_id:
        from database import get_default_client_id

        client_id = get_default_client_id()

    result = await get_kraken_evaluation(project_id, client_id, supabase)

    if not result:
        return {"evaluation": None, "agenticity_score": None, "is_stale": False}

    return result
