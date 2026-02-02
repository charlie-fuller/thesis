"""
User management routes
Handles user CRUD, prompts, and profile operations
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_current_user, require_admin
from config import get_default_client_id
from database import get_supabase
from logger_config import get_logger
from validation import generate_secure_password, validate_image_magic, validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()


# ============================================================================
# Request/Response Models
# ============================================================================

class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "user"


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None


# ============================================================================
# User CRUD Operations
# ============================================================================

@router.get("")
@limiter.limit("60/minute")
async def list_users(
    request: Request,
    current_user: dict = Depends(require_admin)
):
    """List all users (admin only)"""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .select('id, email, name, role, created_at')\
                .order('created_at', desc=True)\
                .execute()
        )

        return {
            'success': True,
            'users': result.data
        }

    except Exception as e:
        logger.error(f"❌ Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("")
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    user_data: UserCreateRequest,
    current_user: dict = Depends(require_admin)
):
    """Create a new user (admin only)"""
    try:
        # Generate secure temporary password
        temp_password = generate_secure_password(16)

        # Auto-assign default client
        client_id = get_default_client_id()

        # Create user in Supabase Auth
        auth_result = await asyncio.to_thread(
            lambda: supabase.auth.admin.create_user({
                "email": user_data.email,
                "password": temp_password,
                "email_confirm": True
            })
        )

        user_id = auth_result.user.id

        # Create/update user profile in database
        # Use upsert because the on_auth_user_created trigger may have already created the row
        profile_data = {
            'id': user_id,
            'email': user_data.email,
            'name': user_data.name,
            'role': user_data.role,
            'client_id': client_id
        }

        await asyncio.to_thread(
            lambda: supabase.table('users').upsert(profile_data).execute()
        )

        logger.info(f"✅ User created: {user_data.email}")

        return {
            'success': True,
            'user_id': user_id,
            'email': user_data.email,
            'temporary_password': temp_password,
            'message': 'User created successfully. Send password via secure channel.'
        }

    except Exception as e:
        logger.error(f"❌ Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")


@router.put("/{user_id}")
@limiter.limit("30/minute")
async def update_user(
    request: Request,
    user_id: str,
    user_update: UserUpdateRequest,
    current_user: dict = Depends(require_admin)
):
    """Update user profile (admin only)"""
    try:
        validate_uuid(user_id, "user_id")

        update_data = {}
        if user_update.name is not None:
            update_data['name'] = user_update.name
        if user_update.role is not None:
            update_data['role'] = user_update.role

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .update(update_data)\
                .eq('id', user_id)\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            'success': True,
            'user': result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/{user_id}/avatar")
@limiter.limit("10/minute")
async def upload_avatar(
    request: Request,
    user_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a profile avatar image"""
    try:
        validate_uuid(user_id, "user_id")

        # Users can only update their own avatar (unless admin)
        if current_user['role'] != 'admin' and current_user['id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )

        # Validate file size (max 5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max 5MB allowed.")

        # Validate file signature (magic numbers) to ensure it's actually an image
        validate_image_magic(contents, file.content_type)

        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        storage_path = f"{user_id}/avatar.{file_ext}"

        # Upload to Supabase Storage (upsert to replace existing)
        upload_result = await asyncio.to_thread(
            lambda: supabase.storage.from_('avatars').upload(
                path=storage_path,
                file=contents,
                file_options={'content-type': file.content_type, 'upsert': 'true'}
            )
        )

        # Get public URL
        public_url = supabase.storage.from_('avatars').get_public_url(storage_path)

        # Update user record with avatar URL
        await asyncio.to_thread(
            lambda: supabase.table('users')\
                .update({'avatar_url': public_url})\
                .eq('id', user_id)\
                .execute()
        )

        logger.info(f"✅ Avatar uploaded for user {user_id}")

        return {
            'success': True,
            'avatar_url': public_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.delete("/{user_id}/avatar")
@limiter.limit("30/minute")
async def delete_avatar(
    request: Request,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete user's avatar"""
    try:
        validate_uuid(user_id, "user_id")

        # Users can only delete their own avatar (unless admin)
        if current_user['role'] != 'admin' and current_user['id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get current avatar URL to determine file path
        user_result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .select('avatar_url')\
                .eq('id', user_id)\
                .single()\
                .execute()
        )

        if user_result.data and user_result.data.get('avatar_url'):
            # Try to delete from storage
            try:
                # Extract path from URL - try common extensions
                for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    storage_path = f"{user_id}/avatar.{ext}"
                    await asyncio.to_thread(
                        lambda p=storage_path: supabase.storage.from_('avatars').remove([p])
                    )
            except Exception as e:
                logger.debug(f"Could not remove avatar from storage: {e}")

        # Clear avatar_url in database
        await asyncio.to_thread(
            lambda: supabase.table('users')\
                .update({'avatar_url': None})\
                .eq('id', user_id)\
                .execute()
        )

        logger.info(f"✅ Avatar deleted for user {user_id}")

        return {
            'success': True,
            'message': 'Avatar deleted successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting avatar: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/{user_id}/resend-invitation")
@limiter.limit("5/minute")
async def resend_invitation(
    request: Request,
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Resend password reset email to user"""
    try:
        validate_uuid(user_id, "user_id")

        # Get user email
        user_result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .select('email')\
                .eq('id', user_id)\
                .single()\
                .execute()
        )

        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")

        email = user_result.data['email']

        # Send password reset email via Supabase
        await asyncio.to_thread(
            lambda: supabase.auth.reset_password_for_email(email)
        )

        logger.info(f"✅ Password reset email sent to: {email}")

        return {
            'success': True,
            'message': f'Password reset email sent to {email}'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resending invitation: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Current User Documents & Storage
# ============================================================================

@router.get("/me/documents")
async def list_user_documents(
    current_user: dict = Depends(get_current_user)
):
    """List all documents uploaded by current user.

    Returns documents with their tags and obsidian file path (if applicable).
    Handles pagination to fetch all documents (Supabase default limit is 1000).
    """
    try:
        # Fetch all documents with pagination (Supabase limits to 1000 per request)
        all_documents = []
        page_size = 1000
        offset = 0

        while True:
            result = await asyncio.to_thread(
                lambda o=offset: supabase.table('documents')
                    .select('*')
                    .eq('uploaded_by', current_user['id'])
                    .order('uploaded_at', desc=True)
                    .range(o, o + page_size - 1)
                    .execute()
            )

            batch = result.data or []
            all_documents.extend(batch)

            # If we got fewer than page_size, we've fetched all documents
            if len(batch) < page_size:
                break

            offset += page_size

        documents = all_documents
        doc_ids = [doc['id'] for doc in documents]

        # Get tags for all documents (also paginated)
        # Gracefully handle case where document_tags table doesn't exist yet
        tags_by_doc = {}
        if doc_ids:
            try:
                # Fetch tags in batches of 500 doc_ids to avoid query limits
                batch_size = 500
                all_tags = []

                for i in range(0, len(doc_ids), batch_size):
                    batch_ids = doc_ids[i:i + batch_size]
                    tags_result = await asyncio.to_thread(
                        lambda ids=batch_ids: supabase.table('document_tags')
                            .select('document_id, tag, source')
                            .in_('document_id', ids)
                            .execute()
                    )
                    all_tags.extend(tags_result.data or [])

                # Group tags by document_id
                for tag_record in all_tags:
                    doc_id = tag_record['document_id']
                    if doc_id not in tags_by_doc:
                        tags_by_doc[doc_id] = []
                    tags_by_doc[doc_id].append({
                        'tag': tag_record['tag'],
                        'source': tag_record['source']
                    })
            except Exception as tag_error:
                # Table might not exist yet - just log and continue without tags
                logger.debug(f"Could not fetch document tags: {tag_error}")

        # Attach tags to each document
        for doc in documents:
            doc['tags'] = tags_by_doc.get(doc['id'], [])

        return {
            'success': True,
            'documents': documents,
            'count': len(documents)
        }

    except Exception as e:
        import traceback
        logger.error(f"❌ Error listing documents: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/me/storage")
async def get_storage_info(
    current_user: dict = Depends(get_current_user)
):
    """Get storage usage information for current user.

    Calculates storage used directly from documents table for accuracy.
    """
    try:
        user_id = current_user['id']

        # Get user's storage quota (handle case where user doesn't exist in users table yet)
        storage_quota = 524288000  # 500MB default
        try:
            user_result = await asyncio.to_thread(
                lambda: supabase.table('users')\
                    .select('storage_quota')\
                    .eq('id', user_id)\
                    .maybe_single()\
                    .execute()
            )
            if user_result.data:
                storage_quota = user_result.data.get('storage_quota') or storage_quota
        except Exception as user_err:
            logger.debug(f"Could not fetch user storage quota: {user_err}")

        # Calculate actual storage used from documents table
        docs_result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('file_size')\
                .eq('uploaded_by', user_id)\
                .execute()
        )

        storage_used = sum(doc.get('file_size', 0) or 0 for doc in (docs_result.data or []))

        return {
            'success': True,
            'storage_quota': storage_quota,
            'storage_used': storage_used,
            'storage_available': max(0, storage_quota - storage_used),
            'usage_percentage': round((storage_used / storage_quota * 100), 2) if storage_quota > 0 else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching storage info: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/me/documents/list")
async def list_user_documents_paginated(
    limit: int = 50,
    offset: int = 0,
    include_tags: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """List documents with pagination and minimal columns for fast loading.

    Optimized endpoint that:
    - Returns only essential columns (not SELECT *)
    - Supports pagination with offset/limit
    - Optionally includes tags (disabled by default for speed)
    - Returns estimated total count from cache

    Args:
        limit: Number of documents to return (default 50, max 100)
        offset: Number of documents to skip
        include_tags: Whether to include document tags (slower)

    Returns:
        documents: List of document objects with minimal fields
        total_estimate: Estimated total document count (from cache)
        has_more: Boolean indicating if more documents exist
        offset: Current offset
        limit: Current limit
    """
    try:
        user_id = current_user['id']

        # Clamp limit to reasonable bounds
        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        # Select only essential columns for fast loading
        essential_columns = (
            'id, filename, title, uploaded_at, processed, processing_status, '
            'source_platform, file_size, obsidian_file_path, external_url, '
            'google_drive_file_id, notion_page_id, sync_cadence, storage_url'
        )

        # Fetch documents with pagination
        result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select(essential_columns)
                .eq('uploaded_by', user_id)
                .order('uploaded_at', desc=True)
                .range(offset, offset + limit)
                .execute()
        )

        documents = result.data or []

        # Get estimated total from cache (fast) or fall back to actual count
        total_estimate = 0
        try:
            counts_result = await asyncio.to_thread(
                lambda: supabase.table('user_document_counts')
                    .select('total_count')
                    .eq('user_id', user_id)
                    .maybe_single()
                    .execute()
            )
            if counts_result.data:
                total_estimate = counts_result.data.get('total_count', 0)
            else:
                # Cache miss - count documents directly (slower, but initializes cache)
                count_result = await asyncio.to_thread(
                    lambda: supabase.table('documents')
                        .select('id', count='exact')
                        .eq('uploaded_by', user_id)
                        .execute()
                )
                total_estimate = count_result.count or len(documents)
        except Exception as count_err:
            # Fallback if counts table doesn't exist yet
            logger.debug(f"Could not fetch document counts: {count_err}")
            total_estimate = len(documents) + (1 if len(documents) == limit else 0)

        # Optionally include tags
        if include_tags and documents:
            doc_ids = [doc['id'] for doc in documents]
            try:
                tags_result = await asyncio.to_thread(
                    lambda: supabase.table('document_tags')
                        .select('document_id, tag, source')
                        .in_('document_id', doc_ids)
                        .execute()
                )

                # Group tags by document_id
                tags_by_doc = {}
                for tag_record in tags_result.data or []:
                    doc_id = tag_record['document_id']
                    if doc_id not in tags_by_doc:
                        tags_by_doc[doc_id] = []
                    tags_by_doc[doc_id].append({
                        'tag': tag_record['tag'],
                        'source': tag_record['source']
                    })

                # Attach tags to documents
                for doc in documents:
                    doc['tags'] = tags_by_doc.get(doc['id'], [])
            except Exception as tag_err:
                logger.debug(f"Could not fetch document tags: {tag_err}")
                for doc in documents:
                    doc['tags'] = []
        else:
            # No tags requested - set empty arrays
            for doc in documents:
                doc['tags'] = []

        has_more = len(documents) == limit and (offset + limit) < total_estimate

        return {
            'success': True,
            'documents': documents,
            'total_estimate': total_estimate,
            'has_more': has_more,
            'offset': offset,
            'limit': limit
        }

    except Exception as e:
        import traceback
        logger.error(f"❌ Error listing documents paginated: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/me/documents/counts")
async def get_user_document_counts(
    current_user: dict = Depends(get_current_user)
):
    """Get cached document counts by source platform.

    Returns counts from the user_document_counts cache table for fast retrieval.
    Falls back to calculating counts if cache is not available.
    """
    try:
        user_id = current_user['id']

        # Try to get from cache first
        try:
            counts_result = await asyncio.to_thread(
                lambda: supabase.table('user_document_counts')
                    .select('*')
                    .eq('user_id', user_id)
                    .maybe_single()
                    .execute()
            )

            if counts_result.data:
                return {
                    'success': True,
                    'total': counts_result.data.get('total_count', 0),
                    'google_drive': counts_result.data.get('google_drive_count', 0),
                    'notion': counts_result.data.get('notion_count', 0),
                    'obsidian': counts_result.data.get('obsidian_count', 0),
                    'upload': counts_result.data.get('upload_count', 0),
                    'cached': True,
                    'updated_at': counts_result.data.get('updated_at')
                }
        except Exception as cache_err:
            logger.debug(f"Cache lookup failed, calculating counts: {cache_err}")

        # Fallback: calculate counts directly
        docs_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('source_platform')
                .eq('uploaded_by', user_id)
                .execute()
        )

        docs = docs_result.data or []
        counts = {
            'google_drive': 0,
            'notion': 0,
            'obsidian': 0,
            'upload': 0
        }

        for doc in docs:
            platform = doc.get('source_platform') or 'upload'
            if platform in counts:
                counts[platform] += 1
            elif platform == 'google_drive':
                counts['google_drive'] += 1

        return {
            'success': True,
            'total': len(docs),
            'google_drive': counts['google_drive'],
            'notion': counts['notion'],
            'obsidian': counts['obsidian'],
            'upload': counts['upload'],
            'cached': False
        }

    except Exception as e:
        logger.error(f"❌ Error fetching document counts: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")
