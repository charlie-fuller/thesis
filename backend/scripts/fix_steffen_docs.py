"""One-off script to fix Steffen/Stefan document records in Supabase.

Fixes:
1. Delete old "Stefan" document records (duplicates of already-existing "Steffen" records)
2. Fix future date (2026-05-20 -> 2026-02-04) on Meeting Guide document
3. Delete orphaned "Top 10 Questions for Stefan and Raza.md" record

Handles the case where renamed files already have new records from a prior sync.
"""

import os
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_supabase

RETRY_DELAY = 5
MAX_RETRIES = 3


def db_op(fn, description):
    """Execute a DB operation with retries for Cloudflare issues."""
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  Retry {attempt + 1}/{MAX_RETRIES} for: {description} ({e})")
                time.sleep(RETRY_DELAY)
            else:
                raise


def main():
    db = get_supabase()

    # Old document IDs (with "Stefan" in the name)
    old_meeting_guide_id = "2c21e076-cf87-48d4-8df1-29dbe1cf608a"
    old_open_questions_id = "c63cfd9c-944b-470f-acfa-d3d5c65cbbe0"
    old_top10_id = "c20f764d-ecc5-478c-b4da-6338687aca5c"

    # New correct paths
    meeting_guide_path = "projects/AI-Platform-Governance/Meeting Guide - Steffen and Raza Walkthrough.md"
    open_questions_path = "projects/AI-Platform-Governance/Open Questions for Steffen and Raza.md"

    # Step 1: Check if "Steffen" docs already exist
    print("Checking for existing 'Steffen' documents...")
    existing = db_op(
        lambda: db.table("documents")
        .select("id, title, obsidian_file_path, original_date")
        .ilike("obsidian_file_path", "%Steffen%Raza%")
        .execute(),
        "query existing Steffen docs",
    )

    steffen_docs = {doc["obsidian_file_path"]: doc for doc in (existing.data or [])}
    for _path, doc in steffen_docs.items():
        print(f"  Found: {doc['id']} - {doc['title']} (date: {doc.get('original_date')})")

    # Step 2: Fix Meeting Guide date if Steffen version exists
    if meeting_guide_path in steffen_docs:
        mg = steffen_docs[meeting_guide_path]
        if mg.get("original_date") != "2026-02-04":
            print(f"\nFixing Meeting Guide date: {mg.get('original_date')} -> 2026-02-04")
            db_op(
                lambda: db.table("documents").update({"original_date": "2026-02-04"}).eq("id", mg["id"]).execute(),
                "update Meeting Guide date",
            )
            print("  Done")
        else:
            print(f"\nMeeting Guide date already correct: {mg.get('original_date')}")

        # Delete old Stefan version
        print(f"\nDeleting old 'Stefan' Meeting Guide ({old_meeting_guide_id})...")
        db_op(
            lambda: db.table("obsidian_sync_state").delete().eq("document_id", old_meeting_guide_id).execute(),
            "delete old meeting guide sync state",
        )
        db_op(
            lambda: db.table("documents").delete().eq("id", old_meeting_guide_id).execute(),
            "delete old meeting guide doc",
        )
        print("  Done")
    else:
        # No Steffen version yet - rename the Stefan one
        print("\nNo 'Steffen' Meeting Guide found. Renaming Stefan version...")
        db_op(
            lambda: db.table("documents")
            .update(
                {
                    "title": "Meeting Guide - Steffen and Raza Walkthrough",
                    "obsidian_file_path": meeting_guide_path,
                    "original_date": "2026-02-04",
                }
            )
            .eq("id", old_meeting_guide_id)
            .execute(),
            "rename meeting guide",
        )
        print("  Done")

    # Step 3: Handle Open Questions
    if open_questions_path in steffen_docs:
        print(f"\nDeleting old 'Stefan' Open Questions ({old_open_questions_id})...")
        db_op(
            lambda: db.table("obsidian_sync_state").delete().eq("document_id", old_open_questions_id).execute(),
            "delete old open questions sync state",
        )
        db_op(
            lambda: db.table("documents").delete().eq("id", old_open_questions_id).execute(),
            "delete old open questions doc",
        )
        print("  Done")
    else:
        print("\nNo 'Steffen' Open Questions found. Renaming Stefan version...")
        db_op(
            lambda: db.table("documents")
            .update(
                {
                    "title": "Open Questions for Steffen and Raza",
                    "obsidian_file_path": open_questions_path,
                }
            )
            .eq("id", old_open_questions_id)
            .execute(),
            "rename open questions",
        )
        print("  Done")

    # Step 4: Delete orphaned Top 10 Questions
    print(f"\nDeleting orphaned 'Top 10 Questions for Stefan and Raza' ({old_top10_id})...")
    # Check for initiative links first
    links = db_op(
        lambda: db.table("disco_initiative_documents").select("id").eq("document_id", old_top10_id).execute(),
        "check initiative links",
    )
    if links.data:
        print(f"  WARNING: Document is linked to {len(links.data)} initiative(s). Skipping delete.")
    else:
        db_op(
            lambda: db.table("obsidian_sync_state").delete().eq("document_id", old_top10_id).execute(),
            "delete top10 sync state",
        )
        db_op(
            lambda: db.table("documents").delete().eq("id", old_top10_id).execute(),
            "delete top10 doc",
        )
        print("  Done")

    # Step 5: Clean up old sync state entries with Stefan/Steffan paths
    print("\nCleaning up old sync state entries...")
    old_paths = [
        "projects/AI-Platform-Governance/Meeting Guide - Stefan and Raza Walkthrough.md",
        "projects/AI-Platform-Governance/Meeting Guide - Steffan and Raza Walkthrough.md",
        "projects/AI-Platform-Governance/Open Questions for Stefan and Raza.md",
        "projects/AI-Platform-Governance/Open Questions for Steffan and Raza.md",
        "projects/AI-Platform-Governance/Top 10 Questions for Stefan and Raza.md",
    ]
    for old_path in old_paths:
        try:
            result = db_op(
                lambda p=old_path: db.table("obsidian_sync_state").delete().eq("file_path", p).execute(),
                f"delete sync state for {old_path}",
            )
            if result.data:
                print(f"  Deleted sync state: {old_path}")
        except Exception:
            pass  # May not exist

    print("\nDone!")


if __name__ == "__main__":
    main()
