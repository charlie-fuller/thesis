"""Shared models and utilities for DISCo routes."""

import asyncio
from typing import List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger
from services.disco import check_permission

logger = get_logger(__name__)
supabase = get_supabase()


# ============================================================================
# REQUEST/RESPONSE MODELS - INITIATIVES
# ============================================================================


class InitiativeCreate(BaseModel):
    """Create a new initiative."""

    name: str
    description: Optional[str] = None


class InitiativeUpdate(BaseModel):
    """Update an existing initiative."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


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


class BundleApproval(BaseModel):
    """Request body for approving/rejecting a bundle."""

    feedback: Optional[str] = None


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


async def require_initiative_access(initiative_id: str, current_user: dict, required_role: str = "viewer") -> bool:
    """Check user has access to initiative."""
    has_permission = await check_permission(initiative_id, current_user["id"], required_role)
    if not has_permission:
        raise HTTPException(status_code=403, detail=f"Insufficient permissions. Required: {required_role}")
    return True
