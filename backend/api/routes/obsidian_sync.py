"""Obsidian Vault Sync API Routes.

Handles configuration, sync triggers, and status for Obsidian vault integration.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

import pb_client as pb
from logger_config import get_logger
from services.obsidian_sync import (
    ObsidianSyncError,
    create_vault_config,
    deactivate_vault_config,
    get_effective_sync_options,
    get_sync_status,
    get_vault_config,
    scan_vault,
    sync_vault,
    update_vault_config,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/obsidian", tags=["obsidian"])

# Track local sync agent activity (in-memory)
_agent_activity: dict = {}


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

    remove_documents: bool = Field(False, description="Whether to delete synced documents from the knowledge base")


# ============================================================================
# Configuration Endpoints
# ============================================================================


@router.post("/configure")
async def configure_obsidian_vault(request: ConfigureVaultRequest):
    """Configure an Obsidian vault for syncing."""
    try:
        # Create vault configuration (single-tenant: no user/client lookup)
        config = create_vault_config(
            user_id=None,
            client_id=None,
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
async def get_obsidian_status():
    """Get Obsidian sync status."""
    try:
        status = get_sync_status(None)

        # Include local sync agent activity
        agent_info = _agent_activity.get("owner")
        if agent_info:
            now_utc = datetime.now(timezone.utc)
            seconds_since = (now_utc - agent_info["last_upload"]).total_seconds()
            status["agent_active"] = seconds_since < 120
            status["agent_last_upload"] = agent_info["last_upload"].isoformat()
            status["agent_uploads_count"] = agent_info["uploads_since"]
            status["agent_sync_current"] = agent_info.get("sync_current")
            status["agent_sync_total"] = agent_info.get("sync_total")
        else:
            status["agent_active"] = False
            status["agent_last_upload"] = None
            status["agent_uploads_count"] = 0
            status["agent_sync_current"] = None
            status["agent_sync_total"] = None

        return {"success": True, **status}

    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.patch("/settings")
async def update_obsidian_settings(request: UpdateSyncOptionsRequest):
    """Update sync options for the configured vault."""
    try:
        config = get_vault_config(None)

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first.",
            )

        # Merge new options with existing
        existing_options = config.get("sync_options", {})
        merged_options = {**existing_options, **request.sync_options}

        updated = update_vault_config(config["id"], {"sync_options": merged_options})

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
async def trigger_obsidian_sync(background_tasks: BackgroundTasks):
    """Trigger a full sync of the configured Obsidian vault."""
    try:
        config = get_vault_config(None)

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first.",
            )

        if not config.get("is_active"):
            raise HTTPException(status_code=400, detail="Vault sync is not active. Please reconfigure the vault.")

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
async def trigger_recent_sync(background_tasks: BackgroundTasks):
    """Sync only new/pending/failed files."""
    try:
        config = get_vault_config(None)

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No Obsidian vault configured. Please configure a vault first.",
            )

        if not config.get("is_active"):
            raise HTTPException(status_code=400, detail="Vault sync is not active. Please reconfigure the vault.")

        background_tasks.add_task(sync_vault, config, "manual", True)

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
async def trigger_full_sync(background_tasks: BackgroundTasks):
    """Trigger a full resync of all files in the vault."""
    try:
        config = get_vault_config(None)

        if not config:
            raise HTTPException(status_code=404, detail="No Obsidian vault configured")

        background_tasks.add_task(sync_vault, config, "manual", False, True, True)

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
async def disconnect_obsidian(remove_documents: bool = False):
    """Disconnect Obsidian vault integration."""
    try:
        config = get_vault_config(None)

        if not config:
            raise HTTPException(status_code=404, detail="No Obsidian vault configured")

        result = deactivate_vault_config(config["id"], remove_documents)

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
async def get_sync_history(limit: int = 10):
    """Get recent sync history for the configured vault."""
    try:
        config = get_vault_config(None)

        if not config:
            return {"success": True, "history": [], "message": "No vault configured"}

        safe_config_id = pb.escape_filter(config["id"])
        result = pb.list_records(
            "obsidian_sync_log",
            filter=f"config_id='{safe_config_id}'",
            sort="-started_at",
            per_page=limit,
        )

        return {"success": True, "history": result.get("items", [])}

    except Exception as e:
        logger.error(f"Sync history error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# File State Endpoints
# ============================================================================


@router.get("/files")
async def get_synced_files(status: Optional[str] = None, limit: int = 100):
    """Get list of synced files and their sync status."""
    try:
        config = get_vault_config(None)

        if not config:
            return {"success": True, "files": [], "message": "No vault configured"}

        safe_config_id = pb.escape_filter(config["id"])
        filter_str = f"config_id='{safe_config_id}'"
        if status:
            safe_status = pb.escape_filter(status)
            filter_str += f" && sync_status='{safe_status}'"

        result = pb.list_records(
            "obsidian_sync_state",
            filter=filter_str,
            sort="file_path",
            per_page=limit,
        )

        items = result.get("items", [])
        return {"success": True, "files": items, "count": len(items)}

    except Exception as e:
        logger.error(f"Get files error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/files/recent")
async def get_recent_synced_files(limit: int = 10):
    """Get most recent documents from the vault, ordered by original_date DESC."""
    try:
        config = get_vault_config(None)

        if not config:
            return {"success": True, "files": [], "count": 0, "message": "No vault configured"}

        safe_config_id = pb.escape_filter(config["id"])

        sync_records = pb.get_all(
            "obsidian_sync_state",
            filter=f"config_id='{safe_config_id}' && sync_status='synced' && document_id!=''",
            sort="-last_synced_at",
            fields="file_path,document_id,last_synced_at",
        )

        if not sync_records:
            return {"success": True, "files": [], "count": 0}

        # Build lookup from document_id to sync info
        sync_info = {
            s["document_id"]: {"file_path": s["file_path"], "last_synced_at": s["last_synced_at"]}
            for s in sync_records
            if s.get("document_id")
        }

        doc_ids = list(sync_info.keys())
        if not doc_ids:
            return {"success": True, "files": [], "count": 0}

        # Fetch documents in batches
        all_docs = []
        for i in range(0, len(doc_ids), 30):
            batch = doc_ids[i : i + 30]
            parts = [f"id='{pb.escape_filter(did)}'" for did in batch]
            doc_filter = " || ".join(parts)
            docs = pb.get_all(
                "documents",
                filter=doc_filter,
                fields="id,original_date,updated",
                sort="-updated",
            )
            all_docs.extend(docs)

        # Get today's date for validation
        from datetime import date

        today = date.today().isoformat()

        # Merge documents with sync info and sort by best available date DESC
        files_with_dates = []
        for doc in all_docs:
            doc_id = doc["id"]
            sync = sync_info.get(doc_id, {})
            orig_date = doc.get("original_date")
            updated_at = doc.get("updated")

            # Validate original_date - ignore future dates
            valid_orig_date = orig_date if orig_date and orig_date <= today else None

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

        files_with_dates.sort(key=lambda x: x["_sort_date"] or "", reverse=True)

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
async def get_pending_files():
    """Get files that are pending sync or have failed."""
    try:
        config = get_vault_config(None)

        if not config:
            return {"success": True, "pending": [], "failed": []}

        safe_config_id = pb.escape_filter(config["id"])
        records = pb.get_all(
            "obsidian_sync_state",
            filter=f"config_id='{safe_config_id}' && (sync_status='pending' || sync_status='failed')",
            sort="-updated",
        )

        pending = [f for f in records if f["sync_status"] == "pending"]
        failed = [f for f in records if f["sync_status"] == "failed"]

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
async def retry_failed_file(file_path: str, background_tasks: BackgroundTasks):
    """Retry syncing a failed file."""
    try:
        from pathlib import Path

        from services.obsidian_sync import get_sync_state, sync_file

        config = get_vault_config(None)

        if not config:
            raise HTTPException(status_code=404, detail="No vault configured")

        state = get_sync_state(config["id"], file_path)

        if not state:
            raise HTTPException(status_code=404, detail=f"File not found in sync state: {file_path}")

        vault_path = Path(config["vault_path"])
        absolute_path = vault_path / file_path

        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")

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
async def debug_vault_scan(limit: int = 100):
    """Debug endpoint to show what files would be scanned from the vault."""
    import os
    from pathlib import Path

    try:
        config = get_vault_config(None)

        if not config:
            return {"success": False, "error": "No vault configured"}

        vault_path = Path(config["vault_path"])
        sync_options = get_effective_sync_options(config.get("sync_options"))

        include_patterns = sync_options["include_patterns"]
        exclude_patterns = sync_options["exclude_patterns"]
        max_file_size_mb = sync_options.get("max_file_size_mb", 10)

        files = scan_vault(vault_path, include_patterns, exclude_patterns, max_file_size_mb)

        files_info = []
        directories_seen = set()

        for file_path in files[:limit]:
            relative = file_path.relative_to(vault_path)
            relative_str = str(relative)
            depth = len(relative.parts) - 1

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

        all_directories = set()
        for root, dirs, _ in os.walk(vault_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            rel_root = Path(root).relative_to(vault_path)
            if str(rel_root) != ".":
                all_directories.add(str(rel_root))

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


# ============================================================================
# Remote File Upload Endpoint (for local-to-remote sync)
# ============================================================================


class RemoteFileUploadRequest(BaseModel):
    """Request body for uploading a file from remote client."""

    file_path: str = Field(..., description="Relative path within vault (e.g., 'Notes/meeting.md')")
    content: str = Field(..., description="File content (text)")
    content_type: str = Field(default="text/markdown", description="MIME type of content")
    file_mtime: Optional[float] = Field(default=None, description="File modification time as Unix timestamp")
    sync_current: Optional[int] = Field(default=None, description="Current file number in batch")
    sync_total: Optional[int] = Field(default=None, description="Total files in batch")


@router.post("/upload")
async def upload_remote_file(request: RemoteFileUploadRequest, background_tasks: BackgroundTasks):
    """Upload a file from a remote client for processing and storage."""
    try:
        from document_processor import process_document
        from services.obsidian_sync import (
            classify_document_by_filename,
            extract_original_date,
            parse_frontmatter,
        )

        config = get_vault_config(None)

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No vault configured. Use POST /api/obsidian/configure first.",
            )

        file_path = request.file_path
        # Sanitize problematic characters in file path
        import unicodedata
        file_path = unicodedata.normalize("NFKD", file_path).encode("ascii", "ignore").decode("ascii")
        for old, new in [(" <> ", " - "), ("<>", "-"), ("<", "-"), (">", "-"), ("#", ""), ("%", "percent"), ("[NA]", "NA"), ("\u2014", "-"), ("\u2013", "-")]:
            file_path = file_path.replace(old, new)
        content = request.content

        # Parse frontmatter
        frontmatter, clean_content = parse_frontmatter(content)

        # Extract title from frontmatter or filename
        title = frontmatter.get("title") if frontmatter else None
        if not title:
            title = file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]

        # Extract date
        filename = file_path.rsplit("/", 1)[-1]
        mtime_dt = datetime.fromtimestamp(request.file_mtime, tz=timezone.utc) if request.file_mtime else None
        original_date = extract_original_date(
            filename=filename,
            frontmatter=frontmatter,
            content=clean_content,
            file_mtime=mtime_dt,
        )

        # Auto-classify
        sync_options = config.get("sync_options", {})
        doc_type = None
        if sync_options.get("auto_classify", True):
            classification = classify_document_by_filename(filename, file_path)
            doc_type = classification.get("document_type")

        # Compute hash
        import hashlib

        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Check if already synced with same hash
        safe_config_id = pb.escape_filter(config["id"])
        safe_file_path = pb.escape_filter(file_path)
        existing = pb.get_first(
            "obsidian_sync_state",
            filter=f"config_id='{safe_config_id}' && file_path='{safe_file_path}'",
            fields="id,document_id,file_hash",
        )

        if existing and existing.get("file_hash") == content_hash:
            return {
                "success": True,
                "status": "unchanged",
                "file_path": file_path,
                "document_id": existing.get("document_id"),
            }

        # Create or update document
        import uuid

        doc_id = None
        if existing:
            doc_id = existing.get("document_id")
        else:
            # Check if document exists by obsidian_file_path
            existing_doc = pb.get_first(
                "documents",
                filter=f"obsidian_file_path='{safe_file_path}'",
                fields="id",
            )
            if existing_doc:
                doc_id = existing_doc["id"]
        if not doc_id:
            doc_id = str(uuid.uuid4())

        # Upsert document record
        now = datetime.now(timezone.utc).isoformat()
        doc_data = {
            "filename": filename,
            "title": title,
            "file_type": file_path.rsplit(".", 1)[-1] if "." in file_path else "md",
            "source_platform": "obsidian",
            "obsidian_file_path": file_path,
            "last_synced_at": now,
        }

        if original_date:
            doc_data["original_date"] = original_date.isoformat()
        if doc_type:
            doc_data["document_type"] = doc_type

        # Try update first, create if not found
        try:
            pb.update_record("documents", doc_id, doc_data)
        except Exception:
            doc_data["id"] = doc_id
            pb.create_record("documents", doc_data)

        # Update sync state
        safe_frontmatter = None
        if frontmatter:
            safe_frontmatter = {}
            for k, v in frontmatter.items():
                if isinstance(v, datetime):
                    safe_frontmatter[k] = v.isoformat()
                elif isinstance(v, list):
                    safe_frontmatter[k] = [item.isoformat() if isinstance(item, datetime) else item for item in v]
                else:
                    safe_frontmatter[k] = v

        sync_state_data = {
            "config_id": config["id"],
            "file_path": file_path,
            "document_id": doc_id,
            "file_hash": content_hash,
            "sync_status": "synced",
            "last_synced_at": now,
            "frontmatter": safe_frontmatter,
        }

        if existing:
            pb.update_record("obsidian_sync_state", existing["id"], sync_state_data)
        else:
            pb.create_record("obsidian_sync_state", sync_state_data)

        # Process document for embeddings in background
        background_tasks.add_task(process_document, doc_id)

        status = "updated" if existing else "created"

        # Auto-link to DISCO initiatives and projects if this is a new document
        if status == "created":
            from services.obsidian_sync import auto_link_document_to_initiatives

            linked = auto_link_document_to_initiatives(doc_id, file_path, None)
            if linked:
                logger.info(f"[Remote Upload] Auto-linked to {linked} initiative(s)/project(s)")

        logger.info(f"[Remote Upload] {status}: {file_path}")

        # Track local agent activity
        now_utc = datetime.now(timezone.utc)
        if "owner" not in _agent_activity:
            _agent_activity["owner"] = {
                "last_upload": now_utc,
                "uploads_since": 1,
                "started_at": now_utc,
            }
        else:
            _agent_activity["owner"]["last_upload"] = now_utc
            _agent_activity["owner"]["uploads_since"] += 1
        if request.sync_current is not None and request.sync_total is not None:
            _agent_activity["owner"]["sync_current"] = request.sync_current
            _agent_activity["owner"]["sync_total"] = request.sync_total

        return {
            "success": True,
            "status": status,
            "file_path": file_path,
            "document_id": doc_id,
            "title": title,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remote upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/reverse-sync")
async def reverse_sync(since: Optional[str] = None):
    """Get documents that need to be synced back to the local Obsidian vault."""
    try:
        filter_str = "needs_reverse_sync=true && obsidian_file_path!=''"
        if since:
            safe_since = pb.escape_filter(since)
            filter_str += f" && updated>'{safe_since}'"

        documents_raw = pb.get_all(
            "documents",
            filter=filter_str,
            fields="id,title,obsidian_file_path,storage_path,updated,file_size",
            sort="updated",
        )

        documents = []
        for doc in documents_raw:
            # TODO: Storage download needs PocketBase file API instead of Supabase storage
            content = None
            documents.append(
                {
                    "document_id": doc["id"],
                    "obsidian_file_path": doc["obsidian_file_path"],
                    "content": content,
                    "updated_at": doc["updated"],
                    "title": doc["title"],
                }
            )

        return {
            "success": True,
            "count": len(documents),
            "documents": documents,
        }

    except Exception as e:
        logger.error(f"Reverse sync error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch reverse sync documents") from e


@router.post("/reverse-sync/confirm")
async def confirm_reverse_sync(data: dict):
    """Mark documents as reverse-synced after the local client has written them."""
    try:
        document_ids = data.get("document_ids", [])
        if not document_ids:
            return {"success": True, "updated": 0}

        now = datetime.now(timezone.utc).isoformat()

        updated = 0
        for doc_id in document_ids:
            try:
                pb.update_record("documents", doc_id, {
                    "needs_reverse_sync": False,
                    "reverse_synced_at": now,
                })
                updated += 1
            except Exception:
                pass

        logger.info(f"Confirmed reverse sync for {updated} documents")

        return {"success": True, "updated": updated}

    except Exception as e:
        logger.error(f"Reverse sync confirm error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to confirm reverse sync") from e
