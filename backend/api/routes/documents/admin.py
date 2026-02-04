"""Document admin routes - listing, details, cleanup."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from auth import require_admin
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()


@router.get("/")
async def list_all_documents(
    current_user: dict = Depends(require_admin),
    limit: int = 50,
    offset: int = 0,
):
    """List all documents (admin only).

    Args:
        current_user: Injected by FastAPI dependency.
        limit: Maximum documents to return.
        offset: Pagination offset.
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("*, clients(name), users!documents_user_id_fkey(email)")
            .order("uploaded_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        return {"success": True, "documents": result.data, "limit": limit, "offset": offset}

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}/details")
async def get_document_details(
    document_id: str,
    current_user: dict = Depends(require_admin),
):
    """Get detailed document information including chunks (admin only).

    Args:
        document_id: UUID of the document.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("*").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        chunks_result = await asyncio.to_thread(
            lambda: supabase.table("document_chunks")
            .select("id, chunk_index, content")
            .eq("document_id", document_id)
            .order("chunk_index")
            .execute()
        )

        return {
            "success": True,
            "document": doc_result.data,
            "chunks": chunks_result.data,
            "chunk_count": len(chunks_result.data),
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
    current_user: dict = Depends(require_admin),
    limit: int = 100,
):
    """Find documents whose obsidian_file_path contains the given pattern (admin only).

    Use this to identify documents that should be cleaned up, e.g., from node_modules.

    Args:
        pattern: Substring to search for in obsidian_file_path (e.g., "node_modules").
        current_user: Injected by FastAPI dependency.
        limit: Maximum number of documents to return (default 100).
    """
    try:
        if not pattern or len(pattern) < 3:
            raise HTTPException(status_code=400, detail="Pattern must be at least 3 characters")

        result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, title, obsidian_file_path, uploaded_at")
            .ilike("obsidian_file_path", f"%{pattern}%")
            .limit(limit)
            .execute()
        )

        documents = result.data or []
        doc_ids = [d["id"] for d in documents]

        # Batch fetch all tags for the documents in a single query
        tags_by_doc = {}
        if doc_ids:
            tags_result = await asyncio.to_thread(
                lambda: supabase.table("document_tags").select("document_id, tag").in_("document_id", doc_ids).execute()
            )
            for tag_record in tags_result.data or []:
                doc_id = tag_record["document_id"]
                if doc_id not in tags_by_doc:
                    tags_by_doc[doc_id] = []
                tags_by_doc[doc_id].append(tag_record["tag"])

        # Attach tags to each document
        for doc in documents:
            doc["tags"] = tags_by_doc.get(doc["id"], [])

        # Get total count (may be more than limit)
        count_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id", count="exact")
            .ilike("obsidian_file_path", f"%{pattern}%")
            .execute()
        )

        return {
            "success": True,
            "pattern": pattern,
            "total_count": count_result.count,
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
    current_user: dict = Depends(require_admin),
    dry_run: bool = True,
):
    """Delete documents whose obsidian_file_path contains the given pattern (admin only).

    Tags are automatically deleted via CASCADE when documents are deleted.

    Args:
        pattern: Substring to search for in obsidian_file_path (e.g., "node_modules").
        current_user: Injected by FastAPI dependency.
        dry_run: If True (default), only report what would be deleted without deleting.
    """
    try:
        if not pattern or len(pattern) < 3:
            raise HTTPException(status_code=400, detail="Pattern must be at least 3 characters")

        result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, obsidian_file_path")
            .ilike("obsidian_file_path", f"%{pattern}%")
            .execute()
        )

        documents = result.data or []
        doc_ids = [d["id"] for d in documents]

        # Batch fetch all tags for affected documents in a single query
        affected_tags = set()
        if doc_ids:
            tags_result = await asyncio.to_thread(
                lambda: supabase.table("document_tags").select("tag").in_("document_id", doc_ids).execute()
            )
            for t in tags_result.data or []:
                affected_tags.add(t["tag"])

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "pattern": pattern,
                "would_delete_count": len(documents),
                "affected_tags": sorted(affected_tags),
                "documents": [
                    {"id": d["id"], "filename": d["filename"], "path": d["obsidian_file_path"]} for d in documents[:50]
                ],
                "message": (f"Would delete {len(documents)} documents. Set dry_run=false to actually delete."),
            }

        # Actually delete using batch operations
        deleted_count = 0
        errors = []

        if doc_ids:
            try:
                # Batch delete chunks for all documents
                await asyncio.to_thread(
                    lambda: supabase.table("document_chunks").delete().in_("document_id", doc_ids).execute()
                )

                # Batch delete documents (tags deleted via CASCADE)
                await asyncio.to_thread(lambda: supabase.table("documents").delete().in_("id", doc_ids).execute())

                deleted_count = len(doc_ids)

            except Exception as e:
                errors.append({"batch": True, "error": str(e)})

        logger.info(f"Deleted {deleted_count} documents matching pattern '{pattern}' by admin {current_user['id']}")

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
