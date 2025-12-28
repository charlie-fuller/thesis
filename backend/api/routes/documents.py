"""
Document management routes
Handles document upload, processing, retrieval, and deletion
"""
import asyncio
import json
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from auth import get_current_user, require_admin
from config import get_default_client_id
from database import get_supabase
from document_processor import process_document
from logger_config import get_logger
from validation import validate_file_size, validate_file_upload, validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])
supabase = get_supabase()
SUPABASE_URL = os.environ.get("SUPABASE_URL")


# ============================================================================
# Document Upload & Processing
# ============================================================================

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    agent_ids: Optional[str] = Form(None),  # JSON array of agent IDs, or empty for global
    current_user: dict = Depends(get_current_user)
):
    """Upload a document to Supabase Storage and create database record.

    Args:
        file: The file to upload
        agent_ids: JSON array of agent IDs to link the document to (e.g., '["uuid1", "uuid2"]').
                   If empty/null, document is global (available to all agents via RAG).
    """
    try:
        # Validate file
        validate_file_upload(file)

        # Read file content
        file_content = await file.read()
        validate_file_size(file_content)

        # Parse agent_ids if provided
        parsed_agent_ids: List[str] = []
        if agent_ids and agent_ids.strip():
            try:
                parsed_agent_ids = json.loads(agent_ids)
                if not isinstance(parsed_agent_ids, list):
                    parsed_agent_ids = [parsed_agent_ids] if parsed_agent_ids else []
            except json.JSONDecodeError:
                # Maybe it's a single ID
                parsed_agent_ids = [agent_ids] if agent_ids else []

        # Auto-assign default client
        client_id = current_user.get('client_id') or get_default_client_id()
        user_id = current_user['id']

        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'txt'
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        storage_path = f"{client_id}/{unique_filename}"

        # Upload to Supabase Storage
        logger.info(f"Uploading {file.filename} to storage: {storage_path}")

        upload_result = await asyncio.to_thread(
            lambda: supabase.storage.from_('documents').upload(
                storage_path,
                file_content,
                file_options={"content-type": file.content_type or "application/octet-stream"}
            )
        )

        # Get storage URL for the document
        storage_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"

        # Create database record
        # Note: If document is linked to specific agents, it's agent-specific.
        # If not linked to any agent (parsed_agent_ids empty), it's global (available to all).
        doc_record = {
            'client_id': client_id,
            'uploaded_by': user_id,
            'filename': file.filename,
            'storage_path': storage_path,
            'storage_url': storage_url,
            'mime_type': file.content_type or "application/octet-stream",
            'file_size': len(file_content),
            'processed': False  # Will be set to True after processing completes
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('documents').insert(doc_record).execute()
        )

        document = result.data[0]
        document_id = document['id']

        logger.info(f"Document uploaded: {document_id}")

        # Link to specific agents if provided
        linked_agents = []
        if parsed_agent_ids:
            for agent_id in parsed_agent_ids:
                try:
                    validate_uuid(agent_id, "agent_id")
                    link_result = await asyncio.to_thread(
                        lambda aid=agent_id: supabase.table('agent_knowledge_base').insert({
                            'agent_id': aid,
                            'document_id': document_id,
                            'added_by': user_id,
                            'priority': 0
                        }).execute()
                    )
                    linked_agents.append(agent_id)
                    logger.info(f"Linked document {document_id} to agent {agent_id}")
                except Exception as link_error:
                    logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        # Automatically trigger processing in background
        background_tasks.add_task(process_document, document_id)
        logger.info(f"Processing queued for document: {document_id}")

        # Determine if global (no specific agents) or agent-specific
        is_global = len(parsed_agent_ids) == 0

        return {
            'success': True,
            'document_id': document_id,
            'filename': file.filename,
            'is_global': is_global,
            'linked_agents': linked_agents,
            'message': 'Document uploaded successfully. Processing started in background.'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# Save Chat Response to KB
# ============================================================================
# NOTE: This endpoint MUST be defined BEFORE any /{document_id}/* routes
# to avoid the path parameter capturing "save-from-chat" as a document_id

class SaveFromChatRequest(BaseModel):
    """Request body for saving a chat response to the knowledge base."""
    title: str
    content: str
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None  # None = global, [] = global, [...] = agent-specific


@router.post("/save-from-chat")
async def save_from_chat(
    request: SaveFromChatRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Save a chat response as a markdown document in the knowledge base.

    Args:
        request.title: Document title
        request.content: The markdown content to save
        request.message_id: Optional source message ID for reference
        request.conversation_id: Optional source conversation ID for reference
        request.agent_ids: List of agent IDs to link to, or None/empty for global

    Returns:
        Document ID and status
    """
    try:
        # Validate content
        if not request.content or not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        if not request.title or not request.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        client_id = current_user.get('client_id') or get_default_client_id()
        user_id = current_user['id']

        # Create markdown content with metadata header
        markdown_content = f"""# {request.title}

{request.content}

---
*Saved from chat on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        # Generate unique filename
        safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in request.title)[:50]
        unique_filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.md"
        storage_path = f"{client_id}/{unique_filename}"

        # Convert content to bytes
        file_content = markdown_content.encode('utf-8')

        # Upload to Supabase Storage
        logger.info(f"Saving chat response to storage: {storage_path}")

        upload_result = await asyncio.to_thread(
            lambda: supabase.storage.from_('documents').upload(
                storage_path,
                file_content,
                file_options={"content-type": "text/markdown"}
            )
        )

        # Get storage URL
        storage_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"

        # Create database record with source metadata
        doc_metadata = {}
        if request.message_id:
            doc_metadata['source_message_id'] = request.message_id
        if request.conversation_id:
            doc_metadata['source_conversation_id'] = request.conversation_id
        doc_metadata['saved_from_chat'] = True

        doc_record = {
            'client_id': client_id,
            'uploaded_by': user_id,
            'filename': unique_filename,
            'storage_path': storage_path,
            'storage_url': storage_url,
            'mime_type': 'text/markdown',
            'file_size': len(file_content),
            'processed': False,
            'metadata': doc_metadata
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('documents').insert(doc_record).execute()
        )

        document = result.data[0]
        document_id = document['id']

        logger.info(f"Chat response saved as document: {document_id}")

        # Link to specific agents if provided
        linked_agents = []
        parsed_agent_ids = request.agent_ids or []

        if parsed_agent_ids:
            for agent_id in parsed_agent_ids:
                try:
                    validate_uuid(agent_id, "agent_id")
                    link_result = await asyncio.to_thread(
                        lambda aid=agent_id: supabase.table('agent_knowledge_base').insert({
                            'agent_id': aid,
                            'document_id': document_id,
                            'added_by': user_id,
                            'priority': 0
                        }).execute()
                    )
                    linked_agents.append(agent_id)
                    logger.info(f"Linked document {document_id} to agent {agent_id}")
                except Exception as link_error:
                    logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        # Trigger processing in background
        background_tasks.add_task(process_document, document_id)
        logger.info(f"Processing queued for saved document: {document_id}")

        is_global = len(parsed_agent_ids) == 0

        return {
            'success': True,
            'document_id': document_id,
            'filename': unique_filename,
            'is_global': is_global,
            'linked_agents': linked_agents,
            'message': 'Chat response saved to knowledge base. Processing started.'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Save from chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


# ============================================================================
# Document Processing
# ============================================================================

@router.post("/{document_id}/process")
async def process_document_endpoint(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Trigger document processing (chunking and embedding)"""
    try:
        validate_uuid(document_id, "document_id")

        # Start processing in background
        background_tasks.add_task(process_document, document_id)

        return {
            'success': True,
            'message': 'Document processing started',
            'document_id': document_id
        }

    except Exception as e:
        logger.error(f"❌ Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Document Retrieval
# ============================================================================

@router.get("/{document_id}")
async def get_document_metadata(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document metadata"""
    try:
        validate_uuid(document_id, "document_id")

        result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('*')\
                .eq('id', document_id)\
                .single()\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = result.data

        # Authorization check: user can only access their own documents (unless admin)
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")

        return {
            'success': True,
            'document': document
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Admin Document Management
# ============================================================================

@router.get("")
async def list_all_documents(
    current_user: dict = Depends(require_admin),
    limit: int = 50,
    offset: int = 0
):
    """List all documents (admin only)"""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('*, clients(name), users!documents_user_id_fkey(email)')\
                .order('uploaded_at', desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
        )

        return {
            'success': True,
            'documents': result.data,
            'limit': limit,
            'offset': offset
        }

    except Exception as e:
        logger.error(f"❌ Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/details")
async def get_document_details(
    document_id: str,
    current_user: dict = Depends(require_admin)
):
    """Get detailed document information including chunks (admin only)"""
    try:
        validate_uuid(document_id, "document_id")

        # Get document
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('*')\
                .eq('id', document_id)\
                .single()\
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get chunks
        chunks_result = await asyncio.to_thread(
            lambda: supabase.table('document_chunks')\
                .select('id, chunk_index, content')\
                .eq('document_id', document_id)\
                .order('chunk_index')\
                .execute()
        )

        return {
            'success': True,
            'document': doc_result.data,
            'chunks': chunks_result.data,
            'chunk_count': len(chunks_result.data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching document details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Document Deletion
# ============================================================================

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document and all its chunks"""
    try:
        validate_uuid(document_id, "document_id")

        # Get document to check ownership
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('*')\
                .eq('id', document_id)\
                .single()\
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data

        # Authorization check
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")

        # Delete chunks first
        await asyncio.to_thread(
            lambda: supabase.table('document_chunks')\
                .delete()\
                .eq('document_id', document_id)\
                .execute()
        )

        # Delete from storage
        if document.get('storage_path'):
            try:
                await asyncio.to_thread(
                    lambda: supabase.storage.from_('documents').remove([document['storage_path']])
                )
            except Exception as e:
                logger.warning(f"Could not delete from storage: {e}")

        # Delete document record
        await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .delete()\
                .eq('id', document_id)\
                .execute()
        )

        logger.info(f"✅ Document deleted: {document_id}")

        return {
            'success': True,
            'message': 'Document deleted successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bulk")
async def bulk_delete_documents(
    document_ids: List[str],
    current_user: dict = Depends(require_admin)
):
    """Delete multiple documents (admin only)"""
    try:
        deleted_count = 0
        errors = []

        for doc_id in document_ids:
            try:
                validate_uuid(doc_id, "document_id")

                # Delete chunks
                await asyncio.to_thread(
                    lambda: supabase.table('document_chunks')\
                        .delete()\
                        .eq('document_id', doc_id)\
                        .execute()
                )

                # Delete document
                await asyncio.to_thread(
                    lambda: supabase.table('documents')\
                        .delete()\
                        .eq('id', doc_id)\
                        .execute()
                )

                deleted_count += 1

            except Exception as e:
                errors.append({'document_id': doc_id, 'error': str(e)})

        return {
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"❌ Bulk delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Document Download
# ============================================================================

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate a signed URL for document download"""
    try:
        validate_uuid(document_id, "document_id")

        # Get document
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('*')\
                .eq('id', document_id)\
                .single()\
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data

        # Authorization check
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to download this document")

        # Generate signed URL (1 hour expiry)
        signed_url = await asyncio.to_thread(
            lambda: supabase.storage.from_('documents').create_signed_url(
                document['storage_path'],
                3600  # 1 hour
            )
        )

        return {
            'success': True,
            'download_url': signed_url['signedURL'],
            'expires_in': 3600
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating download URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
