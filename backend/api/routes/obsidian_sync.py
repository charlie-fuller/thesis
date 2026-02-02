"""Obsidian Vault Sync API Routes.

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
    DEFAULT_SYNC_OPTIONS,
    ObsidianSyncError,
    create_vault_config,
    deactivate_vault_config,
    get_sync_status,
    get_vault_config,
    scan_vault,
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
    """Request body for configuring a vault."""

    vault_path: str = Field(..., description="Absolute path to Obsidian vault directory")
    sync_options: Optional[dict] = Field(
        None,
        description="Optional sync options (include_patterns, exclude_patterns, auto_classify, etc.)",
    )


class UpdateSyncOptionsRequest(BaseModel):
    """Request body for updating sync options."""

    sync_options: dict = Field(..., description="Sync options to update")


class DisconnectRequest(BaseModel):
    """Request body for disconnecting vault."""

    remove_documents: bool = Field(
        False, description="Whether to delete synced documents from the knowledge base"
    )


# ============================================================================
# Configuration Endpoints
# ============================================================================


@router.post("/configure")
async def configure_obsidian_vault(
    request: ConfigureVaultRequest, current_user: dict = Depends(get_current_user)
):
    """Configure an Obsidian vault for syncing.

    Creates or updates the vault configuration for the current user.
    Validates that the vault path exists and is a directory.
    """
    try:
        # Get user's client_id
        user_result = await asyncio.to_thread(
            lambda: _get_db()
            .table("users")
            .select("client_id")
            .eq("id", current_user["id"])
            .single()
            .execute()
        )

        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")

        client_id = user_result.data.get("client_id")
        if not client_id:
            raise HTTPException(status_code=400, detail="User has no client association")

        # Create vault configuration
        config = await asyncio.to_thread(
            create_vault_config,
            user_id=current_user["id"],
            client_id=client_id,
            vault_path=request.vault_path,
            sync_options=request.sync_options,
        )

        return {
            "success": True,
            "config_id": config["id"],
            "vault_name": config["vault_name"],
            "vault_path": config["vault_path"],
            "sync_options": config["sync_options"],
            "message": f"Vault '{config['vault_name']}' configured successfully",
        }

    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configure vault error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/status")
async def get_obsidian_status(current_user: dict = Depends(get_current_user)):
    """Get Obsidian sync status for the current user.

    Returns connection status, vault info, sync stats, and pending changes.
    """
    try:
        status = await asyncio.to_thread(get_sync_status, current_user["id"])
        return {"success": True, **status}

    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/settings")
async def update_obsidian_settings(
    request: UpdateSyncOptionsRequest, current_user: dict = Depends(get_current_user)
):
    """Update sync options for the configured vault."""
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first.",
            )

        # Merge new options with existing
        existing_options = config.get("sync_options", {})
        merged_options = {**existing_options, **request.sync_options}

        updated = await asyncio.to_thread(
            update_vault_config, config["id"], {"sync_options": merged_options}
        )

        return {"success": True, "sync_options": updated.get("sync_options", merged_options)}

    except HTTPException:
        raise
    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Update settings error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Sync Endpoints
# ============================================================================


@router.post("/sync")
async def trigger_obsidian_sync(
    background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)
):
    """Trigger a full sync of the configured Obsidian vault.

    Runs in the background and returns immediately.
    Check /api/obsidian/status for sync progress.
    """
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first.",
            )

        if not config.get("is_active"):
            raise HTTPException(
                status_code=400, detail="Vault sync is not active. Please reconfigure the vault."
            )

        # Run sync in background
        background_tasks.add_task(sync_vault, config, "manual")

        return {
            "success": True,
            "message": f"Sync started for vault '{config['vault_name']}' in background",
            "vault_path": config["vault_path"],
        }

    except HTTPException:
        raise
    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/sync/recent")
async def trigger_recent_sync(
    background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)
):
    """Sync only new/pending/failed files (skip already synced files).

    This is faster than a full sync when you just want to pick up new files
    without re-processing files that haven't changed.
    """
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first.",
            )

        if not config.get("is_active"):
            raise HTTPException(
                status_code=400, detail="Vault sync is not active. Please reconfigure the vault."
            )

        # Run sync in background with recent_only=True
        background_tasks.add_task(
            sync_vault,
            config,
            "manual",
            True,  # recent_only
        )

        return {
            "success": True,
            "message": f"Recent sync started for vault '{config['vault_name']}' in background",
            "vault_path": config["vault_path"],
        }

    except HTTPException:
        raise
    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Recent sync error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/sync/full")
async def trigger_full_sync(
    background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)
):
    """Trigger a full resync of all files in the vault.

    This resyncs all files regardless of their current sync state.
    Useful for recovering from sync issues.
    """
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            raise HTTPException(status_code=404, detail="No Obsidian vault configured")

        # Clear sync states to force full resync
        await asyncio.to_thread(
            lambda: _get_db()
            .table("obsidian_sync_state")
            .delete()
            .eq("config_id", config["id"])
            .execute()
        )

        # Run sync in background
        background_tasks.add_task(sync_vault, config, "manual")

        return {
            "success": True,
            "message": f"Full resync started for vault '{config['vault_name']}'",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full sync error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Disconnect Endpoint
# ============================================================================


@router.delete("/disconnect")
async def disconnect_obsidian(
    remove_documents: bool = False, current_user: dict = Depends(get_current_user)
):
    """Disconnect Obsidian vault integration.

    Optionally removes all synced documents from the knowledge base.
    """
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            raise HTTPException(status_code=404, detail="No Obsidian vault configured")

        result = await asyncio.to_thread(deactivate_vault_config, config["id"], remove_documents)

        message = "Obsidian vault disconnected"
        if remove_documents:
            message += f" and {result.get('documents_removed', 0)} documents removed"

        return {"success": True, "message": message, **result}

    except HTTPException:
        raise
    except ObsidianSyncError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Sync History Endpoint
# ============================================================================


@router.get("/sync-history")
async def get_sync_history(current_user: dict = Depends(get_current_user), limit: int = 10):
    """Get recent sync history for the configured vault."""
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            return {"success": True, "history": [], "message": "No vault configured"}

        result = await asyncio.to_thread(
            lambda: _get_db()
            .table("obsidian_sync_log")
            .select("*")
            .eq("config_id", config["id"])
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )

        return {"success": True, "history": result.data}

    except Exception as e:
        logger.error(f"Sync history error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# File State Endpoints
# ============================================================================


@router.get("/files")
async def get_synced_files(
    current_user: dict = Depends(get_current_user), status: Optional[str] = None, limit: int = 100
):
    """Get list of synced files and their sync status.

    Args:
        status: Filter by sync status (synced, pending, failed, deleted)
        limit: Maximum number of results
    """
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            return {"success": True, "files": [], "message": "No vault configured"}

        query = _get_db().table("obsidian_sync_state").select("*").eq("config_id", config["id"])

        if status:
            query = query.eq("sync_status", status)

        result = await asyncio.to_thread(lambda: query.order("file_path").limit(limit).execute())

        return {"success": True, "files": result.data, "count": len(result.data)}

    except Exception as e:
        logger.error(f"Get files error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/files/recent")
async def get_recent_synced_files(current_user: dict = Depends(get_current_user), limit: int = 10):
    """Get most recent documents from the vault, ordered by original_date DESC.

    Returns synced documents ordered by their actual document date (e.g., meeting date),
    falling back to last_synced_at for documents without an original_date.
    """
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            return {"success": True, "files": [], "count": 0, "message": "No vault configured"}

        # Strategy: Query documents first (ordered by updated_at DESC) to get recent activity,
        # then join with sync_state to get file paths for Obsidian vault files.
        # This ensures we see recently updated documents regardless of when they were synced.

        # First, get document IDs linked to this vault's sync state
        # Order by last_synced_at DESC to prioritize recently synced files
        sync_result = await asyncio.to_thread(
            lambda: _get_db()
            .table("obsidian_sync_state")
            .select("file_path, document_id, last_synced_at")
            .eq("config_id", config["id"])
            .eq("sync_status", "synced")
            .not_.is_("document_id", "null")
            .order("last_synced_at", desc=True)
            .limit(500)  # Limit to avoid query size issues
            .execute()
        )

        if not sync_result.data:
            return {"success": True, "files": [], "count": 0}

        # Build lookup from document_id to sync info
        sync_info = {
            s["document_id"]: {"file_path": s["file_path"], "last_synced_at": s["last_synced_at"]}
            for s in sync_result.data
            if s.get("document_id")
        }

        doc_ids = list(sync_info.keys())
        if not doc_ids:
            return {"success": True, "files": [], "count": 0}

        # Get documents ordered by updated_at DESC to find most recently active
        docs_result = await asyncio.to_thread(
            lambda: _get_db()
            .table("documents")
            .select("id, original_date, updated_at")
            .in_("id", doc_ids)
            .order("updated_at", desc=True)
            .limit(100)  # Get top 100 most recently updated vault docs
            .execute()
        )
        {
            d["id"]: {"original_date": d.get("original_date"), "updated_at": d.get("updated_at")}
            for d in docs_result.data
        }

        # Get today's date for validation
        from datetime import date

        today = date.today().isoformat()

        # Merge documents with sync info and sort by best available date DESC
        files_with_dates = []
        for doc in docs_result.data:
            doc_id = doc["id"]
            sync = sync_info.get(doc_id, {})
            orig_date = doc.get("original_date")
            updated_at = doc.get("updated_at")

            # Validate original_date - ignore future dates (data quality issue)
            valid_orig_date = orig_date if orig_date and orig_date <= today else None

            # Use valid original_date if available, otherwise updated_at, then last_synced_at
            sort_date = (
                valid_orig_date
                or (updated_at[:10] if updated_at else None)
                or (sync.get("last_synced_at", "")[:10] if sync.get("last_synced_at") else "")
            )
            files_with_dates.append(
                {
                    "file_path": sync.get("file_path", ""),
                    "document_id": doc_id,
                    "last_synced_at": sync.get("last_synced_at"),
                    "original_date": orig_date,
                    "updated_at": updated_at,
                    "_sort_date": sort_date,
                }
            )

        # Sort by the best available date, newest first
        files_with_dates.sort(key=lambda x: x["_sort_date"] or "", reverse=True)

        # Remove internal sort field before returning
        result_files = []
        for f in files_with_dates[:limit]:
            result_files.append(
                {
                    "file_path": f["file_path"],
                    "document_id": f["document_id"],
                    "last_synced_at": f["last_synced_at"],
                    "original_date": f["original_date"],
                    "updated_at": f["updated_at"],
                }
            )

        return {"success": True, "files": result_files, "count": len(result_files)}

    except Exception as e:
        logger.error(f"Get recent files error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/files/pending")
async def get_pending_files(current_user: dict = Depends(get_current_user)):
    """Get files that are pending sync or have failed."""
    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            return {"success": True, "pending": [], "failed": []}

        result = await asyncio.to_thread(
            lambda: _get_db()
            .table("obsidian_sync_state")
            .select("*")
            .eq("config_id", config["id"])
            .in_("sync_status", ["pending", "failed"])
            .order("updated_at", desc=True)
            .execute()
        )

        pending = [f for f in result.data if f["sync_status"] == "pending"]
        failed = [f for f in result.data if f["sync_status"] == "failed"]

        return {
            "success": True,
            "pending": pending,
            "failed": failed,
            "pending_count": len(pending),
            "failed_count": len(failed),
        }

    except Exception as e:
        logger.error(f"Get pending files error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/files/{file_path:path}/retry")
async def retry_failed_file(
    file_path: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Retry syncing a failed file."""
    try:
        from pathlib import Path

        from services.obsidian_sync import get_sync_state, sync_file

        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            raise HTTPException(status_code=404, detail="No vault configured")

        # Get sync state for this file
        state = await asyncio.to_thread(get_sync_state, config["id"], file_path)

        if not state:
            raise HTTPException(
                status_code=404, detail=f"File not found in sync state: {file_path}"
            )

        # Build absolute path
        vault_path = Path(config["vault_path"])
        absolute_path = vault_path / file_path

        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")

        # Sync the file in background
        background_tasks.add_task(sync_file, config, absolute_path, state)

        return {"success": True, "message": f"Retry started for: {file_path}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry file error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Debug Endpoint
# ============================================================================


@router.get("/debug")
async def debug_vault_scan(current_user: dict = Depends(get_current_user), limit: int = 100):
    """Debug endpoint to show what files would be scanned from the vault.

    Returns the list of files found, grouped by directory depth,
    along with the patterns being used.
    """
    import os
    from pathlib import Path

    try:
        config = await asyncio.to_thread(get_vault_config, current_user["id"])

        if not config:
            return {"success": False, "error": "No vault configured"}

        vault_path = Path(config["vault_path"])
        sync_options = config.get("sync_options", DEFAULT_SYNC_OPTIONS)

        include_patterns = sync_options.get("include_patterns", ["**/*.md"])
        exclude_patterns = sync_options.get("exclude_patterns", [".obsidian/**"])
        max_file_size_mb = sync_options.get("max_file_size_mb", 10)

        # Scan vault
        files = await asyncio.to_thread(
            scan_vault, vault_path, include_patterns, exclude_patterns, max_file_size_mb
        )

        # Get relative paths and group by directory depth
        files_info = []
        directories_seen = set()

        for file_path in files[:limit]:
            relative = file_path.relative_to(vault_path)
            relative_str = str(relative)
            depth = len(relative.parts) - 1  # -1 because the file itself doesn't count

            # Track all parent directories
            parent = relative.parent
            while str(parent) != ".":
                directories_seen.add(str(parent))
                parent = parent.parent

            files_info.append(
                {
                    "path": relative_str,
                    "depth": depth,
                    "size_kb": round(file_path.stat().st_size / 1024, 2),
                }
            )

        # Also walk the vault to show ALL directories (even those with no matching files)
        all_directories = set()
        for root, dirs, _ in os.walk(vault_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            rel_root = Path(root).relative_to(vault_path)
            if str(rel_root) != ".":
                all_directories.add(str(rel_root))

        # Find directories that have no files synced
        dirs_without_files = sorted(all_directories - directories_seen)

        return {
            "success": True,
            "vault_path": str(vault_path),
            "vault_exists": vault_path.exists(),
            "patterns": {
                "include": include_patterns,
                "exclude": exclude_patterns,
                "max_file_size_mb": max_file_size_mb,
            },
            "total_files_found": len(files),
            "files_shown": len(files_info),
            "files": files_info,
            "directories_with_synced_files": sorted(directories_seen),
            "directories_without_synced_files": dirs_without_files[:50],
            "hint": "Check directories_without_synced_files to see folders that may be excluded",
        }

    except Exception as e:
        logger.error(f"Debug vault scan error: {str(e)}")
        import traceback

        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
