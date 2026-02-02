#!/usr/bin/env python3
"""Seed historical system instruction versions (1.0 and 1.1) for version comparison feature.
Run this script after 039_seed_initial_system_instruction.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import Client, create_client


def get_supabase() -> Client:
    """Create Supabase client from environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "Supabase not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY)"
        )

    return create_client(url, key)


def read_instructions_file(filename: str) -> str:
    """Read system instructions from a file in docs/system-instructions/."""
    docs_path = Path(__file__).parent.parent.parent / "docs" / "system-instructions" / filename

    if not docs_path.exists():
        raise FileNotFoundError(f"Instructions file not found: {docs_path}")

    return docs_path.read_text(encoding="utf-8")


def seed_historical_versions():
    """Seed historical versions 1.0 and 1.1 into the database."""
    supabase = get_supabase()

    # Define versions to seed (oldest first)
    versions = [
        {
            "version_number": "1.0",
            "filename": "thesis-instructions.md",
            "version_notes": "Initial production release with Core Philosophy, Output Format, Operating Modes, Command Shortcuts, Image Generation, and Enhanced Guardrails.",
            "created_offset_days": 14,  # Created 14 days ago
        },
        {
            "version_number": "1.1",
            "filename": "thesis-instructions-v1.1.md",
            "version_notes": "Added Progressive Disclosure Protocol, Self-Description Protocol. Updated identity and operating modes with INTERNAL ONLY comments.",
            "created_offset_days": 7,  # Created 7 days ago
        },
    ]

    created_ids = []

    for version_info in versions:
        # Read the instructions content
        try:
            content = read_instructions_file(version_info["filename"])
        except FileNotFoundError as e:
            print(f"⚠️  Skipping {version_info['version_number']}: {e}")
            continue

        # Check if this version already exists
        existing = (
            supabase.table("system_instruction_versions")
            .select("id")
            .eq("version_number", version_info["version_number"])
            .execute()
        )

        if existing.data:
            print(
                f"⏭️  Version {version_info['version_number']} already exists (ID: {existing.data[0]['id']})"
            )
            continue

        # Calculate created_at timestamp (in the past)
        created_at = datetime.now(timezone.utc) - timedelta(
            days=version_info["created_offset_days"]
        )

        # Insert the version
        version_data = {
            "id": str(uuid4()),
            "version_number": version_info["version_number"],
            "content": content,
            "version_notes": version_info["version_notes"],
            "status": "archived",  # Historical versions are archived
            "created_by": None,  # System-seeded
            "is_active": False,  # Historical versions are not active
            "created_at": created_at.isoformat(),
        }

        result = supabase.table("system_instruction_versions").insert(version_data).execute()

        if result.data:
            created_ids.append((version_info["version_number"], result.data[0]["id"]))
            print(
                f"✅ Created version {version_info['version_number']} (ID: {result.data[0]['id']})"
            )
        else:
            print(f"❌ Failed to create version {version_info['version_number']}")

    if created_ids:
        print(f"\n✅ Successfully seeded {len(created_ids)} historical versions")
        for label, vid in created_ids:
            print(f"   - {label}: {vid}")
    else:
        print("\n⚠️  No new versions were created (they may already exist)")

    print("\nYou can now compare versions in the admin UI!")


if __name__ == "__main__":
    try:
        seed_historical_versions()
    except Exception as e:
        print(f"❌ Seed failed: {e}")
        sys.exit(1)
