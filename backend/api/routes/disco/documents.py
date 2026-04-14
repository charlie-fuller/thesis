"""DISCo Documents routes."""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

import pb_client as pb
from logger_config import get_logger
from repositories import disco as disco_repo
from services.disco import (
    delete_document,
    get_document,
    get_documents,
    upload_document,
    upload_document_file,
)

from ._shared import (
    DocumentUploadText,
    LinkDocumentsRequest,
    LinkFolderRequest,
    require_initiative_access,
)

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# DOCUMENTS
# ============================================================================


@router.get("/initiatives/{initiative_id}/documents")
async def api_list_documents(
    initiative_id: str,
    document_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List documents in an initiative."""
    require_initiative_access(initiative_id)

    try:
        result = await get_documents(
            initiative_id=initiative_id,
            document_type=document_type,
            limit=limit,
            offset=offset,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/documents")
async def api_upload_document_file(
    initiative_id: str,
    file: UploadFile = File(...),
):
    """Upload a file document."""
    require_initiative_access(initiative_id)

    logger.info(f"[DISCO-DOC] Upload started: {file.filename}, content_type: {file.content_type}")

    try:
        file_data = await file.read()
        logger.info(f"[DISCO-DOC] File read complete: {len(file_data)} bytes")

        document = await upload_document_file(
            initiative_id=initiative_id,
            file_data=file_data,
            filename=file.filename,
        )
        logger.info(f"[DISCO-DOC] Upload successful: {document.get('id')}")
        return {"success": True, "document": document}
    except ValueError as e:
        logger.warning(f"[DISCO-DOC] Upload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"[DISCO-DOC] Upload failed: {type(e).__name__}: {e}")
        import traceback

        logger.error(f"[DISCO-DOC] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/documents/text")
async def api_upload_document_text(
    initiative_id: str,
    data: DocumentUploadText,
):
    """Upload a text document (for pasting content)."""
    require_initiative_access(initiative_id)

    try:
        document = await upload_document(
            initiative_id=initiative_id,
            filename=data.filename,
            content=data.content,
            document_type=data.document_type,
        )
        return {"success": True, "document": document}
    except Exception as e:
        logger.error(f"Error uploading text document: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/documents/{document_id}")
async def api_get_document(
    initiative_id: str,
    document_id: str,
):
    """Get a document by ID."""
    require_initiative_access(initiative_id)

    try:
        document = await get_document(document_id, initiative_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"success": True, "document": document}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/documents/{document_id}")
async def api_delete_document(
    initiative_id: str,
    document_id: str,
):
    """Delete a document."""
    require_initiative_access(initiative_id)

    try:
        await delete_document(document_id, initiative_id)
        return {"success": True, "message": "Document deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# KB DOCUMENT LINKING
# ============================================================================


@router.post("/initiatives/{initiative_id}/documents/link")
async def api_link_kb_documents(
    initiative_id: str,
    data: LinkDocumentsRequest,
):
    """Link existing KB documents to an initiative.

    Creates links in disco_initiative_documents table and auto-tags
    the KB documents with the initiative name.
    """
    require_initiative_access(initiative_id)

    try:
        if not data.document_ids:
            raise HTTPException(status_code=400, detail="At least one document_id is required")

        # Get initiative name for auto-tagging
        initiative = disco_repo.get_initiative(initiative_id)
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")

        initiative_name = initiative["name"]

        linked_documents = []
        errors = []

        logger.info(f"[DISCO] Linking {len(data.document_ids)} documents to initiative {initiative_id}")

        for doc_id in data.document_ids:
            try:
                # Verify document exists
                doc = pb.get_record("documents", doc_id)
                if not doc:
                    logger.warning(f"[DISCO] Document {doc_id} not found")
                    errors.append({"document_id": doc_id, "error": "Document not found"})
                    continue

                # Create link in junction table (upsert via get_first + create/update)
                esc_init = pb.escape_filter(initiative_id)
                esc_doc = pb.escape_filter(doc_id)
                existing_link = pb.get_first(
                    "disco_initiative_documents",
                    filter=f"initiative_id='{esc_init}' && document_id='{esc_doc}'",
                )
                if not existing_link:
                    pb.create_record("disco_initiative_documents", {
                        "initiative_id": initiative_id,
                        "document_id": doc_id,
                    })

                # Auto-tag document with initiative name
                esc_tag = pb.escape_filter(initiative_name)
                existing_tag = pb.get_first(
                    "document_tags",
                    filter=f"document_id='{esc_doc}' && tag='{esc_tag}'",
                )
                if not existing_tag:
                    pb.create_record("document_tags", {
                        "document_id": doc_id,
                        "tag": initiative_name,
                        "source": "initiative",
                    })

                linked_documents.append(
                    {
                        "id": doc_id,
                        "filename": doc.get("filename"),
                        "title": doc.get("title"),
                    }
                )
                logger.debug(f"[DISCO] Successfully linked document {doc_id}")

            except Exception as e:
                logger.error(f"[DISCO] Error linking document {doc_id}: {e}")
                errors.append({"document_id": doc_id, "error": str(e)})

        logger.info(
            f"[DISCO] Linked {len(linked_documents)} of {len(data.document_ids)} docs to initiative {initiative_id}"
        )

        return {
            "success": True,
            "linked_count": len(linked_documents),
            "documents": linked_documents,
            "errors": errors if errors else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking KB documents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/linked-documents")
async def api_get_linked_kb_documents(
    initiative_id: str,
):
    """Get KB documents linked to this initiative.

    Returns documents from the main KB that have been linked to this initiative
    via the disco_initiative_documents junction table.
    """
    # Resolve to UUID and check access
    resolved_id = require_initiative_access(initiative_id)

    try:
        # Get linked document IDs from junction table
        esc_id = pb.escape_filter(resolved_id)
        links = pb.get_all(
            "disco_initiative_documents",
            filter=f"initiative_id='{esc_id}'",
            sort="-created",
        )

        if not links:
            return {"success": True, "documents": [], "count": 0}

        # Get document details for all linked IDs
        doc_ids = [link["document_id"] for link in links]
        # Build OR filter for all doc IDs
        or_parts = [f"id='{pb.escape_filter(did)}'" for did in doc_ids]
        or_filter = " || ".join(or_parts)
        docs = pb.get_all("documents", filter=f"({or_filter})")

        # Build a lookup map for documents
        docs_map = {doc["id"]: doc for doc in docs}

        # Combine link info with document info
        linked_documents = []
        for link in links:
            doc_id = link["document_id"]
            doc = docs_map.get(doc_id)
            if doc:
                linked_documents.append(
                    {
                        "id": doc["id"],
                        "filename": doc.get("filename") or "Unknown",
                        "title": doc.get("title"),
                        "uploaded_at": doc.get("uploaded_at"),
                        "source_platform": doc.get("source_platform"),
                        "linked_at": link.get("created"),
                        "linked_by": link.get("linked_by"),
                    }
                )
            else:
                # Document was deleted but link remains
                logger.warning(f"[DISCO] Linked document {doc_id} not found (may have been deleted)")
                linked_documents.append(
                    {
                        "id": doc_id,
                        "filename": "[Document deleted]",
                        "title": None,
                        "uploaded_at": link.get("created"),
                        "source_platform": None,
                        "linked_at": link.get("created"),
                        "linked_by": link.get("linked_by"),
                    }
                )

        return {
            "success": True,
            "documents": linked_documents,
            "count": len(linked_documents),
        }

    except Exception as e:
        logger.error(f"Error getting linked KB documents: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/linked-documents/{document_id}")
async def api_unlink_kb_document(
    initiative_id: str,
    document_id: str,
):
    """Unlink a KB document from this initiative.

    Removes the link from disco_initiative_documents but does not delete the document.
    """
    require_initiative_access(initiative_id)

    try:
        esc_init = pb.escape_filter(initiative_id)
        esc_doc = pb.escape_filter(document_id)
        records = pb.get_all(
            "disco_initiative_documents",
            filter=f"initiative_id='{esc_init}' && document_id='{esc_doc}'",
        )
        for record in records:
            pb.delete_record("disco_initiative_documents", record["id"])

        logger.info(f"[DISCO] Unlinked document {document_id} from initiative {initiative_id}")

        return {"success": True, "message": "Document unlinked from initiative"}

    except Exception as e:
        logger.error(f"Error unlinking document: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# FOLDER LINKING (Auto-link subscriptions)
# ============================================================================


@router.post("/initiatives/{initiative_id}/folders/link")
async def api_link_folder(
    initiative_id: str,
    data: LinkFolderRequest,
):
    """Link a vault folder to an initiative.

    New documents synced into this folder will be automatically linked.
    Optionally backfills existing documents in the folder.
    """
    resolved_id = require_initiative_access(initiative_id)

    try:
        folder_path = data.folder_path.strip().strip("/")

        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path is required")

        # Upsert folder link
        disco_repo.link_folder(resolved_id, folder_path, recursive=data.recursive)

        logger.info(f"[DISCO] Linked folder '{folder_path}' to initiative {resolved_id} (recursive={data.recursive})")

        backfilled = 0

        # Backfill: link existing documents in this folder
        if data.backfill:
            # Get initiative name for auto-tagging
            initiative = disco_repo.get_initiative(resolved_id)
            initiative_name = initiative["name"] if initiative else None

            # Find documents in this folder
            esc_path = pb.escape_filter(folder_path)
            docs = pb.get_all(
                "documents",
                filter=f"obsidian_file_path~'{esc_path}/'",
            )

            for doc in docs:
                doc_id = doc["id"]
                doc_path = doc.get("obsidian_file_path", "")

                # For non-recursive, verify the doc is directly in the folder
                if not data.recursive and doc_path:
                    remainder = doc_path[len(folder_path) + 1:]
                    if "/" in remainder:
                        continue  # Skip - this is in a subfolder

                try:
                    # Link document to initiative (upsert)
                    esc_init = pb.escape_filter(resolved_id)
                    esc_doc = pb.escape_filter(doc_id)
                    existing_link = pb.get_first(
                        "disco_initiative_documents",
                        filter=f"initiative_id='{esc_init}' && document_id='{esc_doc}'",
                    )
                    if not existing_link:
                        pb.create_record("disco_initiative_documents", {
                            "initiative_id": resolved_id,
                            "document_id": doc_id,
                        })

                    # Auto-tag
                    if initiative_name:
                        esc_tag = pb.escape_filter(initiative_name)
                        existing_tag = pb.get_first(
                            "document_tags",
                            filter=f"document_id='{esc_doc}' && tag='{esc_tag}'",
                        )
                        if not existing_tag:
                            pb.create_record("document_tags", {
                                "document_id": doc_id,
                                "tag": initiative_name,
                                "source": "initiative",
                            })

                    backfilled += 1
                except Exception as e:
                    logger.warning(f"[DISCO] Failed to backfill document {doc_id}: {e}")

            logger.info(f"[DISCO] Backfilled {backfilled} documents from folder '{folder_path}'")

        return {
            "success": True,
            "folder_path": folder_path,
            "recursive": data.recursive,
            "backfilled_count": backfilled,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking folder: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/linked-folders")
async def api_get_linked_folders(
    initiative_id: str,
):
    """Get folders linked to this initiative."""
    resolved_id = require_initiative_access(initiative_id)

    try:
        folders = disco_repo.get_initiative_folders(resolved_id)

        return {
            "success": True,
            "folders": folders,
            "count": len(folders),
        }

    except Exception as e:
        logger.error(f"Error getting linked folders: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/linked-folders/{folder_path:path}")
async def api_unlink_folder(
    initiative_id: str,
    folder_path: str,
):
    """Unlink a folder from this initiative.

    Removes the folder subscription but keeps existing document links intact.
    """
    resolved_id = require_initiative_access(initiative_id)

    try:
        esc_init = pb.escape_filter(resolved_id)
        esc_path = pb.escape_filter(folder_path)
        records = pb.get_all(
            "disco_initiative_folders",
            filter=f"initiative_id='{esc_init}' && folder_path='{esc_path}'",
        )
        for record in records:
            pb.delete_record("disco_initiative_folders", record["id"])

        logger.info(f"[DISCO] Unlinked folder '{folder_path}' from initiative {resolved_id}")

        return {"success": True, "message": f"Folder '{folder_path}' unlinked from initiative"}

    except Exception as e:
        logger.error(f"Error unlinking folder: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
