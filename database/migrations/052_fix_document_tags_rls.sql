-- Migration: Fix document_tags RLS policies
-- Description: RLS policies incorrectly referenced 'user_id' instead of 'uploaded_by'
-- Date: 2026-01-27

-- Drop existing incorrect policies
DROP POLICY IF EXISTS document_tags_select ON document_tags;
DROP POLICY IF EXISTS document_tags_insert ON document_tags;
DROP POLICY IF EXISTS document_tags_update ON document_tags;
DROP POLICY IF EXISTS document_tags_delete ON document_tags;

-- Recreate policies with correct column name (uploaded_by instead of user_id)
CREATE POLICY document_tags_select ON document_tags FOR SELECT
    USING (document_id IN (SELECT id FROM documents WHERE uploaded_by = auth.uid()));

CREATE POLICY document_tags_insert ON document_tags FOR INSERT
    WITH CHECK (document_id IN (SELECT id FROM documents WHERE uploaded_by = auth.uid()));

CREATE POLICY document_tags_update ON document_tags FOR UPDATE
    USING (document_id IN (SELECT id FROM documents WHERE uploaded_by = auth.uid()));

CREATE POLICY document_tags_delete ON document_tags FOR DELETE
    USING (document_id IN (SELECT id FROM documents WHERE uploaded_by = auth.uid()));

COMMENT ON TABLE document_tags IS 'Document tags from Obsidian frontmatter or manually added by users (RLS fixed 2026-01-27)';
