-- Migration: Document Task Scan Tracking
-- Date: 2026-01-20
-- Description: Adds tracking for whether a document has been scanned for tasks
--              to prevent duplicate task extraction

-- Add column to track when document was scanned for tasks
ALTER TABLE documents ADD COLUMN IF NOT EXISTS tasks_scanned_at TIMESTAMPTZ;

-- Add index for querying unscanned documents
CREATE INDEX IF NOT EXISTS idx_documents_tasks_scanned_at
    ON documents(tasks_scanned_at)
    WHERE tasks_scanned_at IS NULL;

COMMENT ON COLUMN documents.tasks_scanned_at IS 'When this document was last scanned for task extraction (NULL = never scanned)';
