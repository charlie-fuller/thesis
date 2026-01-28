-- Migration: 054_performance_indexes.sql
-- Description: Add missing indexes for batch chunk fetches and user document queries
-- Date: 2026-01-27

-- ============================================================================
-- Index for batch chunk fetches by document_id
-- ============================================================================
-- This index speeds up queries like:
--   SELECT * FROM document_chunks WHERE document_id IN (uuid1, uuid2, ...)
-- Used by get_documents_by_tags and get_documents_by_folder endpoints

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
    ON document_chunks(document_id);

-- ============================================================================
-- Compound index for user's documents sorted by date
-- ============================================================================
-- This index speeds up queries like:
--   SELECT * FROM documents WHERE uploaded_by = user_id ORDER BY uploaded_at DESC
-- Used by get_all_tags, search_documents, and many listing endpoints

CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by_at
    ON documents(uploaded_by, uploaded_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON INDEX idx_document_chunks_document_id IS
'Index for batch fetching chunks by document_id. Improves performance of by-tags and by-folder queries.';

COMMENT ON INDEX idx_documents_uploaded_by_at IS
'Compound index for listing user documents sorted by upload date. Improves performance of document listing endpoints.';

-- Trigger PostgREST schema reload
NOTIFY pgrst, 'reload schema';
