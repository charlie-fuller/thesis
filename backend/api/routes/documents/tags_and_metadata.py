"""Document tags and metadata routes."""

from fastapi import APIRouter, HTTPException

import pb_client as pb
from logger_config import get_logger
from repositories import documents as doc_repo
from validation import validate_uuid

from ._shared import AddTagRequest, OriginalDateUpdate, SyncCadenceUpdate

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# DOCUMENT TAGS
# ============================================================================


@router.get("/{document_id}/tags")
async def get_document_tags(
    document_id: str,
):
    """Get all tags for a document.

    Args:
        document_id: UUID of the document.

    Returns:
        tags: List of tag objects with tag name and source (frontmatter/manual).
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        tags = doc_repo.list_document_tags(document_id)

        return {"success": True, "document_id": document_id, "tags": tags}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/{document_id}/tags")
async def add_document_tag(
    document_id: str,
    request: AddTagRequest,
):
    """Add a manual tag to a document.

    Args:
        document_id: UUID of the document.
        request: Contains the tag text to add.
    """
    try:
        validate_uuid(document_id, "document_id")

        if not request.tag or not request.tag.strip():
            raise HTTPException(status_code=400, detail="Tag cannot be empty")

        tag = request.tag.strip()
        if len(tag) > 100:
            raise HTTPException(status_code=400, detail="Tag must be 100 characters or less")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if tag already exists
        existing = pb.get_first(
            "document_tags",
            filter=f"document_id='{pb.escape_filter(document_id)}' && tag='{pb.escape_filter(tag)}'",
        )

        if existing:
            logger.info(f"Tag '{tag}' already exists on document {document_id}")
            return {
                "success": True,
                "document_id": document_id,
                "tag": existing,
                "already_exists": True,
            }

        # Insert new tag
        new_tag = doc_repo.create_document_tag(
            {"document_id": document_id, "tag": tag, "source": "manual"}
        )

        logger.info(f"Added tag '{tag}' to document {document_id}")

        return {
            "success": True,
            "document_id": document_id,
            "tag": new_tag,
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
):
    """Remove a tag from a document.

    Note: Only manual tags can be removed. Frontmatter tags are controlled by
    the source Obsidian file.

    Args:
        document_id: UUID of the document.
        tag: The tag text to remove.
    """
    try:
        validate_uuid(document_id, "document_id")

        if not tag or not tag.strip():
            raise HTTPException(status_code=400, detail="Tag cannot be empty")

        tag = tag.strip()

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if tag exists and is manual
        existing_tag = pb.get_first(
            "document_tags",
            filter=f"document_id='{pb.escape_filter(document_id)}' && tag='{pb.escape_filter(tag)}'",
        )

        if not existing_tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        if existing_tag.get("source") == "frontmatter":
            raise HTTPException(
                status_code=400,
                detail="Cannot remove frontmatter tags. Edit the source Obsidian file instead.",
            )

        # Delete the tag
        doc_repo.delete_document_tag(existing_tag["id"])

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
):
    """Update the original date for a document (e.g., meeting date for transcripts).

    Args:
        document_id: UUID of the document.
        request: Contains original_date in YYYY-MM-DD format, or null to clear.
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

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

        doc_repo.update_document(document_id, {"original_date": parsed_date})

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
):
    """Update the sync cadence for a document (for Google Drive documents).

    Args:
        document_id: UUID of the document.
        request: Contains sync_cadence - manual, daily, weekly, or monthly.
    """
    try:
        validate_uuid(document_id, "document_id")

        valid_cadences = ["manual", "daily", "weekly", "monthly"]
        if request.sync_cadence not in valid_cadences:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sync_cadence. Must be one of: {', '.join(valid_cadences)}",
            )

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_repo.update_document(document_id, {"sync_cadence": request.sync_cadence})

        logger.info(f"Updated sync_cadence for document {document_id}: {request.sync_cadence}")

        return {"success": True, "document_id": document_id, "sync_cadence": request.sync_cadence}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document sync_cadence: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
