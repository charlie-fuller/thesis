#!/usr/bin/env python3
"""Apply Migration 022: Add metadata column to messages table
Uses direct PostgreSQL connection via psycopg2
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ ERROR: psycopg2 is not installed")
    print("Install it with: pip install psycopg2-binary")
    sys.exit(1)

# Load environment variables
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
load_dotenv(env_path)

# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    print("❌ ERROR: Missing SUPABASE_URL in .env file")
    sys.exit(1)

# Extract project ref from Supabase URL
# Format: https://quizuqhnapsemfvjublt.supabase.co
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")

# Build PostgreSQL connection string
# Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
print("=" * 80)
print("APPLYING MIGRATION 022: Add metadata column to messages table")
print("=" * 80)
print()
print(f"Project: {project_ref}")
print()

# Read migration file
migration_file = backend_dir / "migrations" / "022_add_messages_metadata_column.sql"
with open(migration_file, "r") as f:
    migration_sql = f.read()

print("⚠️  Database Password Required")
print("-" * 80)
print("This migration requires a direct PostgreSQL connection.")
print("You need the database password from your Supabase project settings.")
print()
print("To find your password:")
print("1. Go to: https://supabase.com/dashboard/project/" + project_ref)
print("2. Click 'Settings' → 'Database'")
print("3. Find 'Connection string' → 'URI' section")
print("4. Copy the password from the connection string")
print()

db_password = input("Enter database password (or press Enter to see SQL): ").strip()

if not db_password:
    print()
    print("=" * 80)
    print("MIGRATION SQL TO EXECUTE MANUALLY:")
    print("=" * 80)
    print()
    print("Execute this in Supabase SQL Editor:")
    print(f"Dashboard: https://supabase.com/dashboard/project/{project_ref}/sql")
    print()
    print(migration_sql)
    print()
    print("=" * 80)
    sys.exit(0)

# Connect to database
conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"

try:
    print()
    print("📡 Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = False  # Use transaction
    cursor = conn.cursor()

    print("✅ Connected successfully!")
    print()
    print("📋 Executing migration...")
    print()

    # Execute the migration
    cursor.execute(migration_sql)

    print("✅ Migration SQL executed successfully!")
    print()
    print("💾 Committing transaction...")

    conn.commit()

    print("✅ Transaction committed!")
    print()

    # Verify the column was added
    print("🔍 Verifying metadata column...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'messages'
          AND column_name = 'metadata';
    """)

    result = cursor.fetchone()
    if result:
        print("✅ Metadata column verified:")
        print(f"   - Column: {result[0]}")
        print(f"   - Type: {result[1]}")
        print(f"   - Nullable: {result[2]}")
    else:
        print("⚠️  WARNING: Could not verify metadata column")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("✅ MIGRATION 022 COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Restart your backend server")
    print("2. Test image generation feature")
    print()

except psycopg2.Error as e:
    print(f"❌ DATABASE ERROR: {e}")
    if conn:
        conn.rollback()
        print("🔄 Transaction rolled back")
    sys.exit(1)

except Exception as e:
    print(f"❌ ERROR: {e}")
    if conn:
        conn.rollback()
    sys.exit(1)
