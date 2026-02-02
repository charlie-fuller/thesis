#!/usr/bin/env python3
"""Seed script to insert the initial system instruction version (1.3) into the database.

Run this AFTER the SQL migration (039_add_system_instruction_versioning.sql) has been applied.

Usage:
    python 039_seed_initial_system_instruction.py

This script:
1. Reads the default.txt system instructions file
2. Inserts it as version 1.3 (the current version)
3. Marks it as the active version
4. Optionally binds all existing conversations to this version
"""

import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)


def get_default_instructions_content() -> str:
    """Read the default system instructions file."""
    default_path = backend_dir / "system_instructions" / "default.txt"

    if not default_path.exists():
        raise FileNotFoundError(f"Default system instructions not found at: {default_path}")

    with open(default_path, "r", encoding="utf-8") as f:
        return f.read()


def seed_initial_version(bind_existing_conversations: bool = True):
    """Seed the initial system instruction version (1.3).

    Args:
        bind_existing_conversations: If True, bind all existing conversations to version 1.3
    """
    supabase = get_supabase()

    # Read the default instructions
    content = get_default_instructions_content()
    file_size = len(content.encode("utf-8"))

    logger.info(f"📋 Loaded default.txt ({file_size:,} bytes)")

    # Check if version 1.3 already exists
    existing = (
        supabase.table("system_instruction_versions")
        .select("id")
        .eq("version_number", "1.3")
        .execute()
    )

    if existing.data:
        logger.warning("⚠️ Version 1.3 already exists. Skipping seed.")
        return existing.data[0]["id"]

    # Insert version 1.3
    version_data = {
        "version_number": "1.3",
        "content": content,
        "file_size": file_size,
        "status": "active",
        "is_active": True,
        "version_notes": "Initial version migrated from default.txt. Includes Core Philosophy, Output Format, Operating Modes, Command Shortcuts, Image Generation, and Enhanced Guardrails.",
        "activated_at": "now()",
        "metadata": {
            "migrated_from": "default.txt",
            "migration_script": "039_seed_initial_system_instruction.py",
        },
    }

    result = supabase.table("system_instruction_versions").insert(version_data).execute()

    if not result.data:
        raise Exception("Failed to insert version 1.3")

    version_id = result.data[0]["id"]
    logger.info(f"✅ Created version 1.3 with ID: {version_id}")

    # Bind existing conversations to this version
    if bind_existing_conversations:
        update_result = (
            supabase.table("conversations")
            .update({"system_instruction_version_id": version_id})
            .is_("system_instruction_version_id", "null")
            .execute()
        )

        updated_count = len(update_result.data) if update_result.data else 0
        logger.info(f"✅ Bound {updated_count} existing conversations to version 1.3")

    return version_id


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed the initial system instruction version (1.3)"
    )
    parser.add_argument(
        "--skip-bind",
        action="store_true",
        help="Skip binding existing conversations to version 1.3",
    )
    args = parser.parse_args()

    try:
        version_id = seed_initial_version(bind_existing_conversations=not args.skip_bind)
        print("\n✅ Successfully seeded version 1.3")
        print(f"   Version ID: {version_id}")
        print("\nNext steps:")
        print("1. Verify in database: SELECT * FROM system_instruction_versions;")
        print("2. Test chat to ensure instructions load correctly")

    except Exception as e:
        logger.error(f"❌ Seed failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
