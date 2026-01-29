"""
Obsidian Vault Sync API Routes

Handles configuration, sync triggers, and status for Obsidian vault integration.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger
from services.obsidian_sync import (
    ObsidianSyncError,
    create_vault_config,
    deactivate_vault_config,
    get_sync_status,
    get_vault_config,
    sync_vault,
    update_vault_config,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/obsidian", tags=["obsidian"])

# Lazy Supabase initialization to avoid import-time database connections
_supabase = None


def _get_db():
    """Get Supabase client with lazy initialization."""
    global _supabase
    if _supabase is None:
        _supabase = get_supabase()
    return _supabase


# ============================================================================
# Request/Response Models
# ============================================================================

class ConfigureVaultRequest(BaseModel):
    """Request body for configuring a vault"""
    vault_path: str = Field(..., description="Absolute path to Obsidian vault directory")
    sync_options: Optional[dict] = Field(
        None,
        description="Optional sync options (include_patterns, exclude_patterns, auto_classify, etc.)"
    )


class UpdateSyncOptionsRequest(BaseModel):
    """Request body for updating sync options"""
    sync_options: dict = Field(..., description="Sync options to update")


class DisconnectRequest(BaseModel):
    """Request body for disconnecting vault"""
    remove_documents: bool = Field(
        False,
        description="Whether to delete synced documents from the knowledge base"
    )


# ============================================================================
# Configuration Endpoints
# ============================================================================

@router.post("/configure")
async def configure_obsidian_vault(
    request: ConfigureVaultRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Configure an Obsidian vault for syncing.

    Creates or updates the vault configuration for the current user.
    Validates that the vault path exists and is a directory.
    """
    try:
        # Get user's client_id
        user_result = await asyncio.to_thread(
            lambda: _get_db().table('users')
                .select('client_id')
                .eq('id', current_user['id'])
                .single()
                .execute()
        )

        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")

        client_id = user_result.data.get('client_id')
        if not client_id:
            raise HTTPException(status_code=400, detail="User has no client association")

        # Create vault configuration
        config = await asyncio.to_thread(
            create_vault_config,
            user_id=current_user['id'],
            client_id=client_id,
            vault_path=request.vault_path,
            sync_options=request.sync_options
        )

        return {
            'success': True,
            'config_id': config['id'],
            'vault_name': config['vault_name'],
            'vault_path': config['vault_path'],
            'sync_options': config['sync_options'],
            'message': f"Vault '{config['vault_name']}' configured successfully"
        }

    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configure vault error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/status")
async def get_obsidian_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get Obsidian sync status for the current user.

    Returns connection status, vault info, sync stats, and pending changes.
    """
    try:
        status = await asyncio.to_thread(
            get_sync_status,
            current_user['id']
        )
        return {'success': True, **status}

    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.patch("/settings")
async def update_obsidian_settings(
    request: UpdateSyncOptionsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update sync options for the configured vault.
    """
    try:
        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first."
            )

        # Merge new options with existing
        existing_options = config.get('sync_options', {})
        merged_options = {**existing_options, **request.sync_options}

        updated = await asyncio.to_thread(
            update_vault_config,
            config['id'],
            {'sync_options': merged_options}
        )

        return {
            'success': True,
            'sync_options': updated.get('sync_options', merged_options)
        }

    except HTTPException:
        raise
    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update settings error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Sync Endpoints
# ============================================================================

