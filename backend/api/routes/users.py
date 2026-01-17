"""
User management routes
Handles user CRUD, prompts, and profile operations
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr

from auth import get_current_user, require_admin
from config import get_default_client_id
from database import get_supabase
from logger_config import get_logger
from validation import generate_secure_password, validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])
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
async def list_users(
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_user(
    request: UserCreateRequest,
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
                "email": request.email,
                "password": temp_password,
                "email_confirm": True
            })
        )

        user_id = auth_result.user.id

        # Create/update user profile in database
        # Use upsert because the on_auth_user_created trigger may have already created the row
        profile_data = {
            'id': user_id,
            'email': request.email,
            'name': request.name,
            'role': request.role,
            'client_id': client_id
        }

        await asyncio.to_thread(
            lambda: supabase.table('users').upsert(profile_data).execute()
        )

        logger.info(f"✅ User created: {request.email}")

        return {
            'success': True,
            'user_id': user_id,
            'email': request.email,
            'temporary_password': temp_password,
            'message': 'User created successfully. Send password via secure channel.'
        }

    except Exception as e:
        logger.error(f"❌ Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: dict = Depends(require_admin)
):
    """Update user profile (admin only)"""
    try:
        validate_uuid(user_id, "user_id")

        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.role is not None:
            update_data['role'] = request.role

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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/avatar")
async def upload_avatar(
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
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/avatar")
async def delete_avatar(
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/resend-invitation")
async def resend_invitation(
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
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Current User Documents & Storage
# ============================================================================

@router.get("/me/documents")
async def list_user_documents(
    current_user: dict = Depends(get_current_user)
):
    """List all documents uploaded by current user.

    Returns documents with their tags and obsidian file path (if applicable).
    """
    try:
        # Get all documents for the user
        result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('*')\
                .eq('uploaded_by', current_user['id'])\
                .order('uploaded_at', desc=True)\
                .execute()
        )

        documents = result.data or []
        doc_ids = [doc['id'] for doc in documents]

        # Get tags for all documents in a single query
        tags_by_doc = {}
        if doc_ids:
            tags_result = await asyncio.to_thread(
                lambda: supabase.table('document_tags')\
                    .select('document_id, tag, source')\
                    .in_('document_id', doc_ids)\
                    .order('created_at')\
                    .execute()
            )

            # Group tags by document_id
            for tag_record in tags_result.data or []:
                doc_id = tag_record['document_id']
                if doc_id not in tags_by_doc:
                    tags_by_doc[doc_id] = []
                tags_by_doc[doc_id].append({
                    'tag': tag_record['tag'],
                    'source': tag_record['source']
                })

        # Attach tags to each document
        for doc in documents:
            doc['tags'] = tags_by_doc.get(doc['id'], [])

        return {
            'success': True,
            'documents': documents
        }

    except Exception as e:
        logger.error(f"❌ Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/storage")
async def get_storage_info(
    current_user: dict = Depends(get_current_user)
):
    """Get storage usage information for current user.

    Calculates storage used directly from documents table for accuracy.
    """
    try:
        user_id = current_user['id']

        # Get user's storage quota
        user_result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .select('storage_quota')\
                .eq('id', user_id)\
                .single()\
                .execute()
        )

        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")

        storage_quota = user_result.data.get('storage_quota') or 524288000  # 500MB default

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
        raise HTTPException(status_code=500, detail=str(e))
