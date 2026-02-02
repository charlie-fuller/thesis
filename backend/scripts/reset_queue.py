#!/usr/bin/env python3
"""Reset discovery queue - clear candidates and reset scan flags for re-scanning."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from database import get_supabase


def reset_discovery_queue():
    supabase = get_supabase()

    print("Clearing pending candidates...")

    # Clear task candidates
    result = supabase.table("task_candidates").delete().eq("status", "pending").execute()
    print(f"  - Deleted {len(result.data)} task candidates")

    # Clear opportunity candidates
    result = supabase.table("project_candidates").delete().eq("status", "pending").execute()
    print(f"  - Deleted {len(result.data)} opportunity candidates")

    # Clear stakeholder candidates
    result = supabase.table("stakeholder_candidates").delete().eq("status", "pending").execute()
    print(f"  - Deleted {len(result.data)} stakeholder candidates")

    print("\nResetting scan flags on Granola documents...")

    # Query all docs and filter in Python to avoid ilike Cloudflare issues
    all_docs = (
        supabase.table("documents")
        .select("id, obsidian_file_path")
        .not_.is_("granola_scanned_at", "null")
        .limit(2000)
        .execute()
    )

    # Filter to Granola docs in Python
    granola_ids = [
        d["id"]
        for d in (all_docs.data or [])
        if d.get("obsidian_file_path") and "Granola" in d.get("obsidian_file_path", "")
    ]

    print(f"  - Found {len(granola_ids)} scanned Granola documents")

    # Reset each one
    reset_count = 0
    for doc_id in granola_ids:
        supabase.table("documents").update({"granola_scanned_at": None}).eq("id", doc_id).execute()
        reset_count += 1

    print(f"  - Reset granola_scanned_at on {reset_count} documents")
    print("\nDone! Ready for rescan.")


if __name__ == "__main__":
    reset_discovery_queue()
