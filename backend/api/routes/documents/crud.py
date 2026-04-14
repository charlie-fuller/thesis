"""Document CRUD routes - get, delete, download, process."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

import pb_client as pb
from document_processor import process_document
from logger_config import get_logger
from repositories import documents as doc_repo
from validation import validate_uuid

from ._shared import limiter

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{document_id}/process")
async def process_document_endpoint(
    document_id: str,
    background_tasks: BackgroundTasks,
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
):
    """Get document metadata."""
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"success": True, "document": document}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
):
    """Get document content by reconstructing from chunks."""
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        chunks = doc_repo.list_document_chunks(document_id)

        if chunks:
            content = "\n\n".join(chunk["content"] for chunk in chunks)
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
            "chunk_count": len(chunks),
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
):
    """Delete a document and all its chunks.

    Args:
        request: FastAPI request object for rate limiting.
        document_id: UUID of document to delete.
        check_only: If True, only check for DISCo links without deleting.
    """
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check for DISCo initiative links
        disco_links = []
        try:
            links = pb.get_all(
                "disco_initiative_documents",
                filter=f"document_id='{pb.escape_filter(document_id)}'",
            )
            for link in links:
                initiative = pb.get_record("disco_initiatives", link["initiative_id"])
                if initiative:
                    disco_links.append(
                        {
                            "initiative_id": link["initiative_id"],
                            "initiative_name": initiative["name"],
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
                links_to_delete = pb.get_all(
                    "disco_initiative_documents",
                    filter=f"document_id='{pb.escape_filter(document_id)}'",
                )
                for link in links_to_delete:
                    pb.delete_record("disco_initiative_documents", link["id"])
                logger.info(f"Removed {len(disco_links)} DISCo initiative links for document {document_id}")
            except Exception as e:
                logger.warning(f"Could not delete DISCo links: {e}")

        # Delete vectors from Pinecone before deleting chunks
        try:
            chunks_for_pc = doc_repo.list_document_chunks(document_id)
            if chunks_for_pc:
                pc_ids = [str(c["id"]) for c in chunks_for_pc]
                from services.pinecone_service import delete_vectors

                delete_vectors(ids=pc_ids, namespace="document_chunks")
        except Exception as e:
            logger.warning(f"Could not delete Pinecone vectors: {e}")

        # Delete chunks
        chunks = doc_repo.list_document_chunks(document_id)
        for chunk in chunks:
            doc_repo.delete_document_chunk(chunk["id"])

        # Delete from storage -- PocketBase file storage TBD
        if document.get("storage_path"):
            try:
                # TODO: PocketBase file storage migration pending
                logger.info(f"Skipping storage delete (PocketBase migration pending): {document['storage_path']}")
            except Exception as e:
                logger.warning(f"Could not delete from storage: {e}")

        # Delete document record
        doc_repo.delete_document(document_id)

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
):
    """Delete multiple documents."""
    try:
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
                for doc_id in valid_doc_ids:
                    # Delete chunks first
                    chunks = doc_repo.list_document_chunks(doc_id)
                    for chunk in chunks:
                        doc_repo.delete_document_chunk(chunk["id"])
                    # Delete document
                    doc_repo.delete_document(doc_id)

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
):
    """Generate a signed URL for document download."""
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # TODO: PocketBase file storage migration pending
        # PocketBase has its own file URL generation mechanism
        raise HTTPException(
            status_code=501,
            detail="Document download not yet available (PocketBase storage migration pending)",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/{document_id}/initiative-links")
async def get_document_initiative_links(
    document_id: str,
):
    """Get DISCo initiatives that link to this document."""
    try:
        validate_uuid(document_id, "document_id")

        document = doc_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        links = pb.get_all(
            "disco_initiative_documents",
            filter=f"document_id='{pb.escape_filter(document_id)}'",
        )

        initiatives = []
        for link in links:
            initiative = pb.get_record("disco_initiatives", link["initiative_id"])
            if initiative:
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
