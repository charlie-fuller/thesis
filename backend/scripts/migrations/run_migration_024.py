#!/usr/bin/env python3
"""Apply migration 024: System Instruction Document Mappings"""

import sys
from pathlib import Path

from supabase import create_client

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.lib.credentials import get_credentials

creds = get_credentials()
SUPABASE_URL = creds["supabase_url"]
SUPABASE_SERVICE_ROLE_KEY = creds["supabase_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Read migration file
migration_file = "migrations/024_system_instruction_document_mappings.sql"
with open(migration_file, "r") as f:
    sql = f.read()

print(f"📊 Applying migration: {migration_file}")
print(f"🔗 Database: {SUPABASE_URL}")
print("=" * 80)

try:
    # Check if table already exists
    check_result = (
        supabase.table("system_instruction_document_mappings").select("id").limit(1).execute()
    )
    print("✅ Table 'system_instruction_document_mappings' already exists!")
    print("   Migration may have been applied already.")
except Exception as e:
    print("ℹ️  Table doesn't exist yet, proceeding with migration...")
    print(f"   Error was: {str(e)}")

    print("\n⚠️  Please apply this migration manually in Supabase SQL Editor:")
    print(f"\n{sql}\n")
    print("=" * 80)
    print("\nSteps:")
    print("1. Go to Supabase Dashboard > SQL Editor")
    print("2. Paste the SQL above")
    print("3. Click 'Run'")
    print("4. Verify the table was created")
