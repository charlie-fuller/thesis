"""Shared models and utilities for DISCo routes."""

import asyncio
from typing import List, Literal, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger
from services.disco import check_permission

logger = get_logger(__name__)
supabase = get_supabase()


# ============================================================================
# REQUEST/RESPONSE MODELS - INITIATIVES
# ============================================================================


# ============================================================================
# THROUGHLINE MODELS
# ============================================================================


class ProblemStatement(BaseModel):
    """A problem statement in the throughline."""

    id: Optional[str] = None
    text: str


class Hypothesis(BaseModel):
    """A hypothesis to validate through discovery."""

    id: Optional[str] = None
    statement: str
    rationale: Optional[str] = None
    type: Optional[str] = "assumption"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ("assumption", "belief", "prediction"):
            return "assumption"
        return v


class Gap(BaseModel):
    """A known gap to investigate."""

    id: Optional[str] = None
    description: str
    type: Optional[str] = "data"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ("data", "people", "process", "capability"):
            return "data"
        return v


class Throughline(BaseModel):
    """Structured input framing for an initiative."""

    problem_statements: Optional[List[ProblemStatement]] = None
    hypotheses: Optional[List[Hypothesis]] = None
    gaps: Optional[List[Gap]] = None
    desired_outcome_state: Optional[str] = None


class HypothesisResolution(BaseModel):
    """Resolution of a hypothesis after convergence."""

    hypothesis_id: str
    status: str  # confirmed, refuted, inconclusive
    evidence_summary: Optional[str] = None


class GapStatus(BaseModel):
    """Status of a gap after convergence."""

    gap_id: str
    status: str  # addressed, unaddressed, partially_addressed
    findings: Optional[str] = None


class StateChange(BaseModel):
    """A recommended state change from convergence."""

    description: str
    owner: Optional[str] = None
    deadline: Optional[str] = None


class SoWhat(BaseModel):
    """The 'So What?' synthesis from convergence."""

    state_change_proposed: Optional[str] = None
    next_human_action: Optional[str] = None
    kill_test: Optional[str] = None


class ThroughlineResolution(BaseModel):
    """Structured resolution from the convergence stage."""

    hypothesis_resolutions: Optional[List[HypothesisResolution]] = None
    gap_statuses: Optional[List[GapStatus]] = None
    state_changes: Optional[List[StateChange]] = None
    so_what: Optional[SoWhat] = None


class CreateTasksFromResolution(BaseModel):
    """Request to create tasks from throughline resolution state changes."""

    output_id: str
    project_id: Optional[str] = None
    selected_indices: Optional[List[int]] = None


class ValueAlignment(BaseModel):
    """Flexible value alignment for a discovery."""

    kpis: Optional[List[str]] = None
    department_goals: Optional[List[str]] = None
    company_priority: Optional[str] = None
    strategic_pillar: Optional[Literal["enable", "operationalize", "govern"]] = None
    notes: Optional[str] = None


VALID_INITIATIVE_VERDICTS = {"proceed", "defer", "accept", "no_action"}


