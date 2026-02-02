"""Vault Watcher Scheduler.

Manages the file system watcher for Obsidian vault sync.
Starts automatically with the backend server when VAULT_WATCHER_USER_ID is configured.
"""

import os
import threading
from pathlib import Path
from typing import Optional

from logger_config import get_logger

logger = get_logger(__name__)

# Global watcher instance
_watcher = None
_watcher_user_id: Optional[str] = None


def _on_sync_complete(file_path: str, stats: dict) -> None:
    """Callback for sync completion logging."""
    action = (
        "added"
        if stats.get("files_added")
        else "updated"
        if stats.get("files_updated")
        else "deleted"
        if stats.get("files_deleted")
        else "skipped"
    )
    logger.debug(f"[Vault Watcher] Synced: {file_path} ({action})")


def start_vault_watcher(user_id: Optional[str] = None, initial_sync: bool = True) -> bool:
    """Start the vault watcher for the specified user.

    Args:
        user_id: UUID of the user whose vault to watch.
                 If not provided, uses VAULT_WATCHER_USER_ID env var.
        initial_sync: Whether to perform initial sync on startup.

    Returns:
        True if watcher started successfully, False otherwise.
    """
    global _watcher, _watcher_user_id

    # Get user ID from parameter or environment
    user_id = user_id or os.getenv("VAULT_WATCHER_USER_ID")

    if not user_id:
        logger.info(
            "Vault watcher not started: VAULT_WATCHER_USER_ID not configured. "
            "Set this env var to enable automatic vault watching."
        )
        return False

    try:
        from services.obsidian_sync import (
            ObsidianSyncError,
            ObsidianVaultWatcher,
            get_vault_config,
            sync_vault,
        )

        # Get vault config for this user
        config = get_vault_config(user_id)

        if not config:
            logger.warning(
                f"Vault watcher not started: No vault configured for user {user_id}. "
                "Configure a vault via POST /api/obsidian/configure first."
            )
            return False

        vault_path = config["vault_path"]
        vault_name = config.get("vault_name", Path(vault_path).name)

        # Validate vault path exists
        if not Path(vault_path).exists():
            logger.error(f"Vault watcher not started: Vault path does not exist: {vault_path}")
            return False

        # Create and start watcher first (non-blocking)
        _watcher = ObsidianVaultWatcher(config=config, on_sync_complete=_on_sync_complete)
        _watcher.start()
        _watcher_user_id = user_id

        logger.info(f"Vault watcher started for '{vault_name}' at {vault_path}")

        # Perform initial sync in background thread (non-blocking)
        if initial_sync:

            def _background_sync():
                logger.info(f"[Vault Watcher] Performing initial sync for '{vault_name}'...")
                try:
                    result = sync_vault(config, trigger_source="watcher_init")
                    logger.info(
                        f"[Vault Watcher] Initial sync complete: {result['files_added']} added, "
                        f"{result['files_updated']} updated, {result['files_skipped']} skipped"
                    )
                except ObsidianSyncError as e:
                    logger.warning(f"[Vault Watcher] Initial sync failed: {e}")

            sync_thread = threading.Thread(target=_background_sync, daemon=True)
            sync_thread.start()
            logger.info("[Vault Watcher] Initial sync started in background")

        return True

    except Exception as e:
        logger.error(f"Failed to start vault watcher: {e}")
        return False


def stop_vault_watcher() -> None:
    """Stop the vault watcher if running."""
    global _watcher, _watcher_user_id

    if _watcher:
        try:
            _watcher.stop()
            logger.info("Vault watcher stopped")
        except Exception as e:
            logger.error(f"Error stopping vault watcher: {e}")
        finally:
            _watcher = None
            _watcher_user_id = None


def is_watcher_running() -> bool:
    """Check if the vault watcher is currently running."""
    return _watcher is not None and _watcher._running


def get_watcher_status() -> dict:
    """Get current watcher status.

    Returns:
        Dict with watcher status information.
    """
    if not _watcher:
        return {
            "running": False,
            "user_id": None,
            "vault_path": None,
            "message": "Vault watcher not started",
        }

    return {
        "running": _watcher._running,
        "user_id": _watcher_user_id,
        "vault_path": str(_watcher.vault_path),
        "vault_name": _watcher.config.get("vault_name"),
    }
