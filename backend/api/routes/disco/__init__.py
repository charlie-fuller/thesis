"""DISCo API Routes Package.

Discovery-Insights-Synthesis-Capabilities (DISCo) API endpoints.
Organized into focused modules for better maintainability.
"""

from fastapi import APIRouter

from . import admin, chat, documents, initiatives, synthesis, workflow
from ._shared import (
    AgentRunRequest,
    BundleApproval,
    BundleCreate,
    BundleMerge,
    BundleSplit,
    BundleUpdate,
    ChatQuestion,
    CheckpointApprove,
    CheckpointReset,
    DocumentUploadText,
    ExtractedField,
    ExtractedScore,
    ExtractProjectResponse,
    InitiativeCreate,
    InitiativeUpdate,
    LinkDocumentsRequest,
    MemberInvite,
    MemberRoleUpdate,
    PRDUpdate,
    check_disco_access,
    require_disco_access,
    require_initiative_access,
)

router = APIRouter(prefix="/api/disco", tags=["disco"])

# Include all sub-routers
router.include_router(initiatives.router)
router.include_router(documents.router)
router.include_router(workflow.router)
router.include_router(synthesis.router)
router.include_router(chat.router)
router.include_router(admin.router)

__all__ = [
    "router",
    # Models
    "InitiativeCreate",
    "InitiativeUpdate",
    "DocumentUploadText",
    "LinkDocumentsRequest",
    "MemberInvite",
    "MemberRoleUpdate",
    "ChatQuestion",
    "AgentRunRequest",
    "CheckpointApprove",
    "CheckpointReset",
    "BundleCreate",
    "BundleUpdate",
    "BundleApproval",
    "BundleMerge",
    "BundleSplit",
    "PRDUpdate",
    "ExtractedField",
    "ExtractedScore",
    "ExtractProjectResponse",
    # Auth helpers
    "check_disco_access",
    "require_disco_access",
    "require_initiative_access",
]
