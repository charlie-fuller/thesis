-- Migration: 050_initiative_document_links.sql
-- Description: Add junction table linking DISCo initiatives to KB documents
-- Date: 2026-01-26
-- Purpose: Enable KB as single source of truth - initiatives reference KB documents instead of storing copies

-- ============================================================================
-- NEW TABLE: disco_initiative_documents (junction table)
-- Links initiatives to KB documents instead of storing document copies
-- ============================================================================

CREATE TABLE IF NOT EXISTS disco_initiative_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id UUID NOT NULL REFERENCES disco_initiatives(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    linked_by UUID REFERENCES auth.users(id),
    notes TEXT,  -- Optional notes about why this doc is relevant
    UNIQUE(initiative_id, document_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_disco_init_docs_initiative ON disco_initiative_documents(initiative_id);
CREATE INDEX IF NOT EXISTS idx_disco_init_docs_document ON disco_initiative_documents(document_id);
CREATE INDEX IF NOT EXISTS idx_disco_init_docs_linked_at ON disco_initiative_documents(linked_at DESC);

-- ============================================================================
-- RLS Policies for disco_initiative_documents
-- ============================================================================

ALTER TABLE disco_initiative_documents ENABLE ROW LEVEL SECURITY;

-- SELECT: User can view links for initiatives they have access to
CREATE POLICY disco_init_docs_select ON disco_initiative_documents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives di
            WHERE di.id = disco_initiative_documents.initiative_id
            AND (
                di.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members dim
                    WHERE dim.initiative_id = di.id
                    AND dim.user_id = auth.uid()
                )
            )
        )
    );

-- INSERT: User can link documents to initiatives they can edit
CREATE POLICY disco_init_docs_insert ON disco_initiative_documents FOR INSERT
    WITH CHECK (
        linked_by = auth.uid()
        AND EXISTS (
            SELECT 1 FROM disco_initiatives di
            WHERE di.id = disco_initiative_documents.initiative_id
            AND (
                di.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members dim
                    WHERE dim.initiative_id = di.id
                    AND dim.user_id = auth.uid()
                    AND dim.role IN ('owner', 'editor')
                )
            )
        )
        -- Also verify user owns the document being linked
        AND EXISTS (
            SELECT 1 FROM documents d
            WHERE d.id = disco_initiative_documents.document_id
            AND d.uploaded_by = auth.uid()
        )
    );

-- DELETE: User can unlink documents from initiatives they can edit
CREATE POLICY disco_init_docs_delete ON disco_initiative_documents FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives di
            WHERE di.id = disco_initiative_documents.initiative_id
            AND (
                di.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members dim
                    WHERE dim.initiative_id = di.id
                    AND dim.user_id = auth.uid()
                    AND dim.role IN ('owner', 'editor')
                )
            )
        )
    );

-- ============================================================================
-- MIGRATION: Move existing disco_documents to KB + create links
-- ============================================================================

-- Note: This migration assumes disco_documents contains initiative-specific docs
-- that need to be migrated to the documents table (KB) and linked via the junction table.
-- The actual data migration should be run manually or via a separate script
-- because it involves file content and may require Voyage embeddings.

-- Add a column to track migration status (for incremental migration)
ALTER TABLE disco_documents
ADD COLUMN IF NOT EXISTS migrated_to_kb BOOLEAN DEFAULT FALSE;

-- Create a helper view to identify documents needing migration
CREATE OR REPLACE VIEW disco_documents_pending_migration AS
SELECT
    dd.id as disco_doc_id,
    dd.initiative_id,
    dd.filename,
    dd.document_type,
    dd.content,
    dd.created_at,
    di.created_by as initiative_owner,
    di.name as initiative_name
FROM disco_documents dd
JOIN disco_initiatives di ON dd.initiative_id = di.id
WHERE dd.migrated_to_kb = FALSE;

COMMENT ON VIEW disco_documents_pending_migration IS
'View showing disco_documents that have not yet been migrated to KB';

-- ============================================================================
-- Add 'initiative' source type to document_tags
-- ============================================================================

-- Update the source column comment to include 'initiative' as a valid source
COMMENT ON COLUMN document_tags.source IS
'Tag source: frontmatter (from Obsidian YAML), manual (user-added in UI), or initiative (auto-added when linked to DISCo initiative)';

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE disco_initiative_documents IS
'Junction table linking DISCo initiatives to KB documents. Enables KB as single source of truth - initiatives reference documents instead of storing copies.';

COMMENT ON COLUMN disco_initiative_documents.notes IS
'Optional notes about why this document is relevant to the initiative';

COMMENT ON COLUMN disco_documents.migrated_to_kb IS
'Flag indicating whether this document has been migrated to the main KB (documents table) and linked via disco_initiative_documents';

-- Trigger PostgREST schema reload
NOTIFY pgrst, 'reload schema';
