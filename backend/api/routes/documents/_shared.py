"""Shared utilities and models for document routes."""

import asyncio
from typing import List, Optional

from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()


# ============================================================================
# UTILITIES
# ============================================================================


async def retry_supabase_operation(operation, max_retries: int = 3, base_delay: float = 0.5):
    """Retry a Supabase operation with exponential backoff.

    Handles transient connection errors like ConnectionTerminated that occur
    with rapid successive requests to Supabase.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return await asyncio.to_thread(operation)
        except Exception as e:
            error_str = str(e)
            if "ConnectionTerminated" in error_str or "RemoteProtocolError" in error_str:
                last_error = e
                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Supabase connection error (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay}s: {error_str}"
                )
                await asyncio.sleep(delay)
            else:
                raise
    raise last_error


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
