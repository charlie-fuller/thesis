"""Document routes package - modular organization of document management endpoints."""

from fastapi import APIRouter

from . import admin, agents_and_classification, crud, search, tags_and_metadata, upload
from ._shared import (
    AddTagRequest,
    BatchTagsRequest,
    BulkTagsRequest,
    ConfirmClassificationRequest,
    OriginalDateUpdate,
    SaveFromChatRequest,
    SyncCadenceUpdate,
    UpdateDocumentAgentsRequest,
    limiter,
)

# Create main router with prefix and tags
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Include sub-routers in a specific order:
# 1. Static routes first (admin root, upload, search, cleanup paths)
# 2. Parameterized routes last (to avoid route conflicts)

# Admin routes (includes GET "" for list all, and /cleanup/by-path)
router.include_router(admin.router)

# Upload routes (/upload, /save-from-chat)
router.include_router(upload.router)

# Search routes (/tags, /search, /by-folder, /batch-tags, /bulk-tags)
router.include_router(search.router)

# CRUD routes (/{document_id}, /{document_id}/content, /{document_id}/process, etc.)
router.include_router(crud.router)

# Agent and classification routes (/{document_id}/agents, /{document_id}/classification)
router.include_router(agents_and_classification.router)

# Tags and metadata routes (/{document_id}/tags, /{document_id}/original-date, etc.)
router.include_router(tags_and_metadata.router)

# Export shared utilities for external use
__all__ = [
    "router",
    "limiter",
    "SaveFromChatRequest",
    "BatchTagsRequest",
    "BulkTagsRequest",
    "UpdateDocumentAgentsRequest",
    "ConfirmClassificationRequest",
    "AddTagRequest",
    "OriginalDateUpdate",
    "SyncCadenceUpdate",
]
