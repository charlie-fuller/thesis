#!/usr/bin/env python3
"""Sync all XML instruction files to the database.

This script reads all XML files from backend/system_instructions/agents/
and creates initial versions in agent_instruction_versions table.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/sync_all_xml_to_db.py
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from services.instruction_loader import list_available_instruction_files, load_instruction_from_file
from supabase import Client, create_client


def main():
    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY in environment")
        return 1

    supabase: Client = create_client(url, key)

    # Get all XML files
    xml_files = list_available_instruction_files()
    print(f"Found {len(xml_files)} XML instruction files\n")

    # Get all agents from database
    try:
        agents_result = supabase.table("agents").select("id, name, display_name").execute()
    except Exception as e:
        print("ERROR: Could not fetch agents table. Have you run the migrations?")
        print(f"Error: {e}")
        return 1

    agents_by_name = {a["name"].lower(): a for a in agents_result.data}
    print(f"Found {len(agents_by_name)} agents in database\n")

    synced = 0
    skipped = 0
    errors = 0

    for xml_file in xml_files:
        agent_name = xml_file["agent_name"].lower()

        if agent_name not in agents_by_name:
            print(f"  SKIP: {agent_name} - No matching agent in database")
            skipped += 1
            continue

        agent = agents_by_name[agent_name]
        agent_id = agent["id"]

        # Load XML content first
        content = load_instruction_from_file(agent_name)
        if not content:
            print(f"  ERROR: {agent_name} - Could not load XML file")
            errors += 1
            continue

        # Check if agent already has an active version
        versions = (
            supabase.table("agent_instruction_versions")
            .select("id, instructions")
            .eq("agent_id", agent_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        if versions.data and len(versions.data) > 0:
            existing = versions.data[0]
            existing_instructions = existing.get("instructions", "")

            # Check if existing is a placeholder (starts with "--" or is very short)
            is_placeholder = existing_instructions.startswith("--") or len(existing_instructions) < 200

            if is_placeholder:
                # Update the placeholder with real XML content
                try:
                    supabase.table("agent_instruction_versions").update(
                        {
                            "instructions": content,
                            "description": "Updated from XML file (replaced placeholder)",
                            "activated_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ).eq("id", existing["id"]).execute()

                    print(f"  ✅ UPDATED: {agent_name} - Replaced placeholder with XML ({len(content)} chars)")
                    synced += 1
                    continue
                except Exception as e:
                    print(f"  ERROR: {agent_name} - {e}")
                    errors += 1
                    continue
            else:
                # Real content already exists
                print(f"  SKIP: {agent_name} - Already has real instructions ({len(existing_instructions)} chars)")
                skipped += 1
                continue

        # No active version exists - create initial version
        try:
            supabase.table("agent_instruction_versions").insert(
                {
                    "agent_id": agent_id,
                    "version_number": "1.0",
                    "instructions": content,
                    "description": "Initial version from XML file",
                    "is_active": True,
                    "activated_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()

            # Update agent timestamp
            supabase.table("agents").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq(
                "id", agent_id
            ).execute()

            print(f"  ✅ SYNCED: {agent_name} - Created version 1.0 ({len(content)} chars)")
            synced += 1

        except Exception as e:
            print(f"  ERROR: {agent_name} - {e}")
            errors += 1

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Synced:  {synced}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
