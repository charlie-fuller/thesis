"""Document upload routes."""

import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

import json
import pb_client as pb
from document_processor import process_document, process_document_with_classification
from logger_config import get_logger
from repositories import documents as doc_repo
from validation import (
    validate_file_magic,
    validate_file_size,
    validate_file_upload,
    validate_uuid,
)

from ._shared import ExportToKBRequest, SaveFromChatRequest, limiter

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload")
@limiter.limit("30/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    agent_ids: Optional[str] = Form(None),
    auto_classify: Optional[str] = Form("true"),
    original_date: Optional[str] = Form(None),
):
    """Upload a document and create database record.

    Args:
        request: FastAPI request object for rate limiting.
        background_tasks: FastAPI background tasks for async processing.
        file: The file to upload.
        agent_ids: JSON array of agent IDs to link the document to.
        auto_classify: If "true" and no agent_ids, auto-classify document.
        original_date: The actual date of the document content (YYYY-MM-DD).
    """
    try:
        validate_file_upload(file)
        file_content = await file.read()
        validate_file_size(file_content)
        validate_file_magic(file_content, file.content_type)

        # Parse agent_ids if provided
        parsed_agent_ids = []
        if agent_ids and agent_ids.strip():
            try:
                parsed_agent_ids = json.loads(agent_ids)
                if not isinstance(parsed_agent_ids, list):
                    parsed_agent_ids = [parsed_agent_ids] if parsed_agent_ids else []
            except json.JSONDecodeError:
                parsed_agent_ids = [agent_ids] if agent_ids else []

        # Generate unique filename
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "txt"
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        storage_path = f"uploads/{unique_filename}"

        # TODO: PocketBase file storage migration pending
        # For now, store the path but skip actual storage upload
        logger.info(f"Uploading {file.filename} -- storage upload deferred (PocketBase migration pending)")

        storage_url = ""

        # Parse original_date if provided
        parsed_original_date = None
        if original_date and original_date.strip():
            try:
                from datetime import datetime

                parsed_original_date = datetime.strptime(original_date.strip(), "%Y-%m-%d").date().isoformat()
            except ValueError:
                logger.warning(f"Invalid original_date format: {original_date}, expected YYYY-MM-DD")

        doc_data = {
            "filename": file.filename,
            "storage_path": storage_path,
            "storage_url": storage_url,
            "mime_type": file.content_type or "application/octet-stream",
            "file_size": len(file_content),
            "processed": False,
        }

        if parsed_original_date:
            doc_data["original_date"] = parsed_original_date

        document = doc_repo.create_document(doc_data)
        document_id = document["id"]

        logger.info(f"Document uploaded: {document_id}")

        # Link to specific agents if provided
        linked_agents = []
        if parsed_agent_ids:
            for agent_id in parsed_agent_ids:
                try:
                    validate_uuid(agent_id, "agent_id")
                    pb.create_record(
                        "agent_knowledge_base",
                        {
                            "agent_id": agent_id,
                            "document_id": document_id,
                            "priority": 0,
                        },
                    )
                    linked_agents.append(agent_id)
                    logger.info(f"Linked document {document_id} to agent {agent_id}")
                except Exception as link_error:
                    logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        # Determine if auto-classification should run
        should_auto_classify = len(parsed_agent_ids) == 0 and auto_classify and auto_classify.lower() == "true"

        if should_auto_classify:

            def process_with_classify_sync():
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(process_document_with_classification(document_id, auto_classify=True))
                finally:
                    loop.close()

            background_tasks.add_task(process_with_classify_sync)
            logger.info(f"Processing with auto-classification queued for document: {document_id}")
        else:
            background_tasks.add_task(process_document, document_id)
            logger.info(f"Processing queued for document: {document_id}")

        is_global = len(parsed_agent_ids) == 0

        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "is_global": is_global,
            "linked_agents": linked_agents,
            "auto_classify": should_auto_classify,
            "message": "Document uploaded successfully. Processing started in background."
            + (" Auto-classification enabled." if should_auto_classify else ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from None


@router.post("/save-from-chat")
@limiter.limit("30/minute")
async def save_from_chat(
    request: Request,
    save_data: SaveFromChatRequest,
    background_tasks: BackgroundTasks,
):
    """Save a chat response as a markdown document in the knowledge base."""
    try:
        if not save_data.content or not save_data.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        if not save_data.title or not save_data.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        markdown_content = f"""# {save_data.title}

{save_data.content}

---
*Saved from chat on {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""

        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in save_data.title)[:50]
        unique_filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.md"
        storage_path = f"chat-saves/{unique_filename}"

        file_content = markdown_content.encode("utf-8")

        # TODO: PocketBase file storage migration pending
        logger.info(f"Saving chat response -- storage upload deferred (PocketBase migration pending): {storage_path}")

        storage_url = ""

        doc_data = {
            "title": save_data.title.strip(),
            "filename": unique_filename,
            "storage_path": storage_path,
            "storage_url": storage_url,
            "mime_type": "text/markdown",
            "file_size": len(file_content),
            "processed": False,
        }

        document = doc_repo.create_document(doc_data)
        document_id = document["id"]

        logger.info(f"Chat response saved as document: {document_id}")

        linked_agents = []
        parsed_agent_ids = save_data.agent_ids or []

        if parsed_agent_ids:
            for agent_id in parsed_agent_ids:
                try:
                    validate_uuid(agent_id, "agent_id")
                    pb.create_record(
                        "agent_knowledge_base",
                        {
                            "agent_id": agent_id,
                            "document_id": document_id,
                            "priority": 0,
                        },
                    )
                    linked_agents.append(agent_id)
                    logger.info(f"Linked document {document_id} to agent {agent_id}")
                except Exception as link_error:
                    logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        background_tasks.add_task(process_document, document_id)
        logger.info(f"Processing queued for saved document: {document_id}")

        is_global = len(parsed_agent_ids) == 0

        return {
            "success": True,
            "document_id": document_id,
            "filename": unique_filename,
            "is_global": is_global,
            "linked_agents": linked_agents,
            "message": "Chat response saved to knowledge base. Processing started.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save from chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}") from None


@router.post("/export-to-kb")
@limiter.limit("30/minute")
async def export_to_kb(
    request: Request,
    export_data: ExportToKBRequest,
    background_tasks: BackgroundTasks,
):
    """Export content to KB and optionally link to a project and/or initiative."""
    try:
        if not export_data.content or not export_data.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        if not export_data.title or not export_data.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        # Build markdown with metadata header
        meta_lines = [f"# {export_data.title}"]
        if export_data.location:
            meta_lines.append(f"**Location:** {export_data.location}")
        meta_lines.append("")
        meta_lines.append(export_data.content)
        meta_lines.append("")
        meta_lines.append("---")
        now_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
        meta_lines.append(f"*Exported to KB on {now_str}*")
        markdown_content = "\n".join(meta_lines)

        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in export_data.title)[:50]
        unique_filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.md"

        # Use location as storage subfolder if provided
        if export_data.location:
            safe_location = export_data.location.strip("/").replace("..", "")
            storage_path = f"exports/{safe_location}/{unique_filename}"
        else:
            storage_path = f"exports/{unique_filename}"

        file_content = markdown_content.encode("utf-8")

        # TODO: PocketBase file storage migration pending
        logger.info(f"Exporting to KB -- storage upload deferred (PocketBase migration pending): {storage_path}")

        storage_url = ""

        doc_data = {
            "title": export_data.title.strip(),
            "filename": unique_filename,
            "storage_path": storage_path,
            "storage_url": storage_url,
            "mime_type": "text/markdown",
            "file_size": len(file_content),
            "processed": False,
        }

        document = doc_repo.create_document(doc_data)
        document_id = document["id"]

        logger.info(f"Export saved as document: {document_id}")

        # Link to agents if provided
        linked_agents = []
        for agent_id in (export_data.agent_ids or []):
            try:
                validate_uuid(agent_id, "agent_id")
                pb.create_record(
                    "agent_knowledge_base",
                    {"agent_id": agent_id, "document_id": document_id, "priority": 0},
                )
                linked_agents.append(agent_id)
            except Exception as link_error:
                logger.warning(f"Failed to link to agent {agent_id}: {link_error}")

        # Link to project if provided
        linked_project = None
        if export_data.project_id:
            try:
                validate_uuid(export_data.project_id, "project_id")
                # Upsert: check if exists first
                existing = pb.get_first(
                    "project_documents",
                    filter=f"project_id='{pb.escape_filter(export_data.project_id)}' && document_id='{pb.escape_filter(document_id)}'",
                )
                if not existing:
                    pb.create_record(
                        "project_documents",
                        {"project_id": export_data.project_id, "document_id": document_id},
                    )
                linked_project = export_data.project_id
                logger.info(f"Linked export {document_id} to project {export_data.project_id}")
            except Exception as link_error:
                logger.warning(f"Failed to link to project: {link_error}")

        # Link to initiative if provided
        linked_initiative = None
        if export_data.initiative_id:
            try:
                validate_uuid(export_data.initiative_id, "initiative_id")
                existing = pb.get_first(
                    "disco_initiative_documents",
                    filter=f"initiative_id='{pb.escape_filter(export_data.initiative_id)}' && document_id='{pb.escape_filter(document_id)}'",
                )
                if not existing:
                    pb.create_record(
                        "disco_initiative_documents",
                        {"initiative_id": export_data.initiative_id, "document_id": document_id},
                    )
                linked_initiative = export_data.initiative_id
                logger.info(f"Linked export {document_id} to initiative {export_data.initiative_id}")
            except Exception as link_error:
                logger.warning(f"Failed to link to initiative: {link_error}")

        # Queue processing (chunking + embedding)
        background_tasks.add_task(process_document, document_id)

        return {
            "success": True,
            "document_id": document_id,
            "filename": unique_filename,
            "linked_project": linked_project,
            "linked_initiative": linked_initiative,
            "linked_agents": linked_agents,
            "message": "Exported to KB. Processing started.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export to KB error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}") from None
