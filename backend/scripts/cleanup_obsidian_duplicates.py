"""Cleanup duplicate Obsidian-synced documents.

This script identifies documents with the same filename from Obsidian sync
and keeps only the most recent one, deleting the older duplicates.

Run from backend directory:
    uv run python scripts/cleanup_obsidian_duplicates.py --dry-run
    uv run python scripts/cleanup_obsidian_duplicates.py  # Actually delete
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

# Add backend to path dynamically
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)


def find_obsidian_duplicates(supabase):
    """Find all Obsidian documents with duplicate filenames."""
    # Query all Obsidian-synced documents
    result = (
        supabase.table("documents")
        .select(
            "id, filename, title, storage_path, uploaded_at, source_platform, obsidian_file_path"
        )
        .eq("source_platform", "obsidian")
        .order("uploaded_at", desc=True)
        .execute()
    )

    # Group by filename
    by_filename = defaultdict(list)
    for doc in result.data:
        fn = doc.get("filename", "unknown")
        by_filename[fn].append(doc)

    # Find duplicates (more than 1 doc with same filename)
    duplicates = {}
    for filename, docs in by_filename.items():
        if len(docs) > 1:
            # Sort by upload date descending (newest first)
            docs_sorted = sorted(docs, key=lambda d: d.get("uploaded_at", ""), reverse=True)
            duplicates[filename] = {
                "keep": docs_sorted[0],  # Keep the newest
                "delete": docs_sorted[1:],  # Delete the rest
            }

    return duplicates


def cleanup_document(supabase, doc_id, dry_run=True):
    """Delete a document and its chunks."""
    if dry_run:
        logger.info(f"  [DRY RUN] Would delete document: {doc_id}")
        return True

    try:
        # Delete chunks first
        supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()

        # Delete agent knowledge base links
        supabase.table("agent_knowledge_base").delete().eq("document_id", doc_id).execute()

        # Delete any sync state references
        supabase.table("obsidian_sync_state").update({"document_id": None}).eq(
            "document_id", doc_id
        ).execute()

        # Delete the document record
        supabase.table("documents").delete().eq("id", doc_id).execute()

        logger.info(f"  Deleted document: {doc_id}")
        return True

    except Exception as e:
        logger.error(f"  Failed to delete {doc_id}: {e}")
        return False


def update_sync_states(supabase, duplicates, dry_run=True):
    """Update sync states to point to the kept document."""
    for _filename, info in duplicates.items():
        keep_doc = info["keep"]

        # Find any sync state that references documents being deleted
        # and update it to point to the kept document
        for delete_doc in info["delete"]:
            if dry_run:
                logger.info(
                    f"  [DRY RUN] Would update sync states from {delete_doc['id']} to {keep_doc['id']}"
                )
            else:
                try:
                    supabase.table("obsidian_sync_state").update(
                        {"document_id": keep_doc["id"]}
                    ).eq("document_id", delete_doc["id"]).execute()
                    logger.info("  Updated sync states to point to kept document")
                except Exception as e:
                    logger.warning(f"  Could not update sync states: {e}")


def main():
    parser = argparse.ArgumentParser(description="Cleanup duplicate Obsidian documents")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without deleting")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    dry_run = args.dry_run
    force = args.force

    logger.info("=" * 60)
    logger.info("Obsidian Duplicate Document Cleanup")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE - WILL DELETE'}")
    logger.info("=" * 60)

    supabase = get_supabase()

    # Find duplicates
    logger.info("\nFinding duplicate documents...")
    duplicates = find_obsidian_duplicates(supabase)

    if not duplicates:
        logger.info("No duplicates found!")
        return

    # Calculate stats
    total_duplicates = sum(len(info["delete"]) for info in duplicates.values())
    unique_files = len(duplicates)

    logger.info(
        f"\nFound {total_duplicates} duplicate documents across {unique_files} unique files"
    )

    # Show what will be done
    logger.info("\n" + "=" * 60)
    logger.info("CHANGES TO BE MADE:")
    logger.info("=" * 60)

    for filename, info in sorted(duplicates.items()):
        logger.info(f"\n{filename}:")
        logger.info(f"  KEEP: {info['keep']['id']} (uploaded {info['keep']['uploaded_at']})")
        for doc in info["delete"]:
            logger.info(f"  DELETE: {doc['id']} (uploaded {doc['uploaded_at']})")

    # Confirm if not dry run and not forced
    if not dry_run and not force:
        logger.info("\n" + "=" * 60)
        response = input(f"\nDelete {total_duplicates} duplicate documents? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            return

    # Update sync states first
    logger.info("\nUpdating sync states...")
    update_sync_states(supabase, duplicates, dry_run)

    # Delete duplicates
    logger.info("\nDeleting duplicate documents...")
    deleted = 0
    failed = 0

    for _filename, info in duplicates.items():
        for doc in info["delete"]:
            if cleanup_document(supabase, doc["id"], dry_run):
                deleted += 1
            else:
                failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    if dry_run:
        logger.info(f"Would delete: {deleted} documents")
    else:
        logger.info(f"Deleted: {deleted} documents")
        logger.info(f"Failed: {failed} documents")

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
