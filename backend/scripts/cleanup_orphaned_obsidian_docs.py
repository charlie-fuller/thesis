"""Cleanup orphaned Obsidian documents whose paths don't match the filesystem.

Identifies documents in the DB whose obsidian_file_path doesn't correspond to
any actual file in the vault, and deletes them along with their chunks.

Common case: a folder was moved (e.g., carla-cooper/ -> Team/carla-cooper/)
and the old documents persisted without being cleaned up.

Run from backend directory:
    .venv/bin/python scripts/cleanup_orphaned_obsidian_docs.py --dry-run
    .venv/bin/python scripts/cleanup_orphaned_obsidian_docs.py  # Actually delete
"""

import argparse
import sys
from pathlib import Path

# Add backend to path dynamically
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")

from database import get_supabase
from logger_config import get_logger
from services.obsidian_sync import get_effective_sync_options, scan_vault

logger = get_logger(__name__)


def get_vault_config(supabase):
    """Get the active vault config."""
    result = supabase.table("obsidian_vault_configs").select("*").eq("is_active", True).limit(1).execute()
    if not result.data:
        return None
    return result.data[0]


def get_all_obsidian_documents(supabase, user_id: str):
    """Get all obsidian documents with pagination."""
    docs = []
    page_size = 1000
    offset = 0

    while True:
        result = (
            supabase.table("documents")
            .select("id, filename, obsidian_file_path, uploaded_at")
            .eq("source_platform", "obsidian")
            .eq("uploaded_by", user_id)
            .not_.is_("obsidian_file_path", "null")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        docs.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size

    return docs


def find_orphans(supabase, config):
    """Find documents whose obsidian_file_path doesn't match any file on disk."""
    vault_path = Path(config["vault_path"])
    sync_options = get_effective_sync_options(config.get("sync_options"))

    # Scan the vault to get all files currently on disk
    files = scan_vault(
        vault_path=vault_path,
        include_patterns=sync_options["include_patterns"],
        exclude_patterns=sync_options["exclude_patterns"],
        max_file_size_mb=sync_options.get("max_file_size_mb", 10),
    )

    # Build set of valid relative paths
    valid_paths = set()
    for file_path in files:
        relative_path = str(file_path.relative_to(vault_path))
        valid_paths.add(relative_path)

    print(f"Found {len(valid_paths)} files on disk")

    # Get all documents from the DB
    docs = get_all_obsidian_documents(supabase, config["user_id"])
    print(f"Found {len(docs)} obsidian documents in DB")

    # Find orphans
    orphans = []
    for doc in docs:
        doc_path = doc.get("obsidian_file_path", "")
        if doc_path and doc_path not in valid_paths:
            orphans.append(doc)

    return orphans


def delete_orphans(supabase, orphans, dry_run=True):
    """Delete orphaned documents and their chunks."""
    if not orphans:
        print("No orphaned documents found.")
        return 0

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Found {len(orphans)} orphaned document(s):\n")

    for doc in orphans:
        doc_id = doc["id"]
        doc_path = doc.get("obsidian_file_path", "unknown")
        filename = doc.get("filename", "unknown")
        uploaded = doc.get("uploaded_at", "unknown")

        print(f"  {'Would delete' if dry_run else 'Deleting'}: {doc_path}")
        print(f"    ID: {doc_id}, filename: {filename}, uploaded: {uploaded}")

        if not dry_run:
            try:
                supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
                supabase.table("documents").delete().eq("id", doc_id).execute()
                print("    Deleted successfully")
            except Exception as e:
                print(f"    ERROR: {e}")

    deleted = len(orphans) if not dry_run else 0
    print(f"\n{'[DRY RUN] Would delete' if dry_run else 'Deleted'} {len(orphans)} orphaned document(s)")
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Cleanup orphaned Obsidian documents")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    args = parser.parse_args()

    supabase = get_supabase()
    config = get_vault_config(supabase)

    if not config:
        print("ERROR: No active vault config found")
        sys.exit(1)

    print(f"Vault: {config['vault_name']}")
    print(f"Path: {config['vault_path']}")
    print()

    orphans = find_orphans(supabase, config)
    delete_orphans(supabase, orphans, dry_run=args.dry_run)

    if args.dry_run and orphans:
        print("\nRe-run without --dry-run to actually delete these documents.")


if __name__ == "__main__":
    main()
