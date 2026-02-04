#!/usr/bin/env python3
"""Sync all XML instruction files to the database using direct PostgreSQL connection.

This bypasses the Supabase REST API schema cache issue.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/sync_all_xml_to_db_direct.py
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import psycopg2
from psycopg2.extras import RealDictCursor

from services.instruction_loader import list_available_instruction_files, load_instruction_from_file


def get_postgres_url():
    """Get PostgreSQL connection URL from environment."""
    # First try explicit DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # Try SUPABASE_DB_PASSWORD with project ref
    supabase_url = os.getenv("SUPABASE_URL")
    password = os.getenv("SUPABASE_DB_PASSWORD")

    if supabase_url and password:
        import re

        match = re.search(r"https://([^.]+)\.supabase\.co", supabase_url)
        if match:
            project_ref = match.group(1)
            return f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

    return None


def main():
    # Try direct PostgreSQL connection first
    postgres_url = get_postgres_url()

    if not postgres_url:
        print("=" * 60)
        print("Direct PostgreSQL connection not available.")
        print("")
        print("To use this script, add SUPABASE_DB_PASSWORD to your .env file.")
        print("You can find it in Supabase Dashboard -> Settings -> Database")
        print("-> Connection string -> Copy password")
        print("=" * 60)
        print("")
        print("Alternatively, wait for Supabase schema cache to refresh,")
        print("then run: python scripts/sync_all_xml_to_db.py")
        return 1

    try:
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("Connected to PostgreSQL directly!")
    except Exception as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        return 1

    # Get all XML files
    xml_files = list_available_instruction_files()
    print(f"Found {len(xml_files)} XML instruction files\n")

    # Get all agents from database
    try:
        cursor.execute("SELECT id, name, display_name FROM agents")
        agents = cursor.fetchall()
    except Exception as e:
        print(f"ERROR: Could not fetch agents table: {e}")
        conn.close()
        return 1

    agents_by_name = {a["name"].lower(): a for a in agents}
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
        cursor.execute(
            """
            SELECT id, instructions FROM agent_instruction_versions
            WHERE agent_id = %s AND is_active = TRUE
            LIMIT 1
        """,
            (agent_id,),
        )
        existing = cursor.fetchone()

        if existing:
            existing_instructions = existing.get("instructions", "")

            # Check if existing is a placeholder (starts with "--" or is very short)
            is_placeholder = existing_instructions.startswith("--") or len(existing_instructions) < 200

            if is_placeholder:
                # Update the placeholder with real XML content
                try:
                    cursor.execute(
                        """
                        UPDATE agent_instruction_versions
                        SET instructions = %s,
                            description = 'Updated from XML file (replaced placeholder)',
                            activated_at = %s
                        WHERE id = %s
                    """,
                        (content, datetime.now(timezone.utc), existing["id"]),
                    )
                    conn.commit()

                    print(f"  ✅ UPDATED: {agent_name} - Replaced placeholder with XML ({len(content)} chars)")
                    synced += 1
                    continue
                except Exception as e:
                    print(f"  ERROR: {agent_name} - {e}")
                    conn.rollback()
                    errors += 1
                    continue
            else:
                # Real content already exists
                print(f"  SKIP: {agent_name} - Already has real instructions ({len(existing_instructions)} chars)")
                skipped += 1
                continue

        # No active version exists - create initial version
        try:
            cursor.execute(
                """
                INSERT INTO agent_instruction_versions
                (agent_id, version_number, instructions, description, is_active, activated_at)
                VALUES (%s, '1.0', %s, 'Initial version from XML file', TRUE, %s)
            """,
                (agent_id, content, datetime.now(timezone.utc)),
            )

            cursor.execute(
                """
                UPDATE agents SET updated_at = %s WHERE id = %s
            """,
                (datetime.now(timezone.utc), agent_id),
            )

            conn.commit()

            print(f"  ✅ SYNCED: {agent_name} - Created version 1.0 ({len(content)} chars)")
            synced += 1

        except Exception as e:
            print(f"  ERROR: {agent_name} - {e}")
            conn.rollback()
            errors += 1

    conn.close()

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Synced:  {synced}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
