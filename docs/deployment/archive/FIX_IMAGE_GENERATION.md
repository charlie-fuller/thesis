# Fix Image Generation Feature

## Problem
Image generation is not working because the `messages` table is missing the `metadata` column, which is required to store image suggestion data.

**Error:** `Could not find the 'metadata' column of 'messages' in the schema cache`

## Solution
Apply Migration 022 to add the `metadata` column to the `messages` table.

---

## Option 1: Supabase Dashboard (Easiest)

1. **Open Supabase SQL Editor:**
   - Go to: https://supabase.com/dashboard/project/quizuqhnapsemfvjublt
   - Click **"SQL Editor"** in the left sidebar
   - Click **"New Query"**

2. **Copy and paste this SQL:**

```sql
-- Migration 022: Add metadata column to messages table
-- Date: 2025-12-14
-- Purpose: Add JSONB metadata column to messages table for image suggestions

ALTER TABLE public.messages
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT NULL;

COMMENT ON COLUMN public.messages.metadata IS 'JSON metadata for message (e.g., image_suggestion, has_image, image_id)';

-- Index for querying messages with image suggestions
CREATE INDEX IF NOT EXISTS idx_messages_metadata_image_suggestion
ON public.messages
USING GIN ((metadata->'image_suggestion'))
WHERE metadata->'image_suggestion' IS NOT NULL;

-- Force PostgREST to reload schema cache
NOTIFY pgrst, 'reload schema';

-- Verify the metadata column was added
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'messages'
  AND column_name = 'metadata';
```

3. **Click "Run"** (or press `Ctrl+Enter` / `Cmd+Enter`)

4. **Verify:** You should see output showing the `metadata` column with type `jsonb`

5. **Restart your backend** (if running locally or on Railway)

---

## Option 2: Python Script (Automated)

### Prerequisites
```bash
cd backend
pip install psycopg2-binary
```

### Run the migration script
```bash
python apply_migration_022_psql.py
```

You'll be prompted for your database password. You can find it in:
- Supabase Dashboard → Settings → Database → Connection String

---

## Option 3: psql CLI (Advanced)

If you have PostgreSQL CLI tools installed:

```bash
psql postgresql://postgres:[YOUR_PASSWORD]@db.quizuqhnapsemfvjublt.supabase.co:5432/postgres \
  -f backend/migrations/022_add_messages_metadata_column.sql
```

Replace `[YOUR_PASSWORD]` with your database password from Supabase Settings.

---

## Verification

After applying the migration, verify it worked:

### In Supabase Dashboard:
1. Go to: Table Editor → messages
2. You should see a new column called `metadata` of type `jsonb`

### Test Image Generation:
1. Open your Thesis app: http://localhost:3000 (or your production URL)
2. Start a new conversation
3. Ask: **"generate an image of a dog catching a frisbee"**
4. You should see:
   - Thesis generates the image immediately
   - The image appears in the chat
   - No JSON error messages

---

## What This Migration Does

1.  Adds `metadata` JSONB column to `messages` table
2.  Creates GIN index for fast JSON queries on image suggestions
3.  Forces PostgREST to reload schema cache (fixes the 404 error)
4.  Verifies the column was created successfully

---

## Why Was This Needed?

The image generation feature stores metadata about image suggestions in the `metadata` column:

```json
{
  "image_suggestion": {
    "suggested_prompt": "A happy dog catching a frisbee",
    "reason": "This concept would be clearer with a visual"
  }
}
```

Without this column, the backend cannot save image suggestions, causing the feature to fail silently.

---

## Next Steps After Migration

1. **Restart your backend server** (Railway will auto-restart if deployed)
2. **Test image generation** with a simple request
3. **Monitor logs** for any remaining errors

---

## Troubleshooting

### Still seeing metadata errors?
- Make sure PostgREST reloaded its schema cache (the `NOTIFY pgrst, 'reload schema';` command)
- Restart your backend server
- Check Railway logs: `railway logs --tail`

### Image generation still not working?
- Check backend logs for errors
- Verify your `.env` has `GOOGLE_GENERATIVE_AI_API_KEY`
- Test the `/api/images/generate` endpoint directly

### Need help?
- Check backend logs: `cd backend && tail -f thesis.log`
- Check browser console for frontend errors
- Review the full migration file: `backend/migrations/022_add_messages_metadata_column.sql`
