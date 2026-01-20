#!/usr/bin/env python3
"""
Backfill original_date for existing documents.

This script scans all documents and attempts to extract the original date from:
1. Frontmatter (date, original_date, created, meeting_date fields)
2. Filename patterns
3. Document content (first 500 chars)
4. File modification time (for Obsidian files)

Usage:
    cd backend
    uv run python -m scripts.backfill_original_dates [--dry-run]
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from database import get_supabase
from services.obsidian_sync import extract_original_date, parse_frontmatter
from logger_config import get_logger

logger = get_logger(__name__)


def backfill_original_dates(dry_run: bool = False, limit: int = None):
    """
    Backfill original_date for documents that don't have one set.

    Args:
        dry_run: If True, don't actually update the database
        limit: Optional limit on number of documents to process
    """
    supabase = get_supabase()

    # Get documents without original_date
    query = supabase.table('documents').select(
        'id, filename, title, storage_url, obsidian_file_path, obsidian_vault_path, source_platform'
    ).is_('original_date', 'null')

    if limit:
        query = query.limit(limit)

    result = query.execute()
    documents = result.data or []

    print(f"Found {len(documents)} documents without original_date")
    print()

    updated = 0
    skipped = 0
    errors = 0

    for doc in documents:
        doc_id = doc['id']
        filename = doc.get('filename', '')
        title = doc.get('title', '')

        # Try to get content for date extraction
        content = None
        file_mtime = None
        frontmatter = {}

        # For Obsidian files, try to read from local filesystem
        if doc.get('source_platform') == 'obsidian' and doc.get('obsidian_vault_path') and doc.get('obsidian_file_path'):
            file_path = Path(doc['obsidian_vault_path']) / doc['obsidian_file_path']
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                    frontmatter, content = parse_frontmatter(raw_content)
                    stats = file_path.stat()
                    file_mtime = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")

        # If no local file, try to get content from document chunks
        if content is None:
            chunks_result = supabase.table('document_chunks').select(
                'content'
            ).eq('document_id', doc_id).order('chunk_index').limit(1).execute()

            if chunks_result.data:
                content = chunks_result.data[0].get('content', '')

        # Extract original date
        original_date = extract_original_date(
            filename=filename,
            frontmatter=frontmatter,
            content=content,
            file_mtime=file_mtime
        )

        display_name = title or filename
        if len(display_name) > 50:
            display_name = display_name[:47] + "..."

        if original_date:
            if dry_run:
                print(f"  [DRY RUN] Would update: {display_name} -> {original_date}")
            else:
                try:
                    supabase.table('documents').update({
                        'original_date': original_date.isoformat()
                    }).eq('id', doc_id).execute()
                    print(f"  Updated: {display_name} -> {original_date}")
                except Exception as e:
                    print(f"  ERROR updating {display_name}: {e}")
                    errors += 1
                    continue
            updated += 1
        else:
            print(f"  Skipped (no date found): {display_name}")
            skipped += 1

    print()
    print("=" * 50)
    print(f"Results:")
    print(f"  Updated: {updated}")
    print(f"  Skipped (no date found): {skipped}")
    print(f"  Errors: {errors}")

    if dry_run:
        print()
        print("This was a dry run. No changes were made.")


def main():
    parser = argparse.ArgumentParser(description='Backfill original_date for documents')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of documents to process')
    args = parser.parse_args()

    backfill_original_dates(dry_run=args.dry_run, limit=args.limit)


if __name__ == '__main__':
    main()