@router.post("/sync")
async def trigger_obsidian_sync(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger a full sync of the configured Obsidian vault.

    Runs in the background and returns immediately.
    Check /api/obsidian/status for sync progress.
    """
    try:
        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first."
            )

        if not config.get('is_active'):
            raise HTTPException(
                status_code=400,
                detail="Vault sync is not active. Please reconfigure the vault."
            )

        # Run sync in background
        background_tasks.add_task(
            sync_vault,
            config,
            'manual'
        )

        return {
            'success': True,
            'message': f"Sync started for vault '{config['vault_name']}' in background",
            'vault_path': config['vault_path']
        }

    except HTTPException:
        raise
    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/sync/full")
async def trigger_full_sync(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger a full resync of all files in the vault.

    This resyncs all files regardless of their current sync state.
    Useful for recovering from sync issues.
    """
    try:
        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured"
            )

        # Clear sync states to force full resync
        await asyncio.to_thread(
            lambda: _get_db().table('obsidian_sync_state')
                .delete()
                .eq('config_id', config['id'])
                .execute()
        )

        # Run sync in background
        background_tasks.add_task(
            sync_vault,
            config,
            'manual'
        )

        return {
            'success': True,
            'message': f"Full resync started for vault '{config['vault_name']}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full sync error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Disconnect Endpoint
# ============================================================================

@router.delete("/disconnect")
async def disconnect_obsidian(
    remove_documents: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Disconnect Obsidian vault integration.

    Optionally removes all synced documents from the knowledge base.
    """
    try:
        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured"
            )

        result = await asyncio.to_thread(
            deactivate_vault_config,
            config['id'],
            remove_documents
        )

        message = "Obsidian vault disconnected"
        if remove_documents:
            message += f" and {result.get('documents_removed', 0)} documents removed"

        return {
            'success': True,
            'message': message,
            **result
        }

    except HTTPException:
        raise
    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# Sync History Endpoint
# ============================================================================

@router.get("/sync-history")
async def get_sync_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """
    Get recent sync history for the configured vault.
    """
    try:
        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            return {
                'success': True,
                'history': [],
                'message': 'No vault configured'
            }

        result = await asyncio.to_thread(
            lambda: _get_db().table('obsidian_sync_log')
                .select('*')
                .eq('config_id', config['id'])
                .order('started_at', desc=True)
                .limit(limit)
                .execute()
        )

        return {
            'success': True,
            'history': result.data
        }

    except Exception as e:
        logger.error(f"Sync history error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# ============================================================================
# File State Endpoints
# ============================================================================

@router.get("/files")
async def get_synced_files(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 100
):
    """
    Get list of synced files and their sync status.

    Args:
        status: Filter by sync status (synced, pending, failed, deleted)
        limit: Maximum number of results
    """
    try:
        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            return {
                'success': True,
                'files': [],
                'message': 'No vault configured'
            }

        query = _get_db().table('obsidian_sync_state') \
            .select('*') \
            .eq('config_id', config['id'])

        if status:
            query = query.eq('sync_status', status)

        result = await asyncio.to_thread(
            lambda: query
                .order('file_path')
                .limit(limit)
                .execute()
        )

        return {
            'success': True,
            'files': result.data,
            'count': len(result.data)
        }

    except Exception as e:
        logger.error(f"Get files error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/files/pending")
async def get_pending_files(
    current_user: dict = Depends(get_current_user)
):
    """
    Get files that are pending sync or have failed.
    """
    try:
        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            return {
                'success': True,
                'pending': [],
                'failed': []
            }

        result = await asyncio.to_thread(
            lambda: _get_db().table('obsidian_sync_state')
                .select('*')
                .eq('config_id', config['id'])
                .in_('sync_status', ['pending', 'failed'])
                .order('updated_at', desc=True)
                .execute()
        )

        pending = [f for f in result.data if f['sync_status'] == 'pending']
        failed = [f for f in result.data if f['sync_status'] == 'failed']

        return {
            'success': True,
            'pending': pending,
            'failed': failed,
            'pending_count': len(pending),
            'failed_count': len(failed)
        }

    except Exception as e:
        logger.error(f"Get pending files error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/files/{file_path:path}/retry")
async def retry_failed_file(
    file_path: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Retry syncing a failed file.
    """
    try:
        from pathlib import Path
        from services.obsidian_sync import get_sync_state, sync_file

        config = await asyncio.to_thread(
            get_vault_config,
            current_user['id']
        )

        if not config:
            raise HTTPException(status_code=404, detail="No vault configured")

        # Get sync state for this file
        state = await asyncio.to_thread(
            get_sync_state,
            config['id'],
            file_path
        )

        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"File not found in sync state: {file_path}"
            )

        # Build absolute path
        vault_path = Path(config['vault_path'])
        absolute_path = vault_path / file_path

        if not absolute_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found on disk: {file_path}"
            )

        # Sync the file in background
        background_tasks.add_task(
            sync_file,
            config,
            absolute_path,
            state
        )

        return {
            'success': True,
            'message': f"Retry started for: {file_path}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry file error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")
