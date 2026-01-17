-- Migration: Document Tags
-- Description: Add document_tags table for storing tags from Obsidian frontmatter and manual user tags
-- Date: 2026-01-17

-- Document tags table (supports both Obsidian frontmatter and manual tags)
CREATE TABLE IF NOT EXISTS document_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',  -- 'frontmatter', 'manual'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, tag)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_document_tags_tag ON document_tags(tag);
CREATE INDEX IF NOT EXISTS idx_document_tags_source ON document_tags(source);

-- Enable RLS
ALTER TABLE document_tags ENABLE ROW LEVEL SECURITY;

-- RLS policies: users can only access tags for their own documents
CREATE POLICY document_tags_select ON document_tags FOR SELECT
    USING (document_id IN (SELECT id FROM documents WHERE user_id = auth.uid()));

CREATE POLICY document_tags_insert ON document_tags FOR INSERT
    WITH CHECK (document_id IN (SELECT id FROM documents WHERE user_id = auth.uid()));

CREATE POLICY document_tags_update ON document_tags FOR UPDATE
    USING (document_id IN (SELECT id FROM documents WHERE user_id = auth.uid()));

CREATE POLICY document_tags_delete ON document_tags FOR DELETE
    USING (document_id IN (SELECT id FROM documents WHERE user_id = auth.uid()));

-- Comment on table
COMMENT ON TABLE document_tags IS 'Document tags from Obsidian frontmatter or manually added by users';
COMMENT ON COLUMN document_tags.source IS 'Tag source: frontmatter (from Obsidian YAML) or manual (user-added in UI)';
