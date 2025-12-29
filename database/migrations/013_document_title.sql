-- Migration 013: Add title column to documents table
-- Allows storing a display title separate from the unique filename

-- Add title column (nullable for backwards compatibility with existing documents)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS title TEXT;

-- For existing documents, default title to filename without extension and UUID suffix
-- This is a one-time backfill
UPDATE documents
SET title = REGEXP_REPLACE(
    REGEXP_REPLACE(filename, '\.[^.]+$', ''),  -- Remove extension
    '_[a-f0-9]{8}$', ''  -- Remove UUID suffix
)
WHERE title IS NULL;

-- Add comment
COMMENT ON COLUMN documents.title IS 'Display title for the document (user-provided or derived from filename)';
