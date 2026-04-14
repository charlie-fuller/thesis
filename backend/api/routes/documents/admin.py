"""Document admin routes - listing, details, cleanup."""

from fastapi import APIRouter, HTTPException

import pb_client as pb
from logger_config import get_logger
from repositories import documents as doc_repo
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_all_documents(
    limit: int = 50,
    offset: int = 0,
):
    """List all documents (admin only).

    Args:
        limit: Maximum documents to return.
        offset: Pagination offset.
    """
    try:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "documents",
            sort="-uploaded_at",
            page=page,
            per_page=limit,
        )
        documents = result.get("items", [])

        return {"success": True, "documents": documents, "limit": limit, "offset": offset}

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}/details")
async def get_document_details(
    document_id: str,
):
    """Get detailed document information including chunks (admin only).

    Args:
        document_id: UUID of the document.
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        chunks = doc_repo.list_document_chunks(document_id)

        return {
            "success": True,
            "document": document,
            "chunks": chunks,
            "chunk_count": len(chunks),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document details: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# CLEANUP BY PATH PATTERN
# ============================================================================


@router.get("/cleanup/by-path")
async def find_documents_by_path_pattern(
    pattern: str,
    limit: int = 100,
):
    """Find documents whose obsidian_file_path contains the given pattern (admin only).

    Use this to identify documents that should be cleaned up, e.g., from node_modules.

    Args:
        pattern: Substring to search for in obsidian_file_path (e.g., "node_modules").
        limit: Maximum number of documents to return (default 100).
    """
    try:
        if not pattern or len(pattern) < 3:
            raise HTTPException(status_code=400, detail="Pattern must be at least 3 characters")

        result = pb.list_records(
            "documents",
            filter=f"obsidian_file_path~'{pb.escape_filter(pattern)}'",
            per_page=limit,
        )
        documents = result.get("items", [])
        doc_ids = [d["id"] for d in documents]

        # Fetch tags for each document
        tags_by_doc = {}
        for doc_id in doc_ids:
            tags = doc_repo.list_document_tags(doc_id)
            tags_by_doc[doc_id] = [t["tag"] for t in tags]

        # Attach tags to each document
        for doc in documents:
            doc["tags"] = tags_by_doc.get(doc["id"], [])

        # Get total count
        total_count = pb.count(
            "documents",
            filter=f"obsidian_file_path~'{pb.escape_filter(pattern)}'",
        )

        return {
            "success": True,
            "pattern": pattern,
            "total_count": total_count,
            "returned_count": len(documents),
            "documents": documents,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding documents by path pattern: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/cleanup/by-path")
async def delete_documents_by_path_pattern(
    pattern: str,
    dry_run: bool = True,
):
    """Delete documents whose obsidian_file_path contains the given pattern (admin only).

    Tags are automatically deleted via CASCADE when documents are deleted.

    Args:
        pattern: Substring to search for in obsidian_file_path (e.g., "node_modules").
        dry_run: If True (default), only report what would be deleted without deleting.
    """
    try:
        if not pattern or len(pattern) < 3:
            raise HTTPException(status_code=400, detail="Pattern must be at least 3 characters")

        documents = pb.get_all(
            "documents",
            filter=f"obsidian_file_path~'{pb.escape_filter(pattern)}'",
        )
        doc_ids = [d["id"] for d in documents]

        # Fetch all tags for affected documents
        affected_tags = set()
        for doc_id in doc_ids:
            tags = doc_repo.list_document_tags(doc_id)
            for t in tags:
                affected_tags.add(t["tag"])

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "pattern": pattern,
                "would_delete_count": len(documents),
                "affected_tags": sorted(affected_tags),
                "documents": [
                    {"id": d["id"], "filename": d.get("filename"), "path": d.get("obsidian_file_path")}
                    for d in documents[:50]
                ],
                "message": (f"Would delete {len(documents)} documents. Set dry_run=false to actually delete."),
            }

        # Actually delete
        deleted_count = 0
        errors = []

        if doc_ids:
            try:
                for doc_id in doc_ids:
                    # Delete chunks first
                    chunks = doc_repo.list_document_chunks(doc_id)
                    for chunk in chunks:
                        doc_repo.delete_document_chunk(chunk["id"])
                    # Delete document (tags should cascade)
                    doc_repo.delete_document(doc_id)

                deleted_count = len(doc_ids)

            except Exception as e:
                errors.append({"batch": True, "error": str(e)})

        logger.info(f"Deleted {deleted_count} documents matching pattern '{pattern}'")

        return {
            "success": True,
            "dry_run": False,
            "pattern": pattern,
            "deleted_count": deleted_count,
            "affected_tags": sorted(affected_tags),
            "errors": errors if errors else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting documents by path pattern: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
