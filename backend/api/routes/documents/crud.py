"""Document CRUD routes - get, delete, download, process."""

import asyncio
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from auth import check_owner_or_admin, get_current_user
from database import get_supabase
from document_processor import process_document
from logger_config import get_logger
from validation import validate_uuid

from ._shared import limiter, retry_supabase_operation

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()


@router.post("/{document_id}/process")
async def process_document_endpoint(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Trigger document processing (chunking and embedding)."""
    try:
        validate_uuid(document_id, "document_id")
        background_tasks.add_task(process_document, document_id)

        return {
            "success": True,
            "message": "Document processing started",
            "document_id": document_id,
        }

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}")
async def get_document_metadata(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get document metadata."""
    try:
        validate_uuid(document_id, "document_id")

        result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("*").eq("id", document_id).single().execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        return {"success": True, "document": document}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get document content by reconstructing from chunks."""
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, title, mime_type, uploaded_by, storage_path")
            .eq("id", document_id)
            .single()
            .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        chunks_result = await asyncio.to_thread(
            lambda: supabase.table("document_chunks")
            .select("content, chunk_index")
            .eq("document_id", document_id)
            .order("chunk_index")
            .execute()
        )

        if chunks_result.data:
            content = "\n\n".join(chunk["content"] for chunk in chunks_result.data)
        else:
            content = ""

        return {
            "success": True,
            "document": {
                "id": document["id"],
                "filename": document.get("filename"),
                "title": document.get("title"),
                "mime_type": document.get("mime_type"),
            },
            "content": content,
            "chunk_count": len(chunks_result.data) if chunks_result.data else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document content: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/{document_id}")
@limiter.limit("30/minute")
async def delete_document(
    request: Request,
    document_id: str,
    check_only: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Delete a document and all its chunks.

    Args:
        request: FastAPI request object for rate limiting.
        document_id: UUID of document to delete.
        check_only: If True, only check for DISCo links without deleting.
        current_user: Injected by FastAPI dependency.
    """
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await retry_supabase_operation(
            lambda: supabase.table("documents").select("*").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        # Check for DISCo initiative links
        disco_links = []
        try:
            links_result = await retry_supabase_operation(
                lambda: supabase.table("disco_initiative_documents")
                .select("initiative_id, disco_initiatives(id, name)")
                .eq("document_id", document_id)
                .execute()
            )
            if links_result.data:
                for link in links_result.data:
                    if link.get("disco_initiatives"):
                        disco_links.append(
                            {
                                "initiative_id": link["initiative_id"],
                                "initiative_name": link["disco_initiatives"]["name"],
                            }
                        )
        except Exception as e:
            logger.debug(f"Could not check DISCo links: {e}")

        if check_only:
            return {
                "success": True,
                "document_id": document_id,
                "filename": document.get("filename"),
                "disco_initiatives": disco_links,
                "has_disco_usage": len(disco_links) > 0,
            }

        # Delete DISCo initiative links
        if disco_links:
            try:
                await retry_supabase_operation(
                    lambda: supabase.table("disco_initiative_documents")
                    .delete()
                    .eq("document_id", document_id)
                    .execute()
                )
                logger.info(f"Removed {len(disco_links)} DISCo initiative links for document {document_id}")
            except Exception as e:
                logger.warning(f"Could not delete DISCo links: {e}")

        # Delete chunks
        await retry_supabase_operation(
            lambda: supabase.table("document_chunks").delete().eq("document_id", document_id).execute()
        )

        # Delete from storage
        if document.get("storage_path"):
            try:
                await retry_supabase_operation(
                    lambda: supabase.storage.from_("documents").remove([document["storage_path"]])
                )
            except Exception as e:
                logger.warning(f"Could not delete from storage: {e}")

        # Delete document record
        await retry_supabase_operation(lambda: supabase.table("documents").delete().eq("id", document_id).execute())

        logger.info(f"Document deleted: {document_id}")

        return {
            "success": True,
            "message": "Document deleted successfully",
            "disco_initiatives_unlinked": disco_links if disco_links else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/bulk")
@limiter.limit("10/minute")
async def bulk_delete_documents(
    request: Request,
    document_ids: List[str],
    current_user: dict = Depends(get_current_user),
):
    """Delete multiple documents."""
    try:
        # Check admin role
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        # Validate all UUIDs first
        valid_doc_ids = []
        errors = []
        for doc_id in document_ids:
            try:
                validate_uuid(doc_id, "document_id")
                valid_doc_ids.append(doc_id)
            except Exception as e:
                errors.append({"document_id": doc_id, "error": str(e)})

        deleted_count = 0
        if valid_doc_ids:
            try:
                # Batch delete chunks for all documents
                await asyncio.to_thread(
                    lambda: supabase.table("document_chunks").delete().in_("document_id", valid_doc_ids).execute()
                )

                # Batch delete documents
                await asyncio.to_thread(lambda: supabase.table("documents").delete().in_("id", valid_doc_ids).execute())

                deleted_count = len(valid_doc_ids)

            except Exception as e:
                errors.append({"batch": True, "error": str(e)})

        return {"success": True, "deleted_count": deleted_count, "errors": errors}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk delete error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Generate a signed URL for document download."""
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("*").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        signed_url = await asyncio.to_thread(
            lambda: supabase.storage.from_("documents").create_signed_url(document["storage_path"], 3600)
        )

        return {
            "success": True,
            "download_url": signed_url["signedURL"],
            "expires_in": 3600,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}/initiative-links")
async def get_document_initiative_links(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get DISCo initiatives that link to this document."""
    try:
        validate_uuid(document_id, "document_id")

        doc_result = await asyncio.to_thread(
            lambda: supabase.table("documents").select("id, uploaded_by").eq("id", document_id).single().execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data
        check_owner_or_admin(current_user, document["uploaded_by"], "document")

        links_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_documents")
            .select("initiative_id, disco_initiatives(id, name, status)")
            .eq("document_id", document_id)
            .execute()
        )

        initiatives = []
        for link in links_result.data or []:
            if link.get("disco_initiatives"):
                initiative = link["disco_initiatives"]
                initiatives.append(
                    {
                        "id": initiative["id"],
                        "name": initiative["name"],
                        "status": initiative.get("status", "unknown"),
                    }
                )

        return {
            "success": True,
            "document_id": document_id,
            "linked": len(initiatives) > 0,
            "initiatives": initiatives,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document initiative links: {e}")
        return {
            "success": True,
            "document_id": document_id,
            "linked": False,
            "initiatives": [],
        }
