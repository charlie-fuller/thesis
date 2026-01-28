-- Migration: 053_document_tags_cache.sql
-- Description: Add denormalized tags_cache column for fast filtering
-- Date: 2026-01-27

-- ============================================================================
-- Add tags_cache JSONB column to documents table
-- ============================================================================

ALTER TABLE documents
ADD COLUMN IF NOT EXISTS tags_cache JSONB DEFAULT '[]'::jsonb;

-- GIN index for fast containment queries (e.g., WHERE tags_cache @> '["ashley"]')
CREATE INDEX IF NOT EXISTS idx_documents_tags_cache_gin
ON documents USING GIN (tags_cache);

-- ============================================================================
-- Function to sync tags_cache when document_tags changes
-- ============================================================================

CREATE OR REPLACE FUNCTION sync_document_tags_cache()
RETURNS TRIGGER AS $$
DECLARE
    target_doc_id UUID;
BEGIN
    -- Determine which document_id was affected
    IF TG_OP = 'DELETE' THEN
        target_doc_id := OLD.document_id;
    ELSE
        target_doc_id := NEW.document_id;
    END IF;

    -- Update the tags_cache for this document
    UPDATE documents
    SET tags_cache = COALESCE(
        (SELECT jsonb_agg(DISTINCT tag ORDER BY tag)
         FROM document_tags
         WHERE document_id = target_doc_id),
        '[]'::jsonb
    )
    WHERE id = target_doc_id;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers to keep tags_cache in sync
-- ============================================================================

DROP TRIGGER IF EXISTS trg_sync_tags_cache_insert ON document_tags;
CREATE TRIGGER trg_sync_tags_cache_insert
    AFTER INSERT ON document_tags
    FOR EACH ROW
    EXECUTE FUNCTION sync_document_tags_cache();

DROP TRIGGER IF EXISTS trg_sync_tags_cache_update ON document_tags;
CREATE TRIGGER trg_sync_tags_cache_update
    AFTER UPDATE ON document_tags
    FOR EACH ROW
    EXECUTE FUNCTION sync_document_tags_cache();

DROP TRIGGER IF EXISTS trg_sync_tags_cache_delete ON document_tags;
CREATE TRIGGER trg_sync_tags_cache_delete
    AFTER DELETE ON document_tags
    FOR EACH ROW
    EXECUTE FUNCTION sync_document_tags_cache();

-- ============================================================================
-- Backfill existing tags into tags_cache
-- ============================================================================

UPDATE documents d
SET tags_cache = COALESCE(
    (SELECT jsonb_agg(DISTINCT dt.tag ORDER BY dt.tag)
     FROM document_tags dt
     WHERE dt.document_id = d.id),
    '[]'::jsonb
);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON COLUMN documents.tags_cache IS
'Denormalized JSONB array of tags for fast filtering. Kept in sync via triggers on document_tags table.';

-- Trigger PostgREST schema reload
NOTIFY pgrst, 'reload schema';
