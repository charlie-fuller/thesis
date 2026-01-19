#!/usr/bin/env python3
"""
Seed Manual Agent Documentation

Seeds the Manual agent's knowledge base with Thesis platform documentation
from the repository. This includes user guides, admin guides, and key
reference documents.

Usage:
    cd backend
    source venv/bin/activate

    # Seed docs for a specific user/client
    python -m scripts.seed_manual_docs --user-id <uuid> --client-id <uuid>

    # Dry run (show what would be seeded without actually doing it)
    python -m scripts.seed_manual_docs --user-id <uuid> --client-id <uuid> --dry-run

    # Refresh existing docs (re-sync changed files)
    python -m scripts.seed_manual_docs --user-id <uuid> --client-id <uuid> --refresh

Environment Variables:
    SUPABASE_URL - Supabase URL (required)
    SUPABASE_SERVICE_ROLE_KEY - Supabase service key (required)

Documentation Sources:
    - docs/help/user/*.md     - User guide modules
    - docs/help/admin/*.md    - Admin guide modules
    - CLAUDE.md               - Platform specification
    - README.md               - Feature overview
    - docs/AGENT_GUARDRAILS.md - Agent behavior reference
    - USER_GUIDE.md           - User-facing guide
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


# Documentation paths to seed (relative to repo root)
DOCS_TO_SEED = [
    # User guides (primary)
    "docs/help/user",
    # Admin guides
    "docs/help/admin",
    # Key reference documents
    "CLAUDE.md",
    "README.md",
    "USER_GUIDE.md",
    "docs/AGENT_GUARDRAILS.md",
    "docs/README.md",
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed Manual agent with platform documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--user-id",
        required=True,
        help="UUID of the user to own the documents"
    )

    parser.add_argument(
        "--client-id",
        required=True,
        help="UUID of the client for the documents"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be seeded without making changes"
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-sync changed files (updates existing docs)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def setup_logging(verbose: bool = False):
    """Configure logging."""
    import logging

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    return logging.getLogger(__name__)


def validate_environment():
    """Validate required environment variables."""
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please set these in your .env file or environment")
        sys.exit(1)


def get_repo_root() -> Path:
    """Get the repository root directory."""
    # Script is at backend/scripts/seed_manual_docs.py
    # Repo root is two levels up
    return Path(__file__).parent.parent.parent


def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of file content."""
    content = file_path.read_bytes()
    return hashlib.md5(content).hexdigest()


def generate_storage_path(relative_path: str) -> str:
    """Generate a unique storage path for the document."""
    # Replace path separators and create a flat storage path
    safe_path = relative_path.replace("/", "_").replace("\\", "_")
    return f"manual_docs/{safe_path}"


def generate_title(file_path: Path) -> str:
    """Generate a human-readable title from the file path."""
    stem = file_path.stem

    # Remove numeric prefixes like "00-", "01-"
    if stem[:2].isdigit() and stem[2] == "-":
        stem = stem[3:]

    # Convert to title case and replace separators
    title = stem.replace("-", " ").replace("_", " ").title()

    return title


def collect_files_to_seed(repo_root: Path, logger) -> list[tuple[Path, str]]:
    """Collect all files to seed, returns list of (file_path, relative_path) tuples."""
    files = []

    for doc_path in DOCS_TO_SEED:
        full_path = repo_root / doc_path

        if full_path.is_file():
            # Single file
            if full_path.suffix == ".md":
                files.append((full_path, doc_path))
                logger.debug(f"  Found file: {doc_path}")
        elif full_path.is_dir():
            # Directory - get all markdown files
            for md_file in sorted(full_path.glob("**/*.md")):
                relative = str(md_file.relative_to(repo_root))
                files.append((md_file, relative))
                logger.debug(f"  Found file: {relative}")
        else:
            logger.warning(f"  Path not found: {doc_path}")

    return files


