"""Document tags and metadata routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from auth import check_owner_or_admin, get_current_user
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

from ._shared import AddTagRequest, OriginalDateUpdate, SyncCadenceUpdate

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()


# ============================================================================
# DOCUMENT TAGS
# ============================================================================


@router.get("/{document_id}/tags")
async def get_document_tags(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get all tags for a document.

    Args:
        document_id: UUID of the document.
        current_user: Injected by FastAPI dependency.

    Returns:
        tags: List of tag objects with tag name and source (frontmatter/manual).
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        tags_result = await asyncio.to_thread(
            lambda: supabase.table("document_tags")
            .select("id, tag, source, created_at")
            .eq("document_id", document_id)
            .order("created_at")
            .execute()
        )

        return {"success": True, "document_id": document_id, "tags": tags_result.data or []}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{document_id}/tags")
async def add_document_tag(
    document_id: str,
    request: AddTagRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a manual tag to a document.

    Args:
        document_id: UUID of the document.
        request: Contains the tag text to add.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        if not request.tag or not request.tag.strip():
            raise HTTPException(status_code=400, detail="Tag cannot be empty")

        tag = request.tag.strip()
        if len(tag) > 100:
            raise HTTPException(status_code=400, detail="Tag must be 100 characters or less")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        # Check if tag already exists
        existing = await asyncio.to_thread(
            lambda: supabase.table("document_tags")
            .select("id, tag, source")
            .eq("document_id", document_id)
            .eq("tag", tag)
            .execute()
        )

        if existing.data:
            logger.info(f"Tag '{tag}' already exists on document {document_id}")
            return {
                "success": True,
                "document_id": document_id,
                "tag": existing.data[0],
                "already_exists": True,
            }

        # Insert new tag
        tag_result = await asyncio.to_thread(
            lambda: supabase.table("document_tags")
            .insert({"document_id": document_id, "tag": tag, "source": "manual"})
            .execute()
        )

        logger.info(f"Added tag '{tag}' to document {document_id}: {tag_result.data}")

        return {
            "success": True,
            "document_id": document_id,
            "tag": tag_result.data[0] if tag_result.data else {"tag": tag, "source": "manual"},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding document tag: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{document_id}/tags/{tag}")
async def remove_document_tag(
    document_id: str,
    tag: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove a tag from a document.

    Note: Only manual tags can be removed. Frontmatter tags are controlled by
    the source Obsidian file.

    Args:
        document_id: UUID of the document.
        tag: The tag text to remove.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        if not tag or not tag.strip():
            raise HTTPException(status_code=400, detail="Tag cannot be empty")

        tag = tag.strip()

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        # Check if tag exists and is manual
        existing_tag = await asyncio.to_thread(
            lambda: supabase.table("document_tags")
            .select("id, source")
            .eq("document_id", document_id)
            .eq("tag", tag)
            .single()
            .execute()
        )

        if not existing_tag.data:
            raise HTTPException(status_code=404, detail="Tag not found")

        if existing_tag.data["source"] == "frontmatter":
            raise HTTPException(
                status_code=400,
                detail="Cannot remove frontmatter tags. Edit the source Obsidian file instead.",
            )

        # Delete the tag
        await asyncio.to_thread(
            lambda: supabase.table("document_tags").delete().eq("document_id", document_id).eq("tag", tag).execute()
        )

        logger.info(f"Removed tag '{tag}' from document {document_id}")

        return {"success": True, "document_id": document_id, "removed_tag": tag}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing document tag: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# DOCUMENT METADATA
# ============================================================================


@router.patch("/{document_id}/original-date")
async def update_document_original_date(
    document_id: str,
    request: OriginalDateUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update the original date for a document (e.g., meeting date for transcripts).

    Args:
        document_id: UUID of the document.
        request: Contains original_date in YYYY-MM-DD format, or null to clear.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        # Validate and parse date if provided
        parsed_date = None
        if request.original_date and request.original_date.strip():
            try:
                from datetime import datetime

                parsed_date = datetime.strptime(request.original_date.strip(), "%Y-%m-%d").date().isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Please use YYYY-MM-DD format."
                ) from None

        await asyncio.to_thread(
            lambda: supabase.table("documents").update({"original_date": parsed_date}).eq("id", document_id).execute()
        )

        logger.info(f"Updated original_date for document {document_id}: {parsed_date}")

        return {"success": True, "document_id": document_id, "original_date": parsed_date}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document original_date: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/{document_id}/sync-cadence")
async def update_document_sync_cadence(
    document_id: str,
    request: SyncCadenceUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update the sync cadence for a document (for Google Drive documents).

    Args:
        document_id: UUID of the document.
        request: Contains sync_cadence - manual, daily, weekly, or monthly.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        valid_cadences = ["manual", "daily", "weekly", "monthly"]
        if request.sync_cadence not in valid_cadences:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sync_cadence. Must be one of: {', '.join(valid_cadences)}",
            )

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, uploaded_by, source_platform")
            .eq("id", document_id)
            .single()
            .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        await asyncio.to_thread(
            lambda: supabase.table("documents")
            .update({"sync_cadence": request.sync_cadence})
            .eq("id", document_id)
            .execute()
        )

        logger.info(f"Updated sync_cadence for document {document_id}: {request.sync_cadence}")

        return {"success": True, "document_id": document_id, "sync_cadence": request.sync_cadence}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document sync_cadence: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
