"""DISCo Documents routes."""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from database import get_supabase
from logger_config import get_logger
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
    require_disco_access,
    require_initiative_access,
)

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()


# ============================================================================
# DOCUMENTS
# ============================================================================


@router.get("/initiatives/{initiative_id}/documents")
async def api_list_documents(
    initiative_id: str,
    document_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_disco_access),
):
    """List documents in an initiative."""
    await require_initiative_access(initiative_id, current_user, "viewer")

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
    current_user: dict = Depends(require_disco_access),
):
    """Upload a file document."""
    await require_initiative_access(initiative_id, current_user, "editor")

    logger.info(f"[DISCO-DOC] Upload started: {file.filename}, content_type: {file.content_type}")

    try:
        file_data = await file.read()
        logger.info(f"[DISCO-DOC] File read complete: {len(file_data)} bytes")

        document = await upload_document_file(
            initiative_id=initiative_id,
            file_data=file_data,
            filename=file.filename,
            user_id=current_user["id"],
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
    current_user: dict = Depends(require_disco_access),
):
    """Upload a text document (for pasting content)."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        document = await upload_document(
            initiative_id=initiative_id,
            filename=data.filename,
            content=data.content,
            user_id=current_user["id"],
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
    current_user: dict = Depends(require_disco_access),
):
    """Get a document by ID."""
    await require_initiative_access(initiative_id, current_user, "viewer")

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
    current_user: dict = Depends(require_disco_access),
):
    """Delete a document."""
    await require_initiative_access(initiative_id, current_user, "editor")

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
    current_user: dict = Depends(require_disco_access),
):
    """Link existing KB documents to an initiative.

    Creates links in disco_initiative_documents table and auto-tags
    the KB documents with the initiative name.
    """
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        if not data.document_ids:
            raise HTTPException(status_code=400, detail="At least one document_id is required")

        # Get initiative name for auto-tagging
        initiative_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiatives").select("id, name").eq("id", initiative_id).single().execute()
        )

        if not initiative_result.data:
            raise HTTPException(status_code=404, detail="Initiative not found")

        initiative_name = initiative_result.data["name"]
        user_id = current_user["id"]

        linked_documents = []
        errors = []

        logger.info(f"[DISCO] Linking {len(data.document_ids)} documents to initiative {initiative_id}")

        for doc_id in data.document_ids:
            try:
                # Verify document exists
                doc_result = await asyncio.to_thread(
                    lambda d=doc_id: supabase.table("documents")
                    .select("id, filename, title, uploaded_by")
                    .eq("id", d)
                    .single()
                    .execute()
                )

                if not doc_result.data:
                    logger.warning(f"[DISCO] Document {doc_id} not found")
                    errors.append({"document_id": doc_id, "error": "Document not found"})
                    continue

                # Log ownership for debugging
                doc_owner = doc_result.data.get("uploaded_by")
                if doc_owner != user_id:
                    logger.info(f"[DISCO] User {user_id} linking document {doc_id} owned by {doc_owner}")

                # Create link in junction table (upsert to handle duplicates)
                link_result = await asyncio.to_thread(
                    lambda d=doc_id: supabase.table("disco_initiative_documents")
                    .upsert(
                        {
                            "initiative_id": initiative_id,
                            "document_id": d,
                            "linked_by": user_id,
                        },
                        on_conflict="initiative_id,document_id",
                    )
                    .execute()
                )

                if not link_result.data:
                    logger.warning(f"[DISCO] Failed to create link for document {doc_id}")

                # Auto-tag document with initiative name
                await asyncio.to_thread(
                    lambda d=doc_id: supabase.table("document_tags")
                    .upsert(
                        {
                            "document_id": d,
                            "tag": initiative_name,
                            "source": "initiative",
                        },
                        on_conflict="document_id,tag",
                    )
                    .execute()
                )

                linked_documents.append(
                    {
                        "id": doc_id,
                        "filename": doc_result.data.get("filename"),
                        "title": doc_result.data.get("title"),
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
    current_user: dict = Depends(require_disco_access),
):
    """Get KB documents linked to this initiative.

    Returns documents from the main KB that have been linked to this initiative
    via the disco_initiative_documents junction table.
    """
    # Resolve to UUID and check access
    resolved_id = await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        # Get linked document IDs from junction table
        links_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_documents")
            .select("document_id, linked_at, linked_by")
            .eq("initiative_id", resolved_id)
            .order("linked_at", desc=True)
            .execute()
        )

        links = links_result.data or []
        if not links:
            return {"success": True, "documents": [], "count": 0}

        # Get document details for all linked IDs
        doc_ids = [link["document_id"] for link in links]
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, title, uploaded_at, source_platform")
            .in_("id", doc_ids)
            .execute()
        )

        # Build a lookup map for documents
        docs_map = {doc["id"]: doc for doc in (docs_result.data or [])}

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
                        "linked_at": link["linked_at"],
                        "linked_by": link["linked_by"],
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
                        "uploaded_at": link["linked_at"],
                        "source_platform": None,
                        "linked_at": link["linked_at"],
                        "linked_by": link["linked_by"],
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
    current_user: dict = Depends(require_disco_access),
):
    """Unlink a KB document from this initiative.

    Removes the link from disco_initiative_documents but does not delete the document.
    """
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_documents")
            .delete()
            .eq("initiative_id", initiative_id)
            .eq("document_id", document_id)
            .execute()
        )

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
    current_user: dict = Depends(require_disco_access),
):
    """Link a vault folder to an initiative.

    New documents synced into this folder will be automatically linked.
    Optionally backfills existing documents in the folder.
    """
    resolved_id = await require_initiative_access(initiative_id, current_user, "editor")

    try:
        user_id = current_user["id"]
        folder_path = data.folder_path.strip().strip("/")

        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path is required")

        # Upsert folder link
        await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_folders")
            .upsert(
                {
                    "initiative_id": resolved_id,
                    "folder_path": folder_path,
                    "recursive": data.recursive,
                    "linked_by": user_id,
                },
                on_conflict="initiative_id,folder_path",
            )
            .execute()
        )

        logger.info(f"[DISCO] Linked folder '{folder_path}' to initiative {resolved_id} (recursive={data.recursive})")

        backfilled = 0

        # Backfill: link existing documents in this folder
        if data.backfill:
            # Get initiative name for auto-tagging
            init_result = await asyncio.to_thread(
                lambda: supabase.table("disco_initiatives").select("name").eq("id", resolved_id).single().execute()
            )
            initiative_name = init_result.data["name"] if init_result.data else None

            # Find documents in this folder
            query = supabase.table("documents").select("id")
            if data.recursive:
                query = query.ilike("obsidian_file_path", f"{folder_path}/%")
            else:
                # Non-recursive: match files directly in this folder (not subfolders)
                # We get all files in the folder prefix, then filter client-side
                query = query.ilike("obsidian_file_path", f"{folder_path}/%")

            docs_result = await asyncio.to_thread(lambda: query.execute())

            if docs_result.data:
                for doc in docs_result.data:
                    doc_id = doc["id"]

                    # For non-recursive, verify the doc is directly in the folder
                    if not data.recursive:
                        # We need the full path to check
                        doc_detail = await asyncio.to_thread(
                            lambda d=doc_id: supabase.table("documents")
                            .select("obsidian_file_path")
                            .eq("id", d)
                            .single()
                            .execute()
                        )
                        if doc_detail.data:
                            path = doc_detail.data["obsidian_file_path"]
                            # Check if there's a subfolder between folder_path and the filename
                            remainder = path[len(folder_path) + 1 :]
                            if "/" in remainder:
                                continue  # Skip - this is in a subfolder

                    try:
                        await asyncio.to_thread(
                            lambda d=doc_id: supabase.table("disco_initiative_documents")
                            .upsert(
                                {
                                    "initiative_id": resolved_id,
                                    "document_id": d,
                                    "linked_by": user_id,
                                },
                                on_conflict="initiative_id,document_id",
                            )
                            .execute()
                        )

                        # Auto-tag
                        if initiative_name:
                            await asyncio.to_thread(
                                lambda d=doc_id: supabase.table("document_tags")
                                .upsert(
                                    {
                                        "document_id": d,
                                        "tag": initiative_name,
                                        "source": "initiative",
                                    },
                                    on_conflict="document_id,tag",
                                )
                                .execute()
                            )

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
    current_user: dict = Depends(require_disco_access),
):
    """Get folders linked to this initiative."""
    resolved_id = await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_folders")
            .select("id, folder_path, recursive, linked_at, linked_by")
            .eq("initiative_id", resolved_id)
            .order("folder_path")
            .execute()
        )

        return {
            "success": True,
            "folders": result.data or [],
            "count": len(result.data or []),
        }

    except Exception as e:
        logger.error(f"Error getting linked folders: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/linked-folders/{folder_path:path}")
async def api_unlink_folder(
    initiative_id: str,
    folder_path: str,
    current_user: dict = Depends(require_disco_access),
):
    """Unlink a folder from this initiative.

    Removes the folder subscription but keeps existing document links intact.
    """
    resolved_id = await require_initiative_access(initiative_id, current_user, "editor")

    try:
        await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_folders")
            .delete()
            .eq("initiative_id", resolved_id)
            .eq("folder_path", folder_path)
            .execute()
        )

        logger.info(f"[DISCO] Unlinked folder '{folder_path}' from initiative {resolved_id}")

        return {"success": True, "message": f"Folder '{folder_path}' unlinked from initiative"}

    except Exception as e:
        logger.error(f"Error unlinking folder: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