def seed_documents(args, logger):
    """Main seeding logic."""
    from database import get_supabase

    supabase = get_supabase()
    repo_root = get_repo_root()

    logger.info("Manual Agent Documentation Seeder")
    logger.info(f"Repo root: {repo_root}")
    logger.info(f"User ID: {args.user_id}")
    logger.info(f"Client ID: {args.client_id}")
    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made")
    if args.refresh:
        logger.info("REFRESH MODE - will update changed files")

    # Get Manual agent ID
    logger.info("Looking up Manual agent...")
    agent_result = supabase.table("agents").select("id").eq("name", "manual").execute()

    if not agent_result.data:
        logger.error("Manual agent not found in database!")
        logger.error("Run the migration first: 023_add_manual_agent.sql")
        sys.exit(1)

    manual_agent_id = agent_result.data[0]["id"]
    logger.info(f"Manual agent ID: {manual_agent_id}")

    # Collect files to seed
    logger.info("Scanning documentation sources...")
    files = collect_files_to_seed(repo_root, logger)
    logger.info(f"Found {len(files)} documentation files")

    # Track stats
    stats = {
        "added": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    # Process each file
    for file_path, relative_path in files:
        storage_path = generate_storage_path(relative_path)
        file_hash = get_file_hash(file_path)
        title = generate_title(file_path)

        logger.debug(f"Processing: {relative_path}")
        logger.debug(f"  Storage path: {storage_path}")
        logger.debug(f"  Title: {title}")
        logger.debug(f"  Hash: {file_hash}")

        # Check if document already exists
        existing = supabase.table("documents") \
            .select("id") \
            .eq("storage_path", storage_path) \
            .execute()

        if existing.data:
            doc = existing.data[0]

            # File changed - update if refresh mode
            if args.refresh:
                if args.dry_run:
                    logger.info(f"  Would update: {relative_path}")
                    stats["updated"] += 1
                    continue

                try:
                    # Update storage
                    content = file_path.read_bytes()
                    supabase.storage.from_("documents").update(
                        path=storage_path,
                        file=content,
                        file_options={"content-type": "text/markdown", "upsert": "true"}
                    )

                    # Update document record
                    supabase.table("documents").update({
                        "title": title,
                        "processed": False,  # Re-process for embeddings
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", doc["id"]).execute()

                    logger.info(f"  Updated: {relative_path}")
                    stats["updated"] += 1

                except Exception as e:
                    logger.error(f"  Failed to update {relative_path}: {e}")
                    stats["failed"] += 1
            else:
                logger.debug(f"  Skipping (exists): {relative_path}")
                stats["skipped"] += 1
            continue

        # New document - create it
        if args.dry_run:
            logger.info(f"  Would add: {relative_path}")
            stats["added"] += 1
            continue

        try:
            content = file_path.read_bytes()

            # Upload to storage
            supabase.storage.from_("documents").upload(
                path=storage_path,
                file=content,
                file_options={"content-type": "text/markdown"}
            )

            # Get storage URL
            storage_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/documents/{storage_path}"

            # Create document record
            doc_record = {
                "user_id": args.user_id,
                "client_id": args.client_id,
                "uploaded_by": args.user_id,
                "filename": file_path.name,
                "title": title,
                "storage_path": storage_path,
                "storage_url": storage_url,
                "source_platform": "seed_script",
                "processed": False,
            }

            doc_result = supabase.table("documents").insert(doc_record).execute()
            document_id = doc_result.data[0]["id"]

            # Link to Manual agent
            supabase.table("agent_knowledge_base").insert({
                "agent_id": manual_agent_id,
                "document_id": document_id,
                "added_by": args.user_id,
                "priority": 10,  # High priority for seeded docs
                "relevance_score": 1.0,
                "classification_source": "seed_script",
                "classification_confidence": 1.0,
                "user_confirmed": True,
            }).execute()

            logger.info(f"  Added: {relative_path}")
            stats["added"] += 1

        except Exception as e:
            logger.error(f"  Failed to add {relative_path}: {e}")
            stats["failed"] += 1

    # Summary
    logger.info("")
    logger.info("Seeding complete!")
    logger.info(f"  Added: {stats['added']}")
    logger.info(f"  Updated: {stats['updated']}")
    logger.info(f"  Skipped: {stats['skipped']}")
    logger.info(f"  Failed: {stats['failed']}")

    if stats["added"] > 0 and not args.dry_run:
        logger.info("")
        logger.info("NOTE: Run document processing to generate embeddings for new documents")


def main():
    """Entry point."""
    args = parse_args()
    logger = setup_logging(args.verbose)
    validate_environment()

    try:
        seed_documents(args, logger)
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
