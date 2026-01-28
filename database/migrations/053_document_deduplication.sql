-- Migration: Document Deduplication
-- Date: 2026-01-27
-- Description: Adds unique constraint on documents(user_id, obsidian_file_path) to prevent
--              duplicate documents from being created during sync. Also cleans up existing
--              duplicates by keeping the most recently updated version.

-- ============================================================================
-- STEP 1: Find and log duplicates (for audit purposes)
-- ============================================================================

-- Create a temp table to track what we're merging
CREATE TEMP TABLE IF NOT EXISTS duplicate_docs_audit AS
SELECT
    user_id,
    obsidian_file_path,
    COUNT(*) as duplicate_count,
    array_agg(id ORDER BY updated_at DESC) as doc_ids,
    array_agg(updated_at ORDER BY updated_at DESC) as updated_times
FROM documents
WHERE obsidian_file_path IS NOT NULL
GROUP BY user_id, obsidian_file_path
HAVING COUNT(*) > 1;

-- Log the duplicates found (visible in migration output)
DO $$
DECLARE
    dup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO dup_count FROM duplicate_docs_audit;
    RAISE NOTICE 'Found % sets of duplicate documents to merge', dup_count;
END $$;

-- ============================================================================
-- STEP 2: Update obsidian_sync_state to point to the kept document
-- ============================================================================

-- For each set of duplicates, update sync state to point to the newest doc
UPDATE obsidian_sync_state oss
SET document_id = (
    SELECT (array_agg(d.id ORDER BY d.updated_at DESC))[1]
    FROM documents d
    WHERE d.user_id = (
        SELECT user_id FROM obsidian_vault_configs WHERE id = oss.config_id
    )
    AND d.obsidian_file_path = oss.file_path
    AND d.obsidian_file_path IS NOT NULL
)
WHERE EXISTS (
    SELECT 1 FROM duplicate_docs_audit da
    WHERE da.obsidian_file_path = oss.file_path
);

-- ============================================================================
-- STEP 3: Delete duplicate documents (keep the newest one per path)
-- ============================================================================

-- Delete all but the newest document for each (user_id, obsidian_file_path) pair
DELETE FROM documents d
WHERE obsidian_file_path IS NOT NULL
AND id NOT IN (
    -- Keep only the newest document for each unique path
    SELECT DISTINCT ON (user_id, obsidian_file_path) id
    FROM documents
    WHERE obsidian_file_path IS NOT NULL
    ORDER BY user_id, obsidian_file_path, updated_at DESC
);

-- Log how many were deleted
DO $$
DECLARE
    deleted_count INTEGER;
BEGIN
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % duplicate documents', deleted_count;
END $$;

-- ============================================================================
-- STEP 4: Add unique constraint to prevent future duplicates
-- ============================================================================

-- Add a partial unique index (only for non-null obsidian_file_path)
-- This allows multiple documents with NULL obsidian_file_path (non-Obsidian docs)
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_unique_obsidian_path
    ON documents(user_id, obsidian_file_path)
    WHERE obsidian_file_path IS NOT NULL;

COMMENT ON INDEX idx_documents_unique_obsidian_path IS
    'Prevents duplicate documents from the same Obsidian file path per user';

-- ============================================================================
-- STEP 5: Clean up temp table
-- ============================================================================

DROP TABLE IF EXISTS duplicate_docs_audit;

-- ============================================================================
-- DONE!
-- ============================================================================
