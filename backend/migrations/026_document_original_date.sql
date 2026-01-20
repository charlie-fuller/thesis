-- ============================================================================
-- MIGRATION: Add original_date to documents
-- Description: Tracks the actual date of the document content (e.g., meeting date
--              for transcripts) separately from upload/sync timestamps
-- Author: Claude
-- Date: 2026-01-20
-- ============================================================================

-- Add original_date column to documents table
-- This represents when the content was created (e.g., meeting date), not upload date
ALTER TABLE documents ADD COLUMN IF NOT EXISTS original_date DATE;

-- Add index for querying by original date (common for "recent meetings" queries)
CREATE INDEX IF NOT EXISTS idx_documents_original_date ON documents(original_date DESC NULLS LAST);

-- Add comment explaining the column purpose
COMMENT ON COLUMN documents.original_date IS 'The actual date of the document content (e.g., meeting date for transcripts). Distinct from uploaded_at which tracks when it was added to the system.';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- After running this migration:
-- 1. Existing documents will have NULL original_date
-- 2. Update document upload flow to capture original_date when available
-- 3. For transcripts, parse the date from filename or content if possible
-- 4. Users can manually set original_date via document info modal