class ResolutionAnnotations(BaseModel):
    """User annotations on hypothesis/gap resolutions and initiative verdict."""

    hypothesis_overrides: Optional[dict] = None  # { "h-1": { status, note } }
    gap_overrides: Optional[dict] = None  # { "g-2": { status, note } }
    initiative_verdict: Optional[str] = None  # proceed, defer, accept, no_action
    defer_until: Optional[str] = None  # date or quarter (e.g., "2026-Q3")
    accept_rationale: Optional[str] = None  # why accepting is the right choice

    @field_validator("initiative_verdict")
    @classmethod
    def validate_verdict(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_INITIATIVE_VERDICTS:
            raise ValueError(f"initiative_verdict must be one of: {', '.join(sorted(VALID_INITIATIVE_VERDICTS))}")
        return v


class InitiativeCreate(BaseModel):
    """Create a new discovery (initiative)."""

    name: str
    description: Optional[str] = None
    throughline: Optional[Throughline] = None
    target_department: Optional[str] = None
    value_alignment: Optional[ValueAlignment] = None
    sponsor_stakeholder_id: Optional[str] = None
    stakeholder_ids: Optional[List[str]] = None


class InitiativeUpdate(BaseModel):
    """Update an existing discovery (initiative)."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    throughline: Optional[Throughline] = None
    target_department: Optional[str] = None
    value_alignment: Optional[ValueAlignment] = None
    sponsor_stakeholder_id: Optional[str] = None
    stakeholder_ids: Optional[List[str]] = None
    resolution_annotations: Optional[ResolutionAnnotations] = None


# ============================================================================
# REQUEST/RESPONSE MODELS - DOCUMENTS
# ============================================================================


class DocumentUploadText(BaseModel):
    """Upload document as text."""

    filename: str
    content: str
    document_type: str = "uploaded"


class LinkDocumentsRequest(BaseModel):
    """Request body for linking KB documents to an initiative."""

    document_ids: List[str]


class LinkFolderRequest(BaseModel):
    """Request body for linking a vault folder to an initiative."""

    folder_path: str
    recursive: bool = True
    backfill: bool = True


# ============================================================================
# REQUEST/RESPONSE MODELS - MEMBERS
# ============================================================================


class MemberInvite(BaseModel):
    """Invite a member to initiative."""

    email: EmailStr
    role: str = "viewer"


class MemberRoleUpdate(BaseModel):
    """Update member role."""

    role: str


# ============================================================================
# REQUEST/RESPONSE MODELS - CHAT
# ============================================================================


class ChatQuestion(BaseModel):
    """Ask a question in chat."""

    question: str
    conversation_id: Optional[str] = None


# ============================================================================
# REQUEST/RESPONSE MODELS - AGENTS
# ============================================================================


class AgentRunRequest(BaseModel):
    """Request to run an agent."""

    agent_type: str
    document_ids: Optional[List[str]] = None
    output_format: Optional[str] = "comprehensive"
    multi_pass: Optional[bool] = False
    kb_folder: Optional[str] = None
    kb_tags: Optional[List[str]] = None


# ============================================================================
# REQUEST/RESPONSE MODELS - CHECKPOINTS
# ============================================================================


class CheckpointApprove(BaseModel):
    """Request body for approving a checkpoint."""

    notes: Optional[str] = None
    checklist_items: Optional[List[dict]] = None


class CheckpointReset(BaseModel):
    """Request body for resetting a checkpoint."""

    reason: Optional[str] = None


# ============================================================================
# REQUEST/RESPONSE MODELS - BUNDLES (Synthesis)
# ============================================================================


VALID_SOLUTION_TYPES = {"build", "buy", "govern", "coordinate", "train", "restructure", "document", "defer", "accept"}


class BundleCreate(BaseModel):
    """Request body for creating a bundle."""

    name: str
    description: str
    impact_score: Optional[str] = None
    impact_rationale: Optional[str] = None
    feasibility_score: Optional[str] = None
    feasibility_rationale: Optional[str] = None
    urgency_score: Optional[str] = None
    urgency_rationale: Optional[str] = None
    complexity_tier: Optional[str] = None
    complexity_rationale: Optional[str] = None
    included_items: Optional[List[dict]] = None
    stakeholders: Optional[List[dict]] = None
    dependencies: Optional[dict] = None
    bundling_rationale: Optional[str] = None
    solution_type: Optional[str] = None

    @field_validator("solution_type")
    @classmethod
    def validate_solution_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_SOLUTION_TYPES:
            raise ValueError(f"solution_type must be one of: {', '.join(sorted(VALID_SOLUTION_TYPES))}")
        return v


class BundleUpdate(BaseModel):
    """Request body for updating a bundle."""

    name: Optional[str] = None
    description: Optional[str] = None
    impact_score: Optional[str] = None
    impact_rationale: Optional[str] = None
    feasibility_score: Optional[str] = None
    feasibility_rationale: Optional[str] = None
    urgency_score: Optional[str] = None
    urgency_rationale: Optional[str] = None
    complexity_tier: Optional[str] = None
    complexity_rationale: Optional[str] = None
    included_items: Optional[List[dict]] = None
    stakeholders: Optional[List[dict]] = None
    dependencies: Optional[dict] = None
    bundling_rationale: Optional[str] = None
    feedback: Optional[str] = None
    solution_type: Optional[str] = None

    @field_validator("solution_type")
    @classmethod
    def validate_solution_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_SOLUTION_TYPES:
            raise ValueError(f"solution_type must be one of: {', '.join(sorted(VALID_SOLUTION_TYPES))}")
        return v


class BundleApproval(BaseModel):
    """Request body for approving/rejecting a bundle."""

    feedback: Optional[str] = None
    output_type: str = Field(
        default="prd", description="Output type: prd, evaluation_framework, decision_framework, assessment"
    )


class BundleMerge(BaseModel):
    """Request body for merging bundles."""

    bundle_ids: List[str]
    merged_name: str
    merged_description: str
    feedback: Optional[str] = None


class BundleSplit(BaseModel):
    """Request body for splitting a bundle."""

    split_definitions: List[dict]
    feedback: Optional[str] = None


# ============================================================================
# REQUEST/RESPONSE MODELS - PRDs (Capabilities)
# ============================================================================


class PRDUpdate(BaseModel):
    """Request body for updating a PRD."""

    content_markdown: Optional[str] = None
    status: Optional[str] = None


# ============================================================================
# REQUEST/RESPONSE MODELS - PROJECT EXTRACTION
# ============================================================================


class ExtractedField(BaseModel):
    """A field extracted from chat with confidence level."""

    value: Optional[str] = None
    confidence: str = Field(default="none", description="Confidence level: high, medium, low, none")


class ExtractedScore(BaseModel):
    """A numeric score (1-5) extracted from chat with confidence level."""

    value: Optional[int] = None
    confidence: str = Field(default="none", description="Confidence level: high, medium, low, none")


class ExtractProjectResponse(BaseModel):
    """Response from project extraction endpoint."""

    title: ExtractedField
    description: ExtractedField
    department: ExtractedField
    current_state: ExtractedField
    desired_state: ExtractedField
    roi_potential: ExtractedScore
    implementation_effort: ExtractedScore
    strategic_alignment: ExtractedScore
    stakeholder_readiness: ExtractedScore
    source_context: str = Field(description="Formatted chat excerpt for source_notes")


# ============================================================================
# AUTH HELPERS
# ============================================================================


async def check_disco_access(user: dict) -> bool:
    """Check if user has DISCo access."""
    user_id = user.get("id")
    if not user_id:
        return False

    result = await asyncio.to_thread(
        lambda: supabase.table("users").select("app_access").eq("id", user_id).single().execute()
    )

    if not result.data:
        return False

    app_access = result.data.get("app_access", ["thesis"])
    return "disco" in app_access or "purdy" in app_access or "all" in app_access


async def require_disco_access(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency to require DISCo access."""
    has_access = await check_disco_access(current_user)
    if not has_access:
        raise HTTPException(status_code=403, detail="DISCo access required")
    return current_user


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        from uuid import UUID

        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


async def resolve_initiative_id(initiative_id: str) -> str:
    """Resolve an initiative ID (UUID or name) to its UUID.

    Args:
        initiative_id: Either a UUID or initiative name

    Returns:
        The initiative's UUID

    Raises:
        HTTPException: If initiative not found
    """
    if _is_valid_uuid(initiative_id):
        return initiative_id

    # Look up by name
    result = await asyncio.to_thread(
        lambda: supabase.table("disco_initiatives").select("id").eq("name", initiative_id).single().execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Initiative not found")

    return result.data["id"]


async def require_initiative_access(initiative_id: str, current_user: dict, required_role: str = "viewer") -> str:
    """Check user has access to initiative.

    Returns:
        The resolved initiative UUID (useful when input was a name)
    """
    # Resolve to UUID if needed
    resolved_id = await resolve_initiative_id(initiative_id)

    has_permission = await check_permission(resolved_id, current_user["id"], required_role)
    if not has_permission:
        raise HTTPException(status_code=403, detail=f"Insufficient permissions. Required: {required_role}")
    return resolved_id
