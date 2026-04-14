"""Shared utilities and models for document routes."""

from typing import List, Optional

from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from logger_config import get_logger

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class SaveFromChatRequest(BaseModel):
    """Request body for saving a chat response to the knowledge base."""

    title: str
    content: str
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None


class ExportToKBRequest(BaseModel):
    """Request body for exporting content to KB with optional project/initiative linking."""

    title: str
    content: str
    location: Optional[str] = None  # Virtual folder path for organization
    project_id: Optional[str] = None
    initiative_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None


class BatchTagsRequest(BaseModel):
    """Request body for fetching tags for multiple documents."""

    document_ids: List[str]


class BulkTagsRequest(BaseModel):
    """Request body for bulk tag operations."""

    document_ids: List[str]
    tags: List[str]
    operation: str  # 'add' or 'remove'


class UpdateDocumentAgentsRequest(BaseModel):
    """Request body for updating document agent assignments."""

    agent_ids: List[str]


class ConfirmClassificationRequest(BaseModel):
    """Request body for confirming/modifying document classification."""

    agent_ids: List[str]
    relevance_scores: Optional[dict] = None


class AddTagRequest(BaseModel):
    """Request body for adding a tag to a document."""

    tag: str


class OriginalDateUpdate(BaseModel):
    """Request body for updating document original date."""

    original_date: Optional[str] = None


class SyncCadenceUpdate(BaseModel):
    """Request body for updating document sync cadence."""

    sync_cadence: str
