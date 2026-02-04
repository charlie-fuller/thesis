"""Document upload routes."""

import asyncio
import json
import os
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

from auth import get_current_user
from config import get_default_client_id
from database import get_supabase
from document_processor import process_document, process_document_with_classification
from logger_config import get_logger
from validation import (
    validate_file_magic,
    validate_file_size,
    validate_file_upload,
    validate_uuid,
)

from ._shared import SaveFromChatRequest, limiter

logger = get_logger(__name__)
router = APIRouter()
supabase = get_supabase()
SUPABASE_URL = os.environ.get("SUPABASE_URL")


@router.post("/upload")
@limiter.limit("30/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    agent_ids: Optional[str] = Form(None),
    auto_classify: Optional[str] = Form("true"),
    original_date: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Upload a document to Supabase Storage and create database record.

    Args:
        request: FastAPI request object for rate limiting.
        background_tasks: FastAPI background tasks for async processing.
        file: The file to upload.
        agent_ids: JSON array of agent IDs to link the document to.
        auto_classify: If "true" and no agent_ids, auto-classify document.
        original_date: The actual date of the document content (YYYY-MM-DD).
        current_user: Injected by FastAPI dependency.
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

        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        # Generate unique filename
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "txt"
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        storage_path = f"{client_id}/{unique_filename}"

        logger.info(f"Uploading {file.filename} to storage: {storage_path}")

        await asyncio.to_thread(
            lambda: supabase.storage.from_("documents").upload(
                storage_path,
                file_content,
                file_options={"content-type": file.content_type or "application/octet-stream"},
            )
        )

        storage_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"

        # Parse original_date if provided
        parsed_original_date = None
        if original_date and original_date.strip():
            try:
                from datetime import datetime

                parsed_original_date = datetime.strptime(original_date.strip(), "%Y-%m-%d").date().isoformat()
            except ValueError:
                logger.warning(f"Invalid original_date format: {original_date}, expected YYYY-MM-DD")

        doc_record = {
            "client_id": client_id,
            "uploaded_by": user_id,
            "filename": file.filename,
            "storage_path": storage_path,
            "storage_url": storage_url,
            "mime_type": file.content_type or "application/octet-stream",
            "file_size": len(file_content),
            "processed": False,
        }

        if parsed_original_date:
            doc_record["original_date"] = parsed_original_date

        result = await asyncio.to_thread(lambda: supabase.table("documents").insert(doc_record).execute())

        document = result.data[0]
        document_id = document["id"]

        logger.info(f"Document uploaded: {document_id}")

        # Link to specific agents if provided
        linked_agents = []
        if parsed_agent_ids:
            for agent_id in parsed_agent_ids:
                try:
                    validate_uuid(agent_id, "agent_id")
                    await asyncio.to_thread(
                        lambda aid=agent_id: supabase.table("agent_knowledge_base")
                        .insert(
                            {
                                "agent_id": aid,
                                "document_id": document_id,
                                "added_by": user_id,
                                "priority": 0,
                            }
                        )
                        .execute()
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
    current_user: dict = Depends(get_current_user),
):
    """Save a chat response as a markdown document in the knowledge base."""
    try:
        if not save_data.content or not save_data.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        if not save_data.title or not save_data.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        client_id = current_user.get("client_id") or get_default_client_id()
        user_id = current_user["id"]

        markdown_content = f"""# {save_data.title}

{save_data.content}

---
*Saved from chat on {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""

        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in save_data.title)[:50]
        unique_filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.md"
        storage_path = f"{client_id}/{unique_filename}"

        file_content = markdown_content.encode("utf-8")

        logger.info(f"Saving chat response to storage: {storage_path}")

        await asyncio.to_thread(
            lambda: supabase.storage.from_("documents").upload(
                storage_path, file_content, file_options={"content-type": "text/markdown"}
            )
        )

        storage_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"

        doc_record = {
            "client_id": client_id,
            "uploaded_by": user_id,
            "title": save_data.title.strip(),
            "filename": unique_filename,
            "storage_path": storage_path,
            "storage_url": storage_url,
            "mime_type": "text/markdown",
            "file_size": len(file_content),
            "processed": False,
        }

        result = await asyncio.to_thread(lambda: supabase.table("documents").insert(doc_record).execute())

        document = result.data[0]
        document_id = document["id"]

        logger.info(f"Chat response saved as document: {document_id}")

        linked_agents = []
        parsed_agent_ids = save_data.agent_ids or []

        if parsed_agent_ids:
            for agent_id in parsed_agent_ids:
                try:
                    validate_uuid(agent_id, "agent_id")
                    await asyncio.to_thread(
                        lambda aid=agent_id: supabase.table("agent_knowledge_base")
                        .insert(
                            {
                                "agent_id": aid,
                                "document_id": document_id,
                                "added_by": user_id,
                                "priority": 0,
                            }
                        )
                        .execute()
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
