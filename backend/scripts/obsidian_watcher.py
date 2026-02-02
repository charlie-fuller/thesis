#!/usr/bin/env python3
"""Obsidian Vault Watcher

Standalone script to run the Obsidian file watcher as a background process.
Monitors configured vault directories for .md file changes and syncs them
to the Thesis Knowledge Base.

Usage:
    cd backend
    source venv/bin/activate

    # Watch vault for a specific user
    python -m scripts.obsidian_watcher --user-id <uuid>

    # Watch vault from environment variable
    OBSIDIAN_VAULT_PATH=/path/to/vault python -m scripts.obsidian_watcher --user-id <uuid>

    # Run with verbose logging
    python -m scripts.obsidian_watcher --user-id <uuid> --verbose

Environment Variables:
    OBSIDIAN_VAULT_PATH - Override vault path (optional)
    SUPABASE_URL - Supabase URL (required)
    SUPABASE_SERVICE_ROLE_KEY - Supabase service key (required)

Signals:
    SIGINT (Ctrl+C) - Graceful shutdown
    SIGTERM - Graceful shutdown
"""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Watch an Obsidian vault and sync changes to Thesis KB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--user-id", required=True, help="UUID of the user whose vault to watch")

    parser.add_argument(
        "--vault-path",
        help="Override vault path (default: from database config or OBSIDIAN_VAULT_PATH env)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--initial-sync", action="store_true", help="Perform initial sync before starting watcher"
    )

    return parser.parse_args()


def setup_logging(verbose: bool = False):
    """Configure logging for the watcher."""
    import logging

    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce noise from other loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.INFO if verbose else logging.WARNING)


def validate_environment():
    """Validate required environment variables."""
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please set these in your .env file or environment")
        sys.exit(1)


def on_sync_complete(file_path: str, stats: dict):
    """Callback for sync completion."""
    action = (
        "added"
        if stats.get("files_added")
        else "updated"
        if stats.get("files_updated")
        else "deleted"
        if stats.get("files_deleted")
        else "skipped"
    )
    print(f"  Synced: {file_path} ({action})")


async def run_watcher(args):
    """Main watcher loop."""
    from logger_config import get_logger
    from services.obsidian_sync import (
        ObsidianSyncError,
        ObsidianVaultWatcher,
        create_vault_config,
        get_vault_config,
        sync_vault,
    )

    logger = get_logger(__name__)

    user_id = args.user_id
    vault_path_override = args.vault_path or os.getenv("OBSIDIAN_VAULT_PATH")

    logger.info("Starting Obsidian Vault Watcher")
    logger.info(f"User ID: {user_id}")

    # Get or create vault config
    config = get_vault_config(user_id)

    if vault_path_override:
        # Create or update config with override path
        if config and config.get("vault_path") != vault_path_override:
            logger.info(f"Vault path override: {vault_path_override}")

            from database import get_supabase

            supabase = get_supabase()

            # Get user's client_id
            user_result = (
                supabase.table("users").select("client_id").eq("id", user_id).single().execute()
            )

            if not user_result.data or not user_result.data.get("client_id"):
                logger.error("User not found or has no client association")
                sys.exit(1)

            client_id = user_result.data["client_id"]

            config = create_vault_config(
                user_id=user_id, client_id=client_id, vault_path=vault_path_override
            )
        elif not config:
            logger.error("No vault configured and no override path provided")
            logger.error("Configure a vault first via API or provide --vault-path")
            sys.exit(1)

    if not config:
        logger.error("No Obsidian vault configured for this user")
        logger.error("Configure a vault first using the API: POST /api/obsidian/configure")
        sys.exit(1)

    vault_path = config["vault_path"]
    vault_name = config.get("vault_name", Path(vault_path).name)

    logger.info(f"Vault: {vault_name}")
    logger.info(f"Path: {vault_path}")

    # Validate vault path exists
    if not Path(vault_path).exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Perform initial sync if requested
    if args.initial_sync:
        logger.info("Performing initial sync...")
        try:
            result = sync_vault(config, trigger_source="watcher_init")
            logger.info(
                f"Initial sync complete: {result['files_added']} added, "
                f"{result['files_updated']} updated, "
                f"{result['files_skipped']} skipped"
            )
        except ObsidianSyncError as e:
            logger.error(f"Initial sync failed: {e}")
            # Continue with watcher anyway

    # Create and start watcher
    watcher = ObsidianVaultWatcher(config=config, on_sync_complete=on_sync_complete)

    # Set up signal handlers for graceful shutdown
    stop_event = asyncio.Event()

    def signal_handler(signum, frame):
        signame = signal.Signals(signum).name
        logger.info(f"Received {signame}, shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        watcher.start()
        logger.info("Watcher started. Press Ctrl+C to stop.")
        logger.info("Watching for file changes...")

        # Keep running until stop signal
        while not stop_event.is_set():
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Watcher error: {e}")
        raise
    finally:
        watcher.stop()
        logger.info("Watcher stopped")


def main():
    """Entry point."""
    args = parse_args()

    # Setup
    setup_logging(args.verbose)
    validate_environment()

    # Run the async watcher
    try:
        asyncio.run(run_watcher(args))
    except KeyboardInterrupt:
        print("\nShutdown complete")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
