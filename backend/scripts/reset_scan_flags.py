#!/usr/bin/env python3
"""Reset Granola scan flags using RPC function."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from database import get_supabase


def reset_scan_flags():
    supabase = get_supabase()

    print("Resetting scan flags using RPC...")

    # Use the RPC function that already exists for getting Granola docs
    result = supabase.rpc(
        "get_granola_scan_status",
        {
            "p_user_id": "00000000-0000-0000-0000-000000000000"  # Will get all
        },
    ).execute()

    print(f"Current status: {result.data}")

    # Let's just update all documents with granola_scanned_at set
    print("\nResetting via direct update on scanned docs...")
    result = (
        supabase.table("documents")
        .update({"granola_scanned_at": None})
        .not_.is_("granola_scanned_at", "null")
        .execute()
    )

    print(f"Reset {len(result.data)} documents")
    print("\nDone! Ready for rescan.")


if __name__ == "__main__":
    reset_scan_flags()
