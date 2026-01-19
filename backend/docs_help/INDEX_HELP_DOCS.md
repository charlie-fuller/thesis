# Indexing Help Documentation

The help docs need to be indexed with embeddings for the help chat system to find them.

---

## Prerequisites

You need these environment variables set in `/backend/.env`:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (for elevated permissions)
- `VOYAGE_API_KEY` - Voyage AI API key (for creating embeddings)

Note: If you're using dotenvx for encrypted secrets, your `.env.vault` already has these encrypted. Run `dotenvx run` to inject them.

---

## Running the Indexer

**Option 1: With dotenvx (encrypted vault)**

```bash
cd backend
dotenvx run -- python scripts/index_help_docs.py --force
```

**Option 2: With plain .env file**

```bash
cd backend
source .venv/bin/activate
python scripts/index_help_docs.py --force
```

**Option 3: On Railway (Production)**

The indexer can be triggered via the reindex webhook endpoint (requires `HELP_REINDEX_API_KEY`):

```bash
curl -X POST https://thesis-production.up.railway.app/api/help/reindex \
  -H "X-Reindex-Key: $HELP_REINDEX_API_KEY"
```

The `--force` flag reindexes all documents even if they exist.

---

## What It Does

1. Scans `/docs/help/` for markdown files (13 documents currently)
2. Extracts sections based on headings
3. Chunks content (1000 chars with 200 char overlap)
4. Creates embeddings via Voyage AI (`voyage-3` model, 1024 dimensions)
5. Stores in `help_documents` and `help_chunks` tables
6. Tags with role access based on directory:
   - `/admin/` → admin only
   - `/user/` → user only
   - `/system/` → both admin and user

---

## After Indexing

Verify in database:
- `help_documents` table should have 13 entries (one per markdown file)
- `help_chunks` table should have embedded chunks with vectors

The help chat system uses these embeddings for RAG retrieval. When users ask questions, the system:
1. Creates an embedding of their question
2. Finds similar chunks via vector search
3. Includes relevant chunks in the AI prompt

---

## Reindexing

Run with `--force` whenever help docs change:

```bash
python scripts/index_help_docs.py --force
```

This clears ALL existing data and recreates everything fresh, ensuring embeddings match current content.

---

## Database Tables

```sql
-- help_documents: One row per markdown file
-- Columns: id, title, file_path, category, content, word_count, role_access

-- help_chunks: Embedded chunks from each document
-- Columns: id, document_id, content, embedding (vector), chunk_index, heading_context, role_access, metadata
```

---

## Troubleshooting

**Missing VOYAGE_API_KEY error:**
The Voyage AI key is required for embeddings. Check your `.env` or use dotenvx to decrypt `.env.vault`.

**Help docs path not found:**
The indexer looks for help docs in multiple locations:
1. `/backend/docs_help/` (committed in repo, used on Railway)
2. `/docs/help/` (repo root, used locally)

**Database errors:**
Ensure migrations 033, 034, 036, 038 have been run for the help system tables.
