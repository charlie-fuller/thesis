#!/usr/bin/env python3
"""
Script to sync PuRDy System KB from filesystem to database.
Run from backend directory: python scripts/sync_purdy_kb.py
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.purdy.system_kb_service import sync_kb_from_filesystem, get_kb_stats

async def main():
    print("=" * 60)
    print("PuRDy System KB Sync")
    print("=" * 60)

    try:
        print("\nSyncing KB files from filesystem...")
        stats = await sync_kb_from_filesystem()

        print(f"\nSync Results:")
        print(f"  Created: {stats['created']}")
        print(f"  Updated: {stats['updated']}")
        print(f"  Skipped (unchanged): {stats['skipped']}")
        print(f"  Errors: {stats['errors']}")
        print(f"\nFiles processed:")
        for f in stats['files_processed']:
            print(f"  - {f}")

        print("\n" + "-" * 60)
        print("Getting KB stats...")
        kb_stats = await get_kb_stats()

        print(f"\nKB Statistics:")
        print(f"  Total files: {kb_stats['total_files']}")
        print(f"  Total chunks: {kb_stats['total_chunks']}")
        print(f"  By category:")
        for cat, count in kb_stats['by_category'].items():
            print(f"    - {cat}: {count}")

        print("\n" + "=" * 60)
        print("KB sync complete!")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
