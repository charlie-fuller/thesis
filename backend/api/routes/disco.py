"""DISCo API Routes.

Discovery-Insights-Synthesis-Capabilities (DISCo) API endpoints.
"""

import asyncio
import os
from typing import List, Optional

import anthropic
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from auth import get_current_user, require_admin
from database import get_supabase
from logger_config import get_logger
from services.disco import (
    # Sharing
    add_member,
    # Chat
    ask_question,
    check_permission,
    # Initiative
    create_initiative,
    delete_document,
    delete_initiative,
    get_agent_types,
    get_conversation,
    get_document,
    get_documents,
    get_initiative,
    get_kb_files,
    list_initiatives,
    list_members,
    # Agent
    load_agent_prompt,
    promote_output_to_document,
    remove_member,
    run_agent,
    search_system_kb,
    # System KB
    sync_kb_from_filesystem,
    update_initiative,
    update_member_role,
    # Document
    upload_document,
    upload_document_file,
)
from services.disco.agent_service import (
    MULTI_PASS_CONFIG,
    get_consolidated_agents,
    get_run,
    list_runs,
    run_agent_multi_pass,
)
from services.disco.condenser_service import condense_output
from services.disco.prd_service import (
    approve_prd,
    # DISCo Capabilities stage
    generate_executive_summary,
    generate_prd_for_bundle,
    get_prd,
    list_prds,
    update_prd,
)
from services.disco.synthesis_service import (
    approve_bundle,
    # DISCo Synthesis stage
    create_bundle,
    get_bundle,
    get_bundle_feedback,
    list_bundles,
    merge_bundles,
    parse_synthesis_output,
    reject_bundle,
    split_bundle,
    update_bundle,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/disco", tags=["disco"])
supabase = get_supabase()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class InitiativeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class InitiativeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class DocumentUploadText(BaseModel):
    filename: str
    content: str
    document_type: str = "uploaded"


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = "viewer"


class MemberRoleUpdate(BaseModel):
    role: str


class ChatQuestion(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class AgentRunRequest(BaseModel):
    agent_type: str
    document_ids: Optional[List[str]] = None
    output_format: Optional[str] = "comprehensive"  # comprehensive, executive, brief
    multi_pass: Optional[bool] = False  # Enable multi-pass synthesis (synthesizer only)
    kb_folder: Optional[str] = None  # KB folder path for discovery_prep agent (deprecated)
    kb_tags: Optional[List[str]] = None  # KB tags for discovery_prep agent (preferred)


class LinkDocumentsRequest(BaseModel):
    """Request body for linking KB documents to an initiative."""

    document_ids: List[str]


# ============================================================================
# AUTH HELPERS
# ============================================================================


async def check_disco_access(user: dict) -> bool:
    """Check if user has DISCo access."""
    user_id = user.get("id")
    if not user_id:
        return False

    # Fetch user's app_access
    result = await asyncio.to_thread(
        lambda: supabase.table("users").select("app_access").eq("id", user_id).single().execute()
    )

    if not result.data:
        return False

    app_access = result.data.get("app_access", ["thesis"])

    # Check for disco, purdy (legacy), or all access
    return "disco" in app_access or "purdy" in app_access or "all" in app_access


async def require_disco_access(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to require DISCo access."""
    has_access = await check_disco_access(current_user)
    if not has_access:
        raise HTTPException(status_code=403, detail="DISCo access required")
    return current_user


async def require_initiative_access(
    initiative_id: str, current_user: dict, required_role: str = "viewer"
) -> bool:
    """Check user has access to initiative."""
    has_permission = await check_permission(initiative_id, current_user["id"], required_role)
    if not has_permission:
        raise HTTPException(
            status_code=403, detail=f"Insufficient permissions. Required: {required_role}"
        )
    return True


# ============================================================================
# INITIATIVES
# ============================================================================


@router.get("/initiatives")
async def api_list_initiatives(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_disco_access),
):
    """List all initiatives accessible to the user."""
    try:
        result = await list_initiatives(
            user_id=current_user["id"], status_filter=status, limit=limit, offset=offset
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error listing initiatives: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives")
async def api_create_initiative(
    data: InitiativeCreate, current_user: dict = Depends(require_disco_access)
):
    """Create a new initiative."""
    try:
        initiative = await create_initiative(
            name=data.name, description=data.description, user_id=current_user["id"]
        )
        return {"success": True, "initiative": initiative}
    except Exception as e:
        logger.error(f"Error creating initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/as-tags")
async def api_get_initiatives_as_tags(current_user: dict = Depends(require_disco_access)):
    """Get all initiatives formatted as tag options.

    Used by TagSelector component when showInitiatives=true.
    Returns initiative names sorted alphabetically.
    """
    try:
        user_id = current_user["id"]

        # Get initiatives the user has access to
        result = await list_initiatives(
            user_id=user_id,
            limit=500,  # Get all
        )

        initiatives = result.get("initiatives", [])

        # Format as tag options, sorted alphabetically
        tags = sorted(
            [
                {
                    "tag": init["name"],
                    "count": 0,  # Initiatives don't have document counts here
                    "type": "initiative",
                    "initiative_id": init["id"],
                    "status": init.get("status", "active"),
                }
                for init in initiatives
            ],
            key=lambda x: x["tag"].lower(),
        )

        return {"success": True, "tags": tags}

    except Exception as e:
        logger.error(f"Error getting initiatives as tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}")
async def api_get_initiative(
    initiative_id: str, current_user: dict = Depends(require_disco_access)
):
    """Get initiative details."""
    try:
        initiative = await get_initiative(initiative_id, current_user["id"])
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")
        return {"success": True, "initiative": initiative}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}")
async def api_update_initiative(
    initiative_id: str, data: InitiativeUpdate, current_user: dict = Depends(require_disco_access)
):
    """Update initiative details."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        updates = data.model_dump(exclude_unset=True)
        initiative = await update_initiative(
            initiative_id=initiative_id, user_id=current_user["id"], updates=updates
        )
        return {"success": True, "initiative": initiative}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error updating initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}")
async def api_delete_initiative(
    initiative_id: str, current_user: dict = Depends(require_disco_access)
):
    """Delete an initiative (owner only)."""
    try:
        await delete_initiative(initiative_id, current_user["id"])
        return {"success": True, "message": "Initiative deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error deleting initiative: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


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
            initiative_id=initiative_id, document_type=document_type, limit=limit, offset=offset
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
    initiative_id: str, data: DocumentUploadText, current_user: dict = Depends(require_disco_access)
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
    initiative_id: str, document_id: str, current_user: dict = Depends(require_disco_access)
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
    initiative_id: str, document_id: str, current_user: dict = Depends(require_disco_access)
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
            lambda: supabase.table("disco_initiatives")
            .select("id, name")
            .eq("id", initiative_id)
            .single()
            .execute()
        )

        if not initiative_result.data:
            raise HTTPException(status_code=404, detail="Initiative not found")

        initiative_name = initiative_result.data["name"]
        user_id = current_user["id"]

        linked_documents = []
        errors = []

        logger.info(
            f"[DISCO] Linking {len(data.document_ids)} documents to initiative {initiative_id}"
        )

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

                # Log ownership for debugging but allow any KB document to be linked
                doc_owner = doc_result.data.get("uploaded_by")
                if doc_owner != user_id:
                    logger.info(
                        f"[DISCO] User {user_id} linking document {doc_id} owned by {doc_owner}"
                    )

                # Create link in junction table (upsert to handle duplicates)
                link_result = await asyncio.to_thread(
                    lambda d=doc_id: supabase.table("disco_initiative_documents")
                    .upsert(
                        {"initiative_id": initiative_id, "document_id": d, "linked_by": user_id},
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
                        {"document_id": d, "tag": initiative_name, "source": "initiative"},
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
    initiative_id: str, current_user: dict = Depends(require_disco_access)
):
    """Get KB documents linked to this initiative.

    Returns documents from the main KB that have been linked to this initiative
    via the disco_initiative_documents junction table.
    """
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        # Step 1: Get linked document IDs from junction table
        links_result = await asyncio.to_thread(
            lambda: supabase.table("disco_initiative_documents")
            .select("document_id, linked_at, linked_by")
            .eq("initiative_id", initiative_id)
            .order("linked_at", desc=True)
            .execute()
        )

        links = links_result.data or []
        if not links:
            return {"success": True, "documents": [], "count": 0}

        # Step 2: Get document details for all linked IDs
        doc_ids = [link["document_id"] for link in links]
        docs_result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("id, filename, title, uploaded_at, source_platform")
            .in_("id", doc_ids)
            .execute()
        )

        # Build a lookup map for documents
        docs_map = {doc["id"]: doc for doc in (docs_result.data or [])}

        # Step 3: Combine link info with document info
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
                # Document was deleted but link remains - include with warning
                logger.warning(
                    f"[DISCO] Linked document {doc_id} not found (may have been deleted)"
                )
                linked_documents.append(
                    {
                        "id": doc_id,
                        "filename": "[Document deleted]",
                        "title": None,
                        "uploaded_at": link["linked_at"],  # Use linked_at as fallback
                        "source_platform": None,
                        "linked_at": link["linked_at"],
                        "linked_by": link["linked_by"],
                    }
                )

        return {"success": True, "documents": linked_documents, "count": len(linked_documents)}

    except Exception as e:
        logger.error(f"Error getting linked KB documents: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/linked-documents/{document_id}")
async def api_unlink_kb_document(
    initiative_id: str, document_id: str, current_user: dict = Depends(require_disco_access)
):
    """Unlink a KB document from this initiative.

    Removes the link from disco_initiative_documents but does not delete the document.
    """
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        # Delete the link
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
# RUNS
# ============================================================================


@router.get("/initiatives/{initiative_id}/runs")
async def api_list_runs(
    initiative_id: str, limit: int = 20, current_user: dict = Depends(require_disco_access)
):
    """List agent runs for an initiative."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        runs = await list_runs(initiative_id, limit)
        return {"success": True, "runs": runs}
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/runs")
async def api_start_run(
    initiative_id: str, data: AgentRunRequest, current_user: dict = Depends(require_disco_access)
):
    """Start a new agent run with streaming response."""
    await require_initiative_access(initiative_id, current_user, "editor")

    # Check if multi-pass is requested and valid
    use_multi_pass = data.multi_pass and data.agent_type in MULTI_PASS_CONFIG.get(
        "supported_agents", []
    )

    async def event_stream():
        # Send initial padding to force proxy buffer flush (some proxies buffer first 1KB)
        yield ": " + " " * 2048 + "\n\n"

        try:
            # Choose single or multi-pass based on request
            if use_multi_pass:
                agent_gen = run_agent_multi_pass(
                    initiative_id=initiative_id,
                    agent_type=data.agent_type,
                    user_id=current_user["id"],
                    document_ids=data.document_ids,
                    output_format=data.output_format or "comprehensive",
                )
            else:
                agent_gen = run_agent(
                    initiative_id=initiative_id,
                    agent_type=data.agent_type,
                    user_id=current_user["id"],
                    document_ids=data.document_ids,
                    output_format=data.output_format or "comprehensive",
                    kb_folder=data.kb_folder,
                    kb_tags=data.kb_tags,
                )

            async for event in agent_gen:
                event_type = event.get("type", "unknown")
                event_data = event.get("data", "")

                if event_type == "content":
                    yield f"data: {event_data}\n\n"
                elif event_type == "keepalive":
                    # SSE comment to keep connection alive and force flush
                    yield ": keepalive\n\n"
                elif event_type == "status":
                    yield f"event: status\ndata: {event_data}\n\n"
                elif event_type == "pass_complete":
                    # Multi-pass specific: indicates a pass completed
                    import json

                    yield f"event: pass_complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == "complete":
                    import json

                    yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == "error":
                    yield f"event: error\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


@router.get("/initiatives/{initiative_id}/runs/{run_id}")
async def api_get_run(
    initiative_id: str, run_id: str, current_user: dict = Depends(require_disco_access)
):
    """Get a run by ID."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        run = await get_run(run_id)
        if not run or run.get("initiative_id") != initiative_id:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"success": True, "run": run}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching run: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# OUTPUTS
# ============================================================================


@router.get("/initiatives/{initiative_id}/outputs")
async def api_list_outputs(
    initiative_id: str,
    agent_type: Optional[str] = None,
    current_user: dict = Depends(require_disco_access),
):
    """List outputs for an initiative."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        query = supabase.table("disco_outputs").select("*").eq("initiative_id", initiative_id)

        if agent_type:
            query = query.eq("agent_type", agent_type)

        query = query.order("created_at", desc=True)

        result = await asyncio.to_thread(lambda: query.execute())

        return {"success": True, "outputs": result.data or []}
    except Exception as e:
        logger.error(f"Error listing outputs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}")
async def api_get_latest_output(
    initiative_id: str, agent_type: str, current_user: dict = Depends(require_disco_access)
):
    """Get the latest output of a specific type."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("agent_type", agent_type)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail=f"No {agent_type} output found")

        return {"success": True, "output": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{agent_type}/versions")
async def api_list_output_versions(
    initiative_id: str, agent_type: str, current_user: dict = Depends(require_disco_access)
):
    """List all versions of an output type."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("id, version, created_at, title, recommendation, confidence_level")
            .eq("initiative_id", initiative_id)
            .eq("agent_type", agent_type)
            .order("version", desc=True)
            .execute()
        )

        return {"success": True, "versions": result.data or []}
    except Exception as e:
        logger.error(f"Error listing output versions: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/outputs/{output_id}/export")
async def api_export_output(
    initiative_id: str, output_id: str, current_user: dict = Depends(require_disco_access)
):
    """Export an output as markdown."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("agent_type, version, content_markdown")
            .eq("id", output_id)
            .eq("initiative_id", initiative_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Output not found")

        output = result.data
        filename = f"{output['agent_type']}_v{output['version']}.md"

        return StreamingResponse(
            iter([output["content_markdown"]]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/outputs/{output_id}/promote")
async def api_promote_output(
    initiative_id: str, output_id: str, current_user: dict = Depends(require_disco_access)
):
    """Promote an output to a document."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        document = await promote_output_to_document(output_id, initiative_id)
        return {"success": True, "document": document}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error promoting output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/outputs/{output_id}")
async def api_delete_output(
    initiative_id: str, output_id: str, current_user: dict = Depends(require_disco_access)
):
    """Delete an output."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        # Verify output belongs to initiative
        output_result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("id, agent_type, version")
            .eq("id", output_id)
            .eq("initiative_id", initiative_id)
            .single()
            .execute()
        )

        if not output_result.data:
            raise HTTPException(status_code=404, detail="Output not found")

        # Delete the output
        await asyncio.to_thread(
            lambda: supabase.table("disco_outputs").delete().eq("id", output_id).execute()
        )

        logger.info(
            f"[DISCO] Deleted output {output_id} ({output_result.data['agent_type']} v{output_result.data['version']})"
        )

        return {"success": True, "deleted_output_id": output_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting output: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/outputs/{output_id}/condense")
async def api_condense_output(
    initiative_id: str, output_id: str, current_user: dict = Depends(require_disco_access)
):
    """Apply Smart Brevity condensation to an output."""
    await require_initiative_access(initiative_id, current_user, "editor")

    async def event_stream():
        # Send initial padding to force proxy buffer flush
        yield ": " + " " * 2048 + "\n\n"

        try:
            async for event in condense_output(output_id, current_user["id"]):
                event_type = event.get("type", "unknown")
                event_data = event.get("data", "")

                if event_type == "content":
                    yield f"data: {event_data}\n\n"
                elif event_type == "keepalive":
                    yield ": keepalive\n\n"
                elif event_type == "status":
                    yield f"event: status\ndata: {event_data}\n\n"
                elif event_type == "complete":
                    import json

                    yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                elif event_type == "error":
                    yield f"event: error\ndata: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Condense stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


# ============================================================================
# CHECKPOINTS
# ============================================================================


class CheckpointApprove(BaseModel):
    """Request body for approving a checkpoint."""

    notes: Optional[str] = None
    checklist_items: Optional[List[dict]] = None  # [{item: str, completed: bool}]


class CheckpointReset(BaseModel):
    """Request body for resetting a checkpoint."""

    reason: Optional[str] = None


@router.get("/initiatives/{initiative_id}/checkpoints")
async def api_list_checkpoints(
    initiative_id: str, current_user: dict = Depends(require_disco_access)
):
    """List all checkpoints for an initiative.

    Returns checkpoint statuses for the 4 stage gates:
    1. Discovery Guide -> Insight Analyst
    2. Insight Analyst -> Initiative Builder
    3. Initiative Builder -> Requirements Generator
    4. Requirements Generator -> Done
    """
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        # Initialize checkpoints if they don't exist
        await asyncio.to_thread(
            lambda: supabase.rpc(
                "initialize_disco_checkpoints", {"p_initiative_id": initiative_id}
            ).execute()
        )

        # Fetch checkpoints
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .order("checkpoint_number")
            .execute()
        )

        checkpoints = result.data or []

        # Calculate staleness for each checkpoint
        for checkpoint in checkpoints:
            if checkpoint["status"] == "approved":
                # Check if new documents were added since approval
                docs_result = await asyncio.to_thread(
                    lambda cp=checkpoint: supabase.table("disco_initiative_documents")
                    .select("linked_at")
                    .eq("initiative_id", initiative_id)
                    .gt("linked_at", cp["approved_at"])
                    .limit(1)
                    .execute()
                )
                if docs_result.data:
                    checkpoint["status"] = "stale"
                    checkpoint["stale_reason"] = "New documents added since approval"

        return {"success": True, "checkpoints": checkpoints}
    except Exception as e:
        logger.error(f"Error listing checkpoints: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/checkpoints/{checkpoint_number}")
async def api_get_checkpoint(
    initiative_id: str, checkpoint_number: int, current_user: dict = Depends(require_disco_access)
):
    """Get a specific checkpoint with details."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("checkpoint_number", checkpoint_number)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        checkpoint = result.data

        # Get checkpoint-specific checklist content
        checkpoint_checklists = {
            1: {
                "title": "Ready to Execute Discovery?",
                "items": [
                    {
                        "item": "Triage decision is GO (not NO-GO or INVESTIGATE)",
                        "completed": False,
                    },
                    {
                        "item": "Discovery sessions are planned with clear agendas",
                        "completed": False,
                    },
                    {"item": "Participants and sponsors are identified", "completed": False},
                    {"item": "You are ready to execute the discovery sessions", "completed": False},
                ],
                "human_action": "After approval, YOU will conduct interviews/workshops per the session plan, upload transcripts and notes to Documents, and re-run Discovery Guide to check coverage.",
            },
            2: {
                "title": "Ready for Initiative Bundles?",
                "items": [
                    {"item": "Decision document quality is acceptable", "completed": False},
                    {"item": "Leverage point makes sense", "completed": False},
                    {"item": "Evidence supports conclusions", "completed": False},
                    {"item": "No critical gaps or contradictions", "completed": False},
                ],
                "human_action": "Review the decision document and validate the leverage point before proceeding.",
            },
            3: {
                "title": "Ready for PRD Generation?",
                "items": [
                    {"item": "Bundle definitions are clear", "completed": False},
                    {
                        "item": "Scoring (impact/feasibility/urgency) is accurate",
                        "completed": False,
                    },
                    {"item": "Dependencies are correctly mapped", "completed": False},
                    {"item": "Selected bundles for PRD generation", "completed": False},
                ],
                "human_action": "Approve, reject, merge, or split bundles as needed before generating PRDs.",
            },
            4: {
                "title": "Ready for Engineering Handoff?",
                "items": [
                    {"item": "PRD is complete and accurate", "completed": False},
                    {"item": "Technical approach is validated", "completed": False},
                    {"item": "Requirements are testable", "completed": False},
                    {"item": "Ready for engineering planning", "completed": False},
                ],
                "human_action": "Final review before handoff to engineering team.",
            },
        }

        checkpoint["checklist_config"] = checkpoint_checklists.get(checkpoint_number)

        return {"success": True, "checkpoint": checkpoint}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/checkpoints/{checkpoint_number}/approve")
async def api_approve_checkpoint(
    initiative_id: str,
    checkpoint_number: int,
    body: CheckpointApprove,
    current_user: dict = Depends(require_disco_access),
):
    """Approve a checkpoint to unlock the next agent.

    This is the human-in-the-loop gate between DISCo stages.
    """
    await require_initiative_access(initiative_id, current_user, "editor")

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        # Get current checkpoint
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("checkpoint_number", checkpoint_number)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        checkpoint = result.data

        if checkpoint["status"] not in ["needs_review", "stale"]:
            raise HTTPException(
                status_code=400,
                detail=f"Checkpoint cannot be approved (current status: {checkpoint['status']})",
            )

        # Update checkpoint to approved
        from datetime import datetime, timezone

        update_data = {
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": current_user["id"],
            "notes": body.notes,
        }

        if body.checklist_items:
            update_data["checklist_items"] = body.checklist_items

        await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .update(update_data)
            .eq("id", checkpoint["id"])
            .execute()
        )

        # Unlock the next checkpoint if not the last one
        if checkpoint_number < 4:
            await asyncio.to_thread(
                lambda: supabase.table("disco_checkpoints")
                .update({"status": "locked"})  # Will be set to needs_review when agent runs
                .eq("initiative_id", initiative_id)
                .eq("checkpoint_number", checkpoint_number + 1)
                .eq("status", "locked")  # Only update if still locked
                .execute()
            )

        logger.info(
            f"[DISCO] Checkpoint {checkpoint_number} approved for initiative {initiative_id} by user {current_user['id']}"
        )

        return {
            "success": True,
            "message": f"Checkpoint {checkpoint_number} approved",
            "next_agent": _get_next_agent_for_checkpoint(checkpoint_number),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving checkpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/checkpoints/{checkpoint_number}/reset")
async def api_reset_checkpoint(
    initiative_id: str,
    checkpoint_number: int,
    body: CheckpointReset,
    current_user: dict = Depends(require_disco_access),
):
    """Reset a checkpoint to needs_review.

    Used when re-running an agent after approval, or when requesting changes.
    """
    await require_initiative_access(initiative_id, current_user, "editor")

    if checkpoint_number not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Checkpoint number must be 1-4")

    try:
        # Get current checkpoint
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .select("*")
            .eq("initiative_id", initiative_id)
            .eq("checkpoint_number", checkpoint_number)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        checkpoint = result.data

        if checkpoint["status"] == "locked":
            raise HTTPException(
                status_code=400,
                detail="Cannot reset a locked checkpoint",
            )

        # Reset checkpoint to needs_review
        update_data = {
            "status": "needs_review",
            "approved_at": None,
            "approved_by": None,
        }

        if body.reason:
            update_data["notes"] = f"Reset: {body.reason}"

        await asyncio.to_thread(
            lambda: supabase.table("disco_checkpoints")
            .update(update_data)
            .eq("id", checkpoint["id"])
            .execute()
        )

        # Also reset subsequent checkpoints to locked
        if checkpoint_number < 4:
            await asyncio.to_thread(
                lambda: supabase.table("disco_checkpoints")
                .update({"status": "locked", "approved_at": None, "approved_by": None})
                .eq("initiative_id", initiative_id)
                .gt("checkpoint_number", checkpoint_number)
                .execute()
            )

        logger.info(
            f"[DISCO] Checkpoint {checkpoint_number} reset for initiative {initiative_id} by user {current_user['id']}"
        )

        return {
            "success": True,
            "message": f"Checkpoint {checkpoint_number} reset to needs_review",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting checkpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


def _get_next_agent_for_checkpoint(checkpoint_number: int) -> str:
    """Get the next agent to run after a checkpoint is approved."""
    agents = {
        1: "insight_analyst",
        2: "initiative_builder",
        3: "requirements_generator",
        4: None,  # No next agent after final checkpoint
    }
    return agents.get(checkpoint_number)


# ============================================================================
# DEBUG
# ============================================================================


@router.get("/initiatives/{initiative_id}/debug/outputs")
async def api_debug_outputs(initiative_id: str, current_user: dict = Depends(require_disco_access)):
    """Debug endpoint to check raw output data."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_outputs")
            .select("id, agent_type, version, title, content_markdown, created_at")
            .eq("initiative_id", initiative_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        outputs = []
        for o in result.data or []:
            outputs.append(
                {
                    "id": o.get("id"),
                    "agent_type": o.get("agent_type"),
                    "agent_type_type": type(o.get("agent_type")).__name__,
                    "version": o.get("version"),
                    "title": o.get("title"),
                    "content_length": len(o.get("content_markdown", "") or ""),
                    "content_preview": (o.get("content_markdown", "") or "")[:200],
                    "created_at": o.get("created_at"),
                }
            )

        return {"success": True, "count": len(result.data or []), "outputs": outputs}
    except Exception as e:
        logger.error(f"Debug outputs error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# SHARING
# ============================================================================


@router.get("/initiatives/{initiative_id}/members")
async def api_list_members(initiative_id: str, current_user: dict = Depends(require_disco_access)):
    """List initiative members."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        members = await list_members(initiative_id)
        return {"success": True, "members": members}
    except Exception as e:
        logger.error(f"Error listing members: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/members")
async def api_add_member(
    initiative_id: str, data: MemberInvite, current_user: dict = Depends(require_disco_access)
):
    """Invite a member to an initiative."""
    await require_initiative_access(initiative_id, current_user, "editor")

    try:
        member = await add_member(
            initiative_id=initiative_id,
            user_email=data.email,
            role=data.role,
            inviter_id=current_user["id"],
        )
        return {"success": True, "member": member}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}/members/{user_id}")
async def api_update_member_role(
    initiative_id: str,
    user_id: str,
    data: MemberRoleUpdate,
    current_user: dict = Depends(require_disco_access),
):
    """Update a member's role."""
    try:
        member = await update_member_role(
            initiative_id=initiative_id,
            user_id=user_id,
            new_role=data.role,
            updater_id=current_user["id"],
        )
        return {"success": True, "member": member}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error updating member role: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/initiatives/{initiative_id}/members/{user_id}")
async def api_remove_member(
    initiative_id: str, user_id: str, current_user: dict = Depends(require_disco_access)
):
    """Remove a member from an initiative."""
    try:
        await remove_member(
            initiative_id=initiative_id, user_id=user_id, remover_id=current_user["id"]
        )
        return {"success": True, "message": "Member removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# CHAT
# ============================================================================


@router.get("/initiatives/{initiative_id}/chat")
async def api_get_chat(initiative_id: str, current_user: dict = Depends(require_disco_access)):
    """Get or create chat conversation."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        conversation = await get_conversation(initiative_id, current_user["id"])
        return {"success": True, "conversation": conversation}
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/chat")
async def api_ask_question(
    initiative_id: str, data: ChatQuestion, current_user: dict = Depends(require_disco_access)
):
    """Ask a question about the initiative."""
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        result = await ask_question(
            initiative_id=initiative_id,
            question=data.question,
            user_id=current_user["id"],
            conversation_id=data.conversation_id,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# PROJECT EXTRACTION FROM CHAT
# ============================================================================


class ExtractedField(BaseModel):
    """A field extracted from chat with confidence level."""

    value: Optional[str] = None
    confidence: str = Field(default="none", description="Confidence level: high, medium, low, none")


class ExtractedScore(BaseModel):
    """A numeric score (1-5) extracted from chat with confidence level."""

    value: Optional[int] = None
    confidence: str = Field(default="none", description="Confidence level: high, medium, low, none")


class ExtractProjectResponse(BaseModel):
    """Response from project extraction endpoint."""

    title: ExtractedField
    description: ExtractedField
    department: ExtractedField
    current_state: ExtractedField
    desired_state: ExtractedField
    roi_potential: ExtractedScore
    implementation_effort: ExtractedScore
    strategic_alignment: ExtractedScore
    stakeholder_readiness: ExtractedScore
    source_context: str = Field(description="Formatted chat excerpt for source_notes")


PROJECT_EXTRACTION_PROMPT = """You are analyzing a conversation from a DISCo initiative chat to extract project information.

Your task is to identify details that could populate a new AI project record. Extract as much as you can confidently determine from the conversation.

For each field, provide:
1. The extracted value (or null if not found)
2. A confidence level: "high" (explicitly stated), "medium" (implied/inferred), "low" (guessed from context), "none" (cannot determine)

IMPORTANT: Pay special attention to the most recent messages (marked with [RECENT]) as they likely contain the most relevant project discussion.

Fields to extract:
- title: A concise project name (max 100 chars)
- description: What this project aims to accomplish (2-3 sentences)
- department: Which department this relates to (finance, legal, hr, it, revops, marketing, sales, operations)
- current_state: The current situation/pain point
- desired_state: The target outcome/goal
- roi_potential: Score 1-5 (5=highest potential ROI)
- implementation_effort: Score 1-5 (5=easiest to implement)
- strategic_alignment: Score 1-5 (5=highest strategic value)
- stakeholder_readiness: Score 1-5 (5=most ready stakeholders)

Respond in this exact JSON format:
{
  "title": {"value": "string or null", "confidence": "high|medium|low|none"},
  "description": {"value": "string or null", "confidence": "high|medium|low|none"},
  "department": {"value": "string or null", "confidence": "high|medium|low|none"},
  "current_state": {"value": "string or null", "confidence": "high|medium|low|none"},
  "desired_state": {"value": "string or null", "confidence": "high|medium|low|none"},
  "roi_potential": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "implementation_effort": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "strategic_alignment": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "stakeholder_readiness": {"value": "number 1-5 or null", "confidence": "high|medium|low|none"},
  "source_summary": "A brief 1-2 sentence summary of the key discussion points that led to these extractions"
}

Return ONLY valid JSON, no markdown formatting."""


@router.post("/initiatives/{initiative_id}/extract-project")
async def api_extract_project_from_chat(
    initiative_id: str, current_user: dict = Depends(require_disco_access)
):
    """Extract project fields from initiative chat conversation using AI.

    Analyzes the full conversation with emphasis on recent messages.
    Returns extracted fields with confidence levels.
    """
    await require_initiative_access(initiative_id, current_user, "viewer")

    try:
        # Get initiative name for context
        initiative = await get_initiative(initiative_id, current_user["id"])
        initiative_name = (
            initiative.get("name", "Unknown Initiative") if initiative else "Unknown Initiative"
        )

        # Get conversation
        conversation = await get_conversation(initiative_id, current_user["id"])

        if not conversation or not conversation.get("messages"):
            return {
                "success": False,
                "error": "No conversation found. Start a chat first to discuss the project.",
            }

        messages = conversation.get("messages", [])
        if not messages:
            return {
                "success": False,
                "error": "No messages in conversation. Discuss your project idea first.",
            }

        # Format conversation for analysis
        # Mark last 5 messages as [RECENT]
        formatted_messages = []
        recent_start = max(0, len(messages) - 5)

        for i, msg in enumerate(messages):
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            prefix = "[RECENT] " if i >= recent_start else ""
            formatted_messages.append(f"{prefix}{role}: {content}")

        conversation_text = "\n\n".join(formatted_messages)

        # Build the prompt
        full_prompt = f"""Initiative: {initiative_name}

Conversation:
{conversation_text}

Now extract project information from this conversation."""

        # Call Claude
        anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = anthropic_client.messages.create(
            model=os.environ.get("DISCO_EXTRACTION_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=1500,
            system=PROJECT_EXTRACTION_PROMPT,
            messages=[{"role": "user", "content": full_prompt}],
        )

        # Parse response
        import json

        response_text = response.content[0].text.strip()
        # Remove any markdown formatting if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        try:
            extracted = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            raise HTTPException(
                status_code=500, detail="Failed to parse AI extraction response"
            ) from e

        # Build source context
        recent_summary = extracted.get("source_summary", "")
        source_context = f"Created from DISCo initiative '{initiative_name}' chat. {recent_summary}"

        # Format response
        return {
            "success": True,
            "extracted": {
                "title": {
                    "value": extracted.get("title", {}).get("value"),
                    "confidence": extracted.get("title", {}).get("confidence", "none"),
                },
                "description": {
                    "value": extracted.get("description", {}).get("value"),
                    "confidence": extracted.get("description", {}).get("confidence", "none"),
                },
                "department": {
                    "value": extracted.get("department", {}).get("value"),
                    "confidence": extracted.get("department", {}).get("confidence", "none"),
                },
                "current_state": {
                    "value": extracted.get("current_state", {}).get("value"),
                    "confidence": extracted.get("current_state", {}).get("confidence", "none"),
                },
                "desired_state": {
                    "value": extracted.get("desired_state", {}).get("value"),
                    "confidence": extracted.get("desired_state", {}).get("confidence", "none"),
                },
                "roi_potential": {
                    "value": extracted.get("roi_potential", {}).get("value"),
                    "confidence": extracted.get("roi_potential", {}).get("confidence", "none"),
                },
                "implementation_effort": {
                    "value": extracted.get("implementation_effort", {}).get("value"),
                    "confidence": extracted.get("implementation_effort", {}).get(
                        "confidence", "none"
                    ),
                },
                "strategic_alignment": {
                    "value": extracted.get("strategic_alignment", {}).get("value"),
                    "confidence": extracted.get("strategic_alignment", {}).get(
                        "confidence", "none"
                    ),
                },
                "stakeholder_readiness": {
                    "value": extracted.get("stakeholder_readiness", {}).get("value"),
                    "confidence": extracted.get("stakeholder_readiness", {}).get(
                        "confidence", "none"
                    ),
                },
            },
            "source_context": source_context,
            "initiative_id": initiative_id,
            "initiative_name": initiative_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting project from chat: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# AGENTS (Reference)
# ============================================================================


@router.get("/agents")
async def api_list_agents(
    include_legacy: bool = False, current_user: dict = Depends(require_disco_access)
):
    """List available agent types.

    Args:
        include_legacy: If True, includes legacy agents for backwards compatibility.
                       Default returns only the 4 consolidated stage-aligned agents.
    """
    if include_legacy:
        return {"success": True, "agents": get_agent_types(include_legacy=True)}
    else:
        return {"success": True, "agents": get_consolidated_agents()}


@router.get("/agents/{agent_type}")
async def api_get_agent_prompt(agent_type: str, current_user: dict = Depends(require_admin)):
    """Get agent prompt (admin only)."""
    try:
        prompt = load_agent_prompt(agent_type)
        return {"success": True, "agent_type": agent_type, "prompt": prompt}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error loading agent prompt: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# SYSTEM KB (Admin)
# ============================================================================


@router.get("/system-kb")
async def api_list_kb_files(current_user: dict = Depends(require_admin)):
    """List system KB files (admin only)."""
    try:
        files = await get_kb_files()
        return {"success": True, "files": files}
    except Exception as e:
        logger.error(f"Error listing KB files: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/system-kb/sync")
async def api_sync_kb(
    background_tasks: BackgroundTasks, current_user: dict = Depends(require_admin)
):
    """Sync system KB from filesystem (admin only)."""
    try:
        # Run sync in background
        async def do_sync():
            try:
                result = await sync_kb_from_filesystem()
                logger.info(f"KB sync completed: {result}")
            except Exception as e:
                logger.error(f"KB sync failed: {e}")

        background_tasks.add_task(asyncio.create_task, do_sync())

        return {"success": True, "message": "KB sync started in background"}
    except Exception as e:
        logger.error(f"Error starting KB sync: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/system-kb/search")
async def api_search_kb(
    q: str,
    limit: int = 10,
    category: Optional[str] = None,
    current_user: dict = Depends(require_disco_access),
):
    """Search system KB."""
    try:
        chunks = await search_system_kb(q, limit=limit, category=category)
        return {"success": True, "results": chunks}
    except Exception as e:
        logger.error(f"Error searching KB: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# DISCo SYNTHESIS STAGE - Bundle Management
# ============================================================================


class BundleCreate(BaseModel):
    """Request body for creating a bundle."""

    name: str
    description: str
    impact_score: Optional[str] = None
    impact_rationale: Optional[str] = None
    feasibility_score: Optional[str] = None
    feasibility_rationale: Optional[str] = None
    urgency_score: Optional[str] = None
    urgency_rationale: Optional[str] = None
    complexity_tier: Optional[str] = None
    complexity_rationale: Optional[str] = None
    included_items: Optional[List[dict]] = None
    stakeholders: Optional[List[dict]] = None
    dependencies: Optional[dict] = None
    bundling_rationale: Optional[str] = None


class BundleUpdate(BaseModel):
    """Request body for updating a bundle."""

    name: Optional[str] = None
    description: Optional[str] = None
    impact_score: Optional[str] = None
    impact_rationale: Optional[str] = None
    feasibility_score: Optional[str] = None
    feasibility_rationale: Optional[str] = None
    urgency_score: Optional[str] = None
    urgency_rationale: Optional[str] = None
    complexity_tier: Optional[str] = None
    complexity_rationale: Optional[str] = None
    included_items: Optional[List[dict]] = None
    stakeholders: Optional[List[dict]] = None
    dependencies: Optional[dict] = None
    bundling_rationale: Optional[str] = None
    feedback: Optional[str] = None


class BundleApproval(BaseModel):
    """Request body for approving/rejecting a bundle."""

    feedback: Optional[str] = None


class BundleMerge(BaseModel):
    """Request body for merging bundles."""

    bundle_ids: List[str]
    merged_name: str
    merged_description: str
    feedback: Optional[str] = None


class BundleSplit(BaseModel):
    """Request body for splitting a bundle."""

    split_definitions: List[dict]  # [{name, description, item_indices}]
    feedback: Optional[str] = None


@router.get("/initiatives/{initiative_id}/bundles")
async def api_list_bundles(
    initiative_id: str,
    status: Optional[str] = None,
    current_user: dict = Depends(require_disco_access),
):
    """List bundles for an initiative."""
    try:
        # Verify access
        initiative = await get_initiative(initiative_id)
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")

        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        bundles = await list_bundles(initiative_id, status=status)
        return {"success": True, "bundles": bundles}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing bundles: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles")
async def api_create_bundle(
    initiative_id: str, body: BundleCreate, current_user: dict = Depends(require_disco_access)
):
    """Create a new bundle for an initiative."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        bundle = await create_bundle(
            initiative_id=initiative_id,
            name=body.name,
            description=body.description,
            impact_score=body.impact_score,
            impact_rationale=body.impact_rationale,
            feasibility_score=body.feasibility_score,
            feasibility_rationale=body.feasibility_rationale,
            urgency_score=body.urgency_score,
            urgency_rationale=body.urgency_rationale,
            complexity_tier=body.complexity_tier,
            complexity_rationale=body.complexity_rationale,
            included_items=body.included_items,
            stakeholders=body.stakeholders,
            dependencies=body.dependencies,
            bundling_rationale=body.bundling_rationale,
        )
        return {"success": True, "bundle": bundle}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/bundles/{bundle_id}")
async def api_get_bundle(
    initiative_id: str, bundle_id: str, current_user: dict = Depends(require_disco_access)
):
    """Get a specific bundle."""
    try:
        # Verify access
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        # Include feedback history
        feedback = await get_bundle_feedback(bundle_id)

        return {"success": True, "bundle": bundle, "feedback": feedback}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}/bundles/{bundle_id}")
async def api_update_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleUpdate,
    current_user: dict = Depends(require_disco_access),
):
    """Update a bundle."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Get bundle and verify it belongs to this initiative
        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        # Build update dict from non-None fields
        updates = {k: v for k, v in body.model_dump().items() if v is not None and k != "feedback"}

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        updated_bundle = await update_bundle(
            bundle_id=bundle_id, updates=updates, user_id=current_user["id"], feedback=body.feedback
        )
        return {"success": True, "bundle": updated_bundle}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error updating bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/approve")
async def api_approve_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleApproval,
    current_user: dict = Depends(require_disco_access),
):
    """Approve a bundle for PRD generation."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Get bundle and verify it belongs to this initiative
        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        if bundle["status"] != "proposed":
            raise HTTPException(status_code=400, detail=f"Bundle is already {bundle['status']}")

        approved_bundle = await approve_bundle(
            bundle_id=bundle_id, user_id=current_user["id"], feedback=body.feedback
        )
        return {"success": True, "bundle": approved_bundle}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/reject")
async def api_reject_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleApproval,
    current_user: dict = Depends(require_disco_access),
):
    """Reject a bundle."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Get bundle and verify it belongs to this initiative
        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        if bundle["status"] != "proposed":
            raise HTTPException(status_code=400, detail=f"Bundle is already {bundle['status']}")

        if not body.feedback:
            raise HTTPException(status_code=400, detail="Feedback is required when rejecting")

        rejected_bundle = await reject_bundle(
            bundle_id=bundle_id, user_id=current_user["id"], feedback=body.feedback
        )
        return {"success": True, "bundle": rejected_bundle}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/merge")
async def api_merge_bundles(
    initiative_id: str, body: BundleMerge, current_user: dict = Depends(require_disco_access)
):
    """Merge multiple bundles into one."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Verify all bundles belong to this initiative
        for bid in body.bundle_ids:
            bundle = await get_bundle(bid)
            if not bundle or bundle["initiative_id"] != initiative_id:
                raise HTTPException(status_code=404, detail=f"Bundle not found: {bid}")

        merged_bundle = await merge_bundles(
            bundle_ids=body.bundle_ids,
            merged_name=body.merged_name,
            merged_description=body.merged_description,
            user_id=current_user["id"],
            feedback=body.feedback,
        )
        return {"success": True, "bundle": merged_bundle}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error merging bundles: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/split")
async def api_split_bundle(
    initiative_id: str,
    bundle_id: str,
    body: BundleSplit,
    current_user: dict = Depends(require_disco_access),
):
    """Split a bundle into multiple bundles."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Get bundle and verify it belongs to this initiative
        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        new_bundles = await split_bundle(
            bundle_id=bundle_id,
            split_definitions=body.split_definitions,
            user_id=current_user["id"],
            feedback=body.feedback,
        )
        return {"success": True, "bundles": new_bundles}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error splitting bundle: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/synthesize")
async def api_run_synthesis(initiative_id: str, current_user: dict = Depends(require_disco_access)):
    """Run the Synthesis agent and create bundles from its output.

    This endpoint:
    1. Runs the synthesis agent
    2. Parses the output to extract bundle definitions
    3. Creates bundle records in the database
    """
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Run strategist agent
        async def stream_and_create_bundles():
            output_id = None
            full_content = ""

            async for event in run_agent(
                initiative_id=initiative_id,
                agent_type="strategist",
                user_id=current_user["id"],
                output_format="comprehensive",
            ):
                if event["type"] == "complete":
                    output_id = event.get("data", {}).get("id")
                    full_content = event.get("data", {}).get("content_markdown", "")
                yield event

            # After streaming completes, parse and create bundles
            if output_id and full_content:
                try:
                    bundle_defs = parse_synthesis_output(full_content, output_id)
                    created_bundles = []
                    for defn in bundle_defs:
                        bundle = await create_bundle(initiative_id=initiative_id, **defn)
                        created_bundles.append(bundle)

                    # Yield final event with bundle info
                    yield {
                        "type": "bundles_created",
                        "data": {"count": len(created_bundles), "bundles": created_bundles},
                    }
                except Exception as e:
                    logger.error(f"Error creating bundles from synthesis: {e}")
                    yield {"type": "bundles_error", "data": str(e)}

        # Stream SSE response
        async def generate():
            async for event in stream_and_create_bundles():
                event_type = event["type"]
                data = event.get("data", "")

                if isinstance(data, dict):
                    import json

                    data = json.dumps(data)

                if event_type in [
                    "status",
                    "complete",
                    "error",
                    "bundles_created",
                    "bundles_error",
                ]:
                    yield f"event: {event_type}\ndata: {data}\n\n"
                else:
                    yield f"data: {data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running synthesis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# DISCo CAPABILITIES STAGE - PRD Generation
# ============================================================================


class PRDUpdate(BaseModel):
    """Request body for updating a PRD."""

    content_markdown: Optional[str] = None
    status: Optional[str] = None


@router.get("/initiatives/{initiative_id}/prds")
async def api_list_prds(
    initiative_id: str,
    bundle_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_disco_access),
):
    """List PRDs for an initiative."""
    try:
        # Verify access
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        prds = await list_prds(initiative_id, bundle_id=bundle_id, status=status)
        return {"success": True, "prds": prds}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing PRDs: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/initiatives/{initiative_id}/prds/{prd_id}")
async def api_get_prd(
    initiative_id: str, prd_id: str, current_user: dict = Depends(require_disco_access)
):
    """Get a specific PRD."""
    try:
        # Verify access
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        prd = await get_prd(prd_id)
        if not prd or prd["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="PRD not found")

        return {"success": True, "prd": prd}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/initiatives/{initiative_id}/prds/{prd_id}")
async def api_update_prd(
    initiative_id: str,
    prd_id: str,
    body: PRDUpdate,
    current_user: dict = Depends(require_disco_access),
):
    """Update a PRD."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Get PRD and verify
        prd = await get_prd(prd_id)
        if not prd or prd["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="PRD not found")

        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        updated_prd = await update_prd(prd_id, updates)
        return {"success": True, "prd": updated_prd}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/prds/{prd_id}/approve")
async def api_approve_prd(
    initiative_id: str, prd_id: str, current_user: dict = Depends(require_disco_access)
):
    """Approve a PRD."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Get PRD and verify
        prd = await get_prd(prd_id)
        if not prd or prd["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="PRD not found")

        approved_prd = await approve_prd(prd_id, current_user["id"])
        return {"success": True, "prd": approved_prd}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/bundles/{bundle_id}/generate-prd")
async def api_generate_prd(
    initiative_id: str, bundle_id: str, current_user: dict = Depends(require_disco_access)
):
    """Generate a PRD for an approved bundle."""
    try:
        # Verify editor access
        can_edit = await check_permission(initiative_id, current_user["id"], "editor")
        if not can_edit:
            raise HTTPException(status_code=403, detail="No edit access to this initiative")

        # Get bundle and verify
        bundle = await get_bundle(bundle_id)
        if not bundle or bundle["initiative_id"] != initiative_id:
            raise HTTPException(status_code=404, detail="Bundle not found")

        if bundle["status"] != "approved":
            raise HTTPException(
                status_code=400, detail=f"Bundle must be approved (current: {bundle['status']})"
            )

        # Stream PRD generation
        async def generate():
            async for event in generate_prd_for_bundle(
                bundle_id=bundle_id, initiative_id=initiative_id, user_id=current_user["id"]
            ):
                event_type = event["type"]
                data = event.get("data", "")

                if isinstance(data, dict):
                    import json

                    data = json.dumps(data)

                if event_type in ["status", "complete", "error"]:
                    yield f"event: {event_type}\ndata: {data}\n\n"
                else:
                    yield f"data: {data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PRD: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/initiatives/{initiative_id}/generate-summary")
async def api_generate_executive_summary(
    initiative_id: str, current_user: dict = Depends(require_disco_access)
):
    """Generate an executive summary across all approved bundles."""
    try:
        # Verify access
        can_view = await check_permission(initiative_id, current_user["id"], "viewer")
        if not can_view:
            raise HTTPException(status_code=403, detail="No access to this initiative")

        # Stream executive summary generation
        async def generate():
            async for event in generate_executive_summary(
                initiative_id=initiative_id, user_id=current_user["id"]
            ):
                event_type = event["type"]
                data = event.get("data", "")

                if isinstance(data, dict):
                    import json

                    data = json.dumps(data)

                if event_type in ["status", "complete", "error"]:
                    yield f"event: {event_type}\ndata: {data}\n\n"
                else:
                    yield f"data: {data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# ANALYTICS
# ============================================================================


@router.get("/analytics/usage")
async def api_disco_usage_analytics(days: int = 30, current_user: dict = Depends(get_current_user)):
    """Get DISCo usage analytics - agent runs over time.

    Returns usage trends with each DISCo agent broken out separately.
    """
    from collections import defaultdict
    from datetime import datetime, timedelta

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch all runs in the date range
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_runs")
            .select("id, agent_type, status, started_at")
            .gte("started_at", start_date.isoformat())
            .order("started_at", desc=False)
            .execute()
        )

        runs = result.data or []

        # Build daily counts per agent
        daily_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        agent_totals: dict[str, int] = defaultdict(int)
        all_agents: set[str] = set()

        for run in runs:
            agent_type = run["agent_type"]
            # Parse date and truncate to day
            started_at = run["started_at"]
            if started_at:
                # Handle ISO format with timezone
                date_str = started_at.split("T")[0]
                daily_counts[date_str][agent_type] += 1
                agent_totals[agent_type] += 1
                all_agents.add(agent_type)

        # Generate all dates in range
        date_cursor = start_date
        all_dates = []
        while date_cursor <= end_date:
            all_dates.append(date_cursor.strftime("%Y-%m-%d"))
            date_cursor += timedelta(days=1)

        # Sort agents by total usage (descending)
        sorted_agents = sorted(all_agents, key=lambda a: agent_totals[a], reverse=True)

        # Build trends data
        trends = []
        for date_str in all_dates:
            data_point = {"date": date_str}
            for agent in sorted_agents:
                data_point[agent] = daily_counts[date_str].get(agent, 0)
            trends.append(data_point)

        return {
            "trends": trends,
            "agents": sorted_agents,
            "agent_totals": dict(agent_totals),
            "total_runs": len(runs),
        }

    except Exception as e:
        logger.error(f"Error fetching DISCo analytics: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
