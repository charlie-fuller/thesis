# Database Migrations

This directory contains SQL migration files for the help system.

## Files

1. **add_help_system.sql** - Core help system tables and indexes
2. **add_help_feedback.sql** - User feedback functionality

## Running Migrations

### Using psql

```bash
# Set your database URL
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Run migrations in order
psql $DATABASE_URL -f add_help_system.sql
psql $DATABASE_URL -f add_help_feedback.sql
```

### Using Supabase CLI

```bash
supabase db push --db-url $DATABASE_URL < add_help_system.sql
supabase db push --db-url $DATABASE_URL < add_help_feedback.sql
```

### From Application Code

```python
from helpers.supabase_helpers import get_supabase_admin_client

supabase = get_supabase_admin_client()

# Read and execute migration
with open('database/migrations/add_help_system.sql', 'r') as f:
    migration_sql = f.read()
    supabase.postgrest.rpc('exec_sql', {'sql': migration_sql}).execute()
```

## What Gets Created

### Tables

- **help_documents** - Stores full documentation files
- **help_chunks** - Searchable chunks with embeddings
- **help_conversations** - User conversation history
- **help_messages** - Individual messages in conversations

### Indexes

- IVFFlat vector index on `help_chunks.embedding` for fast similarity search
- B-tree indexes on foreign keys and commonly queried columns
- GIN indexes on `role_access` arrays for role-based filtering

### Functions

- **match_help_chunks()** - RPC function for vector similarity search

### Row Level Security

- Admins can see all help content
- Users see only content appropriate for their role
- Users can only access their own conversations

## Verifying Installation

```sql
-- Check tables exist
SELECT tablename FROM pg_tables
WHERE schemaname = 'public' AND tablename LIKE 'help_%';

-- Check indexes created
SELECT indexname FROM pg_indexes
WHERE tablename LIKE 'help_%';

-- Test vector search function exists
SELECT proname FROM pg_proc
WHERE proname = 'match_help_chunks';

-- Check RLS policies
SELECT tablename, policyname FROM pg_policies
WHERE tablename LIKE 'help_%';
```

## Rollback (if needed)

To remove all help system tables:

```sql
DROP TABLE IF EXISTS help_messages CASCADE;
DROP TABLE IF EXISTS help_conversations CASCADE;
DROP TABLE IF EXISTS help_chunks CASCADE;
DROP TABLE IF EXISTS help_documents CASCADE;
DROP FUNCTION IF EXISTS match_help_chunks CASCADE;
```

## Requirements

- PostgreSQL 12 or higher
- pgvector extension installed

To install pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

On Supabase, pgvector is already installed and enabled.

## Migration Notes

- Run migrations in order (core system first, then feedback)
- Migrations are idempotent (safe to run multiple times)
- No data loss if re-running on existing tables
- Indexes may take time on large datasets

## Troubleshooting

**Error: "extension vector does not exist"**
```sql
CREATE EXTENSION vector;
```

**Error: "permission denied"**
- Ensure you're using a superuser account or service role key
- On Supabase, use `SUPABASE_SERVICE_ROLE_KEY` not anon key

**Error: "relation help_documents already exists"**
- This is safe - migration uses `IF NOT EXISTS` clauses
- Existing data will be preserved

**Slow index creation**
- IVFFlat index creation can take time on large datasets
- Consider creating index after data load:
  ```sql
  -- Load data first
  -- Then create index
  CREATE INDEX help_chunks_embedding_idx ...
  ```
