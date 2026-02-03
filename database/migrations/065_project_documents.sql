-- Migration: 065_project_documents.sql
-- Description: Add junction table linking projects to KB documents
-- Date: 2026-02-03
-- Purpose: Enable manual document linking to projects (same pattern as DISCo initiatives)

-- ============================================================================
-- NEW TABLE: project_documents (junction table)
-- Links projects to KB documents for reference and context
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES ai_projects(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    linked_by UUID REFERENCES auth.users(id),
    notes TEXT,  -- Optional notes about why this doc is relevant
    UNIQUE(project_id, document_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_project_docs_project ON project_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_project_docs_document ON project_documents(document_id);
CREATE INDEX IF NOT EXISTS idx_project_docs_linked_at ON project_documents(linked_at DESC);

-- ============================================================================
-- RLS Policies for project_documents
-- ============================================================================

ALTER TABLE project_documents ENABLE ROW LEVEL SECURITY;

-- SELECT: User can view links for projects in their client
CREATE POLICY project_docs_select ON project_documents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ai_projects p
            JOIN users u ON u.client_id = p.client_id
            WHERE p.id = project_documents.project_id
            AND u.id = auth.uid()
        )
    );

-- INSERT: User can link documents to projects in their client
CREATE POLICY project_docs_insert ON project_documents FOR INSERT
    WITH CHECK (
        linked_by = auth.uid()
        AND EXISTS (
            SELECT 1 FROM ai_projects p
            JOIN users u ON u.client_id = p.client_id
            WHERE p.id = project_documents.project_id
            AND u.id = auth.uid()
        )
    );

-- DELETE: User can unlink documents from projects in their client
CREATE POLICY project_docs_delete ON project_documents FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM ai_projects p
            JOIN users u ON u.client_id = p.client_id
            WHERE p.id = project_documents.project_id
            AND u.id = auth.uid()
        )
    );

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE project_documents IS
'Junction table linking projects to KB documents. Enables users to manually associate relevant documents with projects.';

COMMENT ON COLUMN project_documents.notes IS
'Optional notes about why this document is relevant to the project';

-- Trigger PostgREST schema reload
NOTIFY pgrst, 'reload schema';
