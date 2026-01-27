"""
Document management routes
Handles document upload, processing, retrieval, deletion, and save-from-chat
"""
import asyncio
import json
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_current_user, require_admin
from config import get_default_client_id
from database import get_supabase
from document_processor import process_document, process_document_with_classification
from logger_config import get_logger
from validation import validate_file_magic, validate_file_size, validate_file_upload, validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()
SUPABASE_URL = os.environ.get("SUPABASE_URL")


# ============================================================================
# Document Upload & Processing
# ============================================================================

@router.post("/upload")
@limiter.limit("30/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    agent_ids: Optional[str] = Form(None),  # JSON array of agent IDs, or empty for global
    auto_classify: Optional[str] = Form("true"),  # Enable auto-classification when no agents specified
    original_date: Optional[str] = Form(None),  # Original document date (e.g., meeting date) in YYYY-MM-DD format
    current_user: dict = Depends(get_current_user)
):
    """Upload a document to Supabase Storage and create database record.

    Args:
        file: The file to upload
        agent_ids: JSON array of agent IDs to link the document to (e.g., '["uuid1", "uuid2"]').
                   If empty/null, document is global (available to all agents via RAG).
        auto_classify: If "true" and no agent_ids provided, auto-classify document for agent relevance.
                       Auto-tags confident matches, flags ambiguous for user review.
        original_date: The actual date of the document content (e.g., meeting date for transcripts).
                       Format: YYYY-MM-DD. If not provided, can be set later via document update.
    """
    try:
        # Validate file
        validate_file_upload(file)

        # Read file content
        file_content = await file.read()
        validate_file_size(file_content)

        # Validate file signature (magic numbers) to prevent disguised files
        validate_file_magic(file_content, file.content_type)

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

        # Parse original_date if provided
        parsed_original_date = None
        if original_date and original_date.strip():
            try:
                # Validate date format (YYYY-MM-DD)
                from datetime import datetime
                parsed_original_date = datetime.strptime(original_date.strip(), '%Y-%m-%d').date().isoformat()
            except ValueError:
                logger.warning(f"Invalid original_date format: {original_date}, expected YYYY-MM-DD")

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

        # Add original_date if provided
        if parsed_original_date:
            doc_record['original_date'] = parsed_original_date

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

        # Determine if auto-classification should run
        # Only auto-classify if no agents specified AND auto_classify is enabled
        should_auto_classify = (
            len(parsed_agent_ids) == 0 and
            auto_classify and
            auto_classify.lower() == "true"
        )

        # Automatically trigger processing in background
        if should_auto_classify:
            # Use sync wrapper for async processing with classification
            def process_with_classify_sync():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        process_document_with_classification(document_id, auto_classify=True)
                    )
                finally:
                    loop.close()

            background_tasks.add_task(process_with_classify_sync)
            logger.info(f"Processing with auto-classification queued for document: {document_id}")
        else:
            # Standard processing without classification
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
            'auto_classify': should_auto_classify,
            'message': 'Document uploaded successfully. Processing started in background.' +
                       (' Auto-classification enabled.' if should_auto_classify else '')
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
@limiter.limit("30/minute")
async def save_from_chat(
    request: Request,
    save_data: SaveFromChatRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Save a chat response as a markdown document in the knowledge base.

    NOTE: This endpoint was added 2025-12-28. If you see 405 errors, Railway deploy failed.

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
        if not save_data.content or not save_data.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        if not save_data.title or not save_data.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        client_id = current_user.get('client_id') or get_default_client_id()
        user_id = current_user['id']

        # Create markdown content with metadata header
        markdown_content = f"""# {save_data.title}

{save_data.content}

---
*Saved from chat on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        # Generate unique filename
        safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in save_data.title)[:50]
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

        # Create database record with title for display
        doc_record = {
            'client_id': client_id,
            'uploaded_by': user_id,
            'title': save_data.title.strip(),  # Store original title for display
            'filename': unique_filename,
            'storage_path': storage_path,
            'storage_url': storage_url,
            'mime_type': 'text/markdown',
            'file_size': len(file_content),
            'processed': False
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('documents').insert(doc_record).execute()
        )

        document = result.data[0]
        document_id = document['id']

        logger.info(f"Chat response saved as document: {document_id}")

        # Link to specific agents if provided
        linked_agents = []
        parsed_agent_ids = save_data.agent_ids or []

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
# Static Routes (must be before parameterized routes)
# ============================================================================

@router.get("/pending-reviews")
async def get_pending_classification_reviews(
    current_user: dict = Depends(get_current_user)
):
    """Get all documents with pending classification reviews for the current user.

    Returns documents that were auto-classified but need user confirmation.
    """
    try:
        # Get documents with pending reviews
        result = await asyncio.to_thread(
            lambda: supabase.table('document_classifications')
                .select('document_id, detected_type, review_reason, raw_scores, created_at, documents(id, filename, uploaded_by)')
                .eq('requires_user_review', True)
                .eq('status', 'needs_review')
                .order('created_at', desc=True)
                .execute()
        )

        pending_reviews = []
        for item in result.data or []:
            doc = item.get('documents')
            if not doc:
                continue

            pending_reviews.append({
                'document_id': item['document_id'],
                'filename': doc.get('filename'),
                'detected_type': item.get('detected_type'),
                'review_reason': item.get('review_reason'),
                'suggested_agents': item.get('raw_scores', {}),
                'created_at': item.get('created_at')
            })

        return {
            'success': True,
            'pending_reviews': pending_reviews,
            'count': len(pending_reviews)
        }

    except Exception as e:
        # Log but return empty - this is a non-critical feature
        logger.warning(f"Error getting pending reviews (returning empty): {e}")
        return {
            'success': True,
            'pending_reviews': [],
            'count': 0
        }


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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Document Retrieval
# ============================================================================

@router.get("/by-folder")
async def get_documents_by_folder(
    folder_path: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all KB documents from a specific Obsidian folder path.

    Args:
        folder_path: The folder path prefix to match (e.g., "Legal Ops/Ashley Adams")

    Returns:
        List of documents whose obsidian_file_path starts with the given folder path
    """
    try:
        if not folder_path or not folder_path.strip():
            raise HTTPException(status_code=400, detail="folder_path is required")

        folder_path = folder_path.strip()
        # Ensure folder path ends with / for prefix matching (unless it's the root)
        search_prefix = folder_path if folder_path.endswith('/') else f"{folder_path}/"

        # Query documents where obsidian_file_path starts with the folder path
        # Use ilike for case-insensitive matching
        result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, filename, title, obsidian_file_path, source_platform, uploaded_at, storage_url')
                .eq('source_platform', 'obsidian')
                .eq('uploaded_by', current_user['id'])
                .ilike('obsidian_file_path', f'{folder_path}%')
                .order('obsidian_file_path')
                .execute()
        )

        documents = result.data or []

        # Also get the full content for each document (for agent use)
        docs_with_content = []
        for doc in documents:
            # Get document content from chunks
            chunks_result = await asyncio.to_thread(
                lambda d=doc: supabase.table('document_chunks')
                    .select('content, chunk_index')
                    .eq('document_id', d['id'])
                    .order('chunk_index')
                    .execute()
            )

            content = '\n'.join([c['content'] for c in (chunks_result.data or [])])
            docs_with_content.append({
                **doc,
                'content': content
            })

        return {
            'success': True,
            'folder_path': folder_path,
            'count': len(docs_with_content),
            'documents': docs_with_content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching documents by folder: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/folders")
async def get_obsidian_folders(
    current_user: dict = Depends(get_current_user)
):
    """Get unique Obsidian folder paths for the current user.

    Returns:
        List of unique folder paths from the user's Obsidian documents
    """
    try:
        # Get all obsidian documents for this user
        result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('obsidian_file_path')
                .eq('source_platform', 'obsidian')
                .eq('uploaded_by', current_user['id'])
                .not_.is_('obsidian_file_path', 'null')
                .execute()
        )

        # Extract unique folder paths
        folders = set()
        for doc in (result.data or []):
            path = doc.get('obsidian_file_path', '')
            if path and '/' in path:
                # Get all parent folders
                parts = path.split('/')
                for i in range(1, len(parts)):
                    folders.add('/'.join(parts[:i]))

        # Sort folders alphabetically
        sorted_folders = sorted(folders)

        return {
            'success': True,
            'folders': sorted_folders
        }

    except Exception as e:
        logger.error(f"Error fetching Obsidian folders: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document content by reconstructing from chunks.

    Returns the full document content by concatenating all chunks in order.
    This endpoint is available to document owners and admins.
    """
    try:
        validate_uuid(document_id, "document_id")

        # Get document metadata
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('id, filename, title, mime_type, uploaded_by, storage_path')\
                .eq('id', document_id)\
                .single()\
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data

        # Authorization check: user can only access their own documents (unless admin)
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")

        # Get all chunks ordered by chunk_index
        chunks_result = await asyncio.to_thread(
            lambda: supabase.table('document_chunks')\
                .select('content, chunk_index')\
                .eq('document_id', document_id)\
                .order('chunk_index')\
                .execute()
        )

        # Reconstruct content from chunks
        if chunks_result.data:
            # Join chunks with double newlines to preserve readability
            content = "\n\n".join(chunk['content'] for chunk in chunks_result.data)
        else:
            content = ""

        return {
            'success': True,
            'document': {
                'id': document['id'],
                'filename': document.get('filename'),
                'title': document.get('title'),
                'mime_type': document.get('mime_type'),
            },
            'content': content,
            'chunk_count': len(chunks_result.data) if chunks_result.data else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching document content: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Document Deletion
# ============================================================================

@router.delete("/{document_id}")
@limiter.limit("30/minute")
async def delete_document(
    request: Request,
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.delete("/bulk")
@limiter.limit("10/minute")
async def bulk_delete_documents(
    request: Request,
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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


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
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Document Agent Assignments
# ============================================================================

@router.get("/{document_id}/agents")
async def get_document_agents(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the agents linked to a document.

    Returns:
        is_global: True if document has no agent links (available to all agents)
        linked_agents: List of agent IDs linked to this document
    """
    try:
        validate_uuid(document_id, "document_id")

        # Verify document exists and user has access
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to view this document")

        # Get agent links
        links_result = await asyncio.to_thread(
            lambda: supabase.table('agent_knowledge_base')
                .select('agent_id, agents(id, name, display_name)')
                .eq('document_id', document_id)
                .execute()
        )

        linked_agents = []
        for link in links_result.data or []:
            if link.get('agents'):
                linked_agents.append({
                    'id': link['agents']['id'],
                    'name': link['agents']['name'],
                    'display_name': link['agents']['display_name']
                })

        return {
            'success': True,
            'document_id': document_id,
            'is_global': len(linked_agents) == 0,
            'linked_agents': linked_agents
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document agents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


class UpdateDocumentAgentsRequest(BaseModel):
    """Request body for updating document agent assignments."""
    agent_ids: List[str]  # Empty list = global (remove all links)


@router.put("/{document_id}/agents")
async def update_document_agents(
    document_id: str,
    request: UpdateDocumentAgentsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update the agents linked to a document.

    Args:
        agent_ids: List of agent IDs to link. Empty list makes document global.

    Returns:
        Updated agent links
    """
    try:
        validate_uuid(document_id, "document_id")

        # Verify document exists and user has access
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this document")

        user_id = current_user['id']

        # Delete all existing links for this document
        await asyncio.to_thread(
            lambda: supabase.table('agent_knowledge_base')
                .delete()
                .eq('document_id', document_id)
                .execute()
        )

        # Create new links
        linked_agents = []
        for agent_id in request.agent_ids:
            try:
                validate_uuid(agent_id, "agent_id")

                # Verify agent exists
                agent_result = await asyncio.to_thread(
                    lambda aid=agent_id: supabase.table('agents')
                        .select('id, name, display_name')
                        .eq('id', aid)
                        .single()
                        .execute()
                )

                if not agent_result.data:
                    logger.warning(f"Agent {agent_id} not found, skipping")
                    continue

                # Create link
                await asyncio.to_thread(
                    lambda aid=agent_id: supabase.table('agent_knowledge_base').insert({
                        'agent_id': aid,
                        'document_id': document_id,
                        'added_by': user_id,
                        'priority': 0
                    }).execute()
                )

                linked_agents.append({
                    'id': agent_result.data['id'],
                    'name': agent_result.data['name'],
                    'display_name': agent_result.data['display_name']
                })
                logger.info(f"Linked document {document_id} to agent {agent_id}")

            except Exception as link_error:
                logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        is_global = len(linked_agents) == 0

        return {
            'success': True,
            'document_id': document_id,
            'is_global': is_global,
            'linked_agents': linked_agents,
            'message': 'Global (all agents)' if is_global else f'Linked to {len(linked_agents)} agent(s)'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document agents: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Document Classification Endpoints
# ============================================================================

@router.get("/{document_id}/classification")
async def get_document_classification(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get classification results for a document.

    Returns classification status, suggested agents, and whether user review is needed.
    """
    try:
        validate_uuid(document_id, "document_id")

        # Verify document exists
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, filename')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get latest classification
        classification_result = await asyncio.to_thread(
            lambda: supabase.table('document_classifications')
                .select('*')
                .eq('document_id', document_id)
                .order('created_at', desc=True)
                .limit(1)
                .execute()
        )

        if not classification_result.data:
            return {
                'success': True,
                'document_id': document_id,
                'classification': None,
                'message': 'No classification found for this document'
            }

        classification = classification_result.data[0]

        # Get current agent links with relevance scores
        links_result = await asyncio.to_thread(
            lambda: supabase.table('agent_knowledge_base')
                .select('agent_id, relevance_score, classification_source, classification_confidence, user_confirmed, agents(id, name, display_name)')
                .eq('document_id', document_id)
                .execute()
        )

        linked_agents = []
        for link in links_result.data or []:
            if link.get('agents'):
                linked_agents.append({
                    'id': link['agents']['id'],
                    'name': link['agents']['name'],
                    'display_name': link['agents']['display_name'],
                    'relevance_score': link.get('relevance_score', 0),
                    'classification_source': link.get('classification_source', 'manual'),
                    'confidence': link.get('classification_confidence'),
                    'user_confirmed': link.get('user_confirmed', False)
                })

        return {
            'success': True,
            'document_id': document_id,
            'classification': {
                'id': classification['id'],
                'detected_type': classification.get('detected_type'),
                'method': classification.get('classification_method'),
                'status': classification.get('status'),
                'requires_user_review': classification.get('requires_user_review', False),
                'review_reason': classification.get('review_reason'),
                'raw_scores': classification.get('raw_scores', {}),
                'created_at': classification.get('created_at')
            },
            'linked_agents': linked_agents
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document classification: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


class ConfirmClassificationRequest(BaseModel):
    """Request body for confirming/modifying document classification."""
    agent_ids: List[str]  # Agent IDs to link (user's confirmed selection)
    relevance_scores: Optional[dict] = None  # Optional {agent_id: score} overrides


@router.post("/{document_id}/classification/confirm")
async def confirm_classification(
    document_id: str,
    request: ConfirmClassificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Confirm or modify auto-classification for a document.

    Called when user reviews and approves/modifies suggested agent tags.
    """
    try:
        validate_uuid(document_id, "document_id")

        # Verify document exists
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this document")

        user_id = current_user['id']

        # Delete all existing auto-classified links (keep manual ones)
        await asyncio.to_thread(
            lambda: supabase.table('agent_knowledge_base')
                .delete()
                .eq('document_id', document_id)
                .execute()
        )

        # Create confirmed links
        linked_agents = []
        for agent_id in request.agent_ids:
            try:
                validate_uuid(agent_id, "agent_id")

                # Get relevance score (from request override or default)
                relevance_score = 0.8  # Default for user-confirmed
                if request.relevance_scores and agent_id in request.relevance_scores:
                    relevance_score = request.relevance_scores[agent_id]

                # Verify agent exists
                agent_result = await asyncio.to_thread(
                    lambda aid=agent_id: supabase.table('agents')
                        .select('id, name, display_name')
                        .eq('id', aid)
                        .single()
                        .execute()
                )

                if not agent_result.data:
                    logger.warning(f"Agent {agent_id} not found, skipping")
                    continue

                # Create link with user confirmation
                await asyncio.to_thread(
                    lambda aid=agent_id, rs=relevance_score: supabase.table('agent_knowledge_base').insert({
                        'agent_id': aid,
                        'document_id': document_id,
                        'added_by': user_id,
                        'priority': 0,
                        'relevance_score': rs,
                        'classification_source': 'user_confirmed',
                        'classification_confidence': rs,
                        'user_confirmed': True
                    }).execute()
                )

                linked_agents.append({
                    'id': agent_result.data['id'],
                    'name': agent_result.data['name'],
                    'display_name': agent_result.data['display_name'],
                    'relevance_score': relevance_score
                })
                logger.info(f"User confirmed document {document_id} link to agent {agent_id}")

            except Exception as link_error:
                logger.warning(f"Failed to link document to agent {agent_id}: {link_error}")

        # Update classification status to reviewed
        await asyncio.to_thread(
            lambda: supabase.table('document_classifications')
                .update({
                    'status': 'reviewed',
                    'requires_user_review': False,
                    'reviewed_at': 'now()',
                    'reviewed_by': user_id
                })
                .eq('document_id', document_id)
                .execute()
        )

        return {
            'success': True,
            'document_id': document_id,
            'is_global': len(linked_agents) == 0,
            'linked_agents': linked_agents,
            'message': f'Classification confirmed with {len(linked_agents)} agent(s)'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming document classification: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Document Tags
# ============================================================================

@router.get("/{document_id}/tags")
async def get_document_tags(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all tags for a document.

    Returns:
        tags: List of tag objects with tag name and source (frontmatter/manual)
    """
    try:
        validate_uuid(document_id, "document_id")

        # Verify document exists and user has access
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to view this document")

        # Get tags
        tags_result = await asyncio.to_thread(
            lambda: supabase.table('document_tags')
                .select('id, tag, source, created_at')
                .eq('document_id', document_id)
                .order('created_at')
                .execute()
        )

        return {
            'success': True,
            'document_id': document_id,
            'tags': tags_result.data or []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document tags: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


class AddTagRequest(BaseModel):
    """Request body for adding a tag to a document."""
    tag: str


@router.post("/{document_id}/tags")
async def add_document_tag(
    document_id: str,
    request: AddTagRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a manual tag to a document.

    Args:
        tag: The tag text to add

    Returns:
        The created tag record
    """
    try:
        validate_uuid(document_id, "document_id")

        if not request.tag or not request.tag.strip():
            raise HTTPException(status_code=400, detail="Tag cannot be empty")

        tag = request.tag.strip()
        if len(tag) > 100:
            raise HTTPException(status_code=400, detail="Tag must be 100 characters or less")

        # Verify document exists and user has access
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this document")

        # Insert tag (upsert to handle duplicates)
        tag_result = await asyncio.to_thread(
            lambda: supabase.table('document_tags')
                .upsert({
                    'document_id': document_id,
                    'tag': tag,
                    'source': 'manual'
                }, on_conflict='document_id,tag')
                .execute()
        )

        logger.info(f"Added tag '{tag}' to document {document_id}")

        return {
            'success': True,
            'document_id': document_id,
            'tag': tag_result.data[0] if tag_result.data else {'tag': tag, 'source': 'manual'}
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding document tag: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.delete("/{document_id}/tags/{tag}")
async def remove_document_tag(
    document_id: str,
    tag: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a tag from a document.

    Note: Only manual tags can be removed. Frontmatter tags are controlled by
    the source Obsidian file.

    Args:
        tag: The tag text to remove
    """
    try:
        validate_uuid(document_id, "document_id")

        if not tag or not tag.strip():
            raise HTTPException(status_code=400, detail="Tag cannot be empty")

        tag = tag.strip()

        # Verify document exists and user has access
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this document")

        # Check if tag exists and is manual
        existing_tag = await asyncio.to_thread(
            lambda: supabase.table('document_tags')
                .select('id, source')
                .eq('document_id', document_id)
                .eq('tag', tag)
                .single()
                .execute()
        )

        if not existing_tag.data:
            raise HTTPException(status_code=404, detail="Tag not found")

        if existing_tag.data['source'] == 'frontmatter':
            raise HTTPException(
                status_code=400,
                detail="Cannot remove frontmatter tags. Edit the source Obsidian file instead."
            )

        # Delete the tag
        await asyncio.to_thread(
            lambda: supabase.table('document_tags')
                .delete()
                .eq('document_id', document_id)
                .eq('tag', tag)
                .execute()
        )

        logger.info(f"Removed tag '{tag}' from document {document_id}")

        return {
            'success': True,
            'document_id': document_id,
            'removed_tag': tag
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing document tag: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Document Metadata Updates
# ============================================================================

class OriginalDateUpdate(BaseModel):
    original_date: Optional[str] = None  # YYYY-MM-DD format or null to clear


class SyncCadenceUpdate(BaseModel):
    sync_cadence: str  # manual, daily, weekly, monthly


@router.patch("/{document_id}/original-date")
async def update_document_original_date(
    document_id: str,
    request: OriginalDateUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update the original date for a document (e.g., meeting date for transcripts).

    Args:
        original_date: The actual date of the document content in YYYY-MM-DD format,
                       or null to clear the date.
    """
    try:
        validate_uuid(document_id, "document_id")

        # Verify document exists and user has access
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this document")

        # Validate and parse date if provided
        parsed_date = None
        if request.original_date and request.original_date.strip():
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(request.original_date.strip(), '%Y-%m-%d').date().isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Please use YYYY-MM-DD format."
                )

        # Update the document
        await asyncio.to_thread(
            lambda: supabase.table('documents')
                .update({'original_date': parsed_date})
                .eq('id', document_id)
                .execute()
        )

        logger.info(f"Updated original_date for document {document_id}: {parsed_date}")

        return {
            'success': True,
            'document_id': document_id,
            'original_date': parsed_date
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document original_date: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.patch("/{document_id}/sync-cadence")
async def update_document_sync_cadence(
    document_id: str,
    request: SyncCadenceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update the sync cadence for a document (for Google Drive/Notion documents).

    Args:
        sync_cadence: How often to sync - manual, daily, weekly, or monthly.
    """
    try:
        validate_uuid(document_id, "document_id")

        # Validate sync_cadence value
        valid_cadences = ['manual', 'daily', 'weekly', 'monthly']
        if request.sync_cadence not in valid_cadences:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sync_cadence. Must be one of: {', '.join(valid_cadences)}"
            )

        # Verify document exists and user has access
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, uploaded_by, source_platform')
                .eq('id', document_id)
                .single()
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Authorization check
        document = doc_result.data
        if current_user['role'] != 'admin' and document['uploaded_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this document")

        # Update the document
        await asyncio.to_thread(
            lambda: supabase.table('documents')
                .update({'sync_cadence': request.sync_cadence})
                .eq('id', document_id)
                .execute()
        )

        logger.info(f"Updated sync_cadence for document {document_id}: {request.sync_cadence}")

        return {
            'success': True,
            'document_id': document_id,
            'sync_cadence': request.sync_cadence
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document sync_cadence: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")
