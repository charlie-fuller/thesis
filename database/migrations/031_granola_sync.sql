-- Migration: Granola Sync Support
-- Date: 2026-01-21
-- Description: Adds columns to track Granola meeting syncing and extraction

-- ============================================================================
-- GRANOLA TRACKING COLUMNS ON DOCUMENTS
-- ============================================================================

-- Unique Granola ID from frontmatter
ALTER TABLE documents ADD COLUMN IF NOT EXISTS granola_id TEXT;

-- When structured data (opportunities, tasks, stakeholders) was last extracted
ALTER TABLE documents ADD COLUMN IF NOT EXISTS granola_scanned_at TIMESTAMPTZ;

-- Add document_type if not exists (for filtering meeting summaries vs other docs)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_type VARCHAR(50);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- For checking if a Granola meeting has been processed
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_granola_id
ON documents(granola_id)
WHERE granola_id IS NOT NULL;

-- For finding unprocessed Granola documents
CREATE INDEX IF NOT EXISTS idx_documents_granola_unscanned
ON documents(granola_scanned_at)
WHERE source_platform = 'granola' AND granola_scanned_at IS NULL;

-- For filtering by document type
CREATE INDEX IF NOT EXISTS idx_documents_document_type
ON documents(document_type)
WHERE document_type IS NOT NULL;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN documents.granola_id IS 'Unique ID from Granola frontmatter for deduplication';
COMMENT ON COLUMN documents.granola_scanned_at IS 'When structured data was extracted from this Granola meeting';
COMMENT ON COLUMN documents.document_type IS 'Type of document: meeting_summary, transcript, report, policy, etc.';

-- ============================================================================
-- ADD SOURCE_DOCUMENT_ID TO PROJECT_TASKS (if not exists)
-- ============================================================================
-- Allows linking tasks to KB documents (not just transcripts)

ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_project_tasks_source_document
ON project_tasks(source_document_id)
WHERE source_document_id IS NOT NULL;

COMMENT ON COLUMN project_tasks.source_document_id IS 'Source KB document if task was extracted from a document';

-- ============================================================================
-- DONE!
-- ============================================================================
