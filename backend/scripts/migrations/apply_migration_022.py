#!/usr/bin/env python3
"""Apply Migration 022: Add metadata column to messages table"""

import sys
from pathlib import Path

from supabase import Client, create_client

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.lib.credentials import get_credentials

creds = get_credentials()
SUPABASE_URL = creds["supabase_url"]
SUPABASE_SERVICE_ROLE_KEY = creds["supabase_key"]

backend_dir = Path(__file__).parent

# Initialize Supabase client with service role key (has admin privileges)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Read migration file
migration_file = backend_dir / "migrations" / "022_add_messages_metadata_column.sql"
with open(migration_file, "r") as f:
    migration_sql = f.read()

print("=" * 80)
print("APPLYING MIGRATION 022: Add metadata column to messages table")
print("=" * 80)
print()

try:
    # Execute the migration using Supabase SQL RPC
    # Note: Supabase Python client doesn't have direct SQL execution,
    # so we'll use the REST API to execute SQL via RPC

    print("📋 Executing migration SQL...")
    print()

    # Split migration into individual statements
    statements = migration_sql.split(";")

    for i, statement in enumerate(statements, 1):
        statement = statement.strip()
        if not statement or statement.startswith("--"):
            continue

        print(f"Executing statement {i}...")

        # Execute via Supabase RPC (requires a custom function or direct postgres connection)
        # For now, we'll print instructions for manual execution
        print(f"  {statement[:100]}...")

    print()
    print("=" * 80)
    print("⚠️  MANUAL EXECUTION REQUIRED")
    print("=" * 80)
    print()
    print("The Supabase Python client doesn't support direct SQL execution.")
    print("Please execute this migration manually:")
    print()
    print("OPTION 1: Supabase Dashboard (Recommended)")
    print("-" * 80)
    print(
        f"1. Go to: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}"
    )
    print("2. Click 'SQL Editor' in the left sidebar")
    print("3. Click 'New Query'")
    print("4. Copy the SQL from: backend/migrations/022_add_messages_metadata_column.sql")
    print("5. Paste and click 'Run'")
    print()
    print("OPTION 2: Using psql CLI")
    print("-" * 80)
    print(
        "psql postgresql://postgres:[PASSWORD]@db.quizuqhnapsemfvjublt.supabase.co:5432/postgres \\"
    )
    print("  -f backend/migrations/022_add_messages_metadata_column.sql")
    print()
    print("=" * 80)
    print()

    # Print the migration SQL for easy copying
    print("MIGRATION SQL TO EXECUTE:")
    print("=" * 80)
    print(migration_sql)
    print("=" * 80)

except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
