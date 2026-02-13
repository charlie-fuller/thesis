-- Migration: 074_initiative_folder_links
-- Description: Add folder-level subscriptions for DISCO initiatives.
-- When a folder is linked to an initiative, new documents synced into that folder
-- are automatically linked to the initiative.
-- Date: 2026-02-13

-- Junction table: which folders each initiative watches
CREATE TABLE IF NOT EXISTS disco_initiative_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id UUID NOT NULL REFERENCES disco_initiatives(id) ON DELETE CASCADE,
    folder_path TEXT NOT NULL,
    recursive BOOLEAN NOT NULL DEFAULT TRUE,
    linked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    linked_by UUID REFERENCES auth.users(id),
    UNIQUE(initiative_id, folder_path)
);

-- Index for folder path lookups during sync
CREATE INDEX IF NOT EXISTS idx_disco_initiative_folders_path
    ON disco_initiative_folders(folder_path);

-- Index for initiative lookups
CREATE INDEX IF NOT EXISTS idx_disco_initiative_folders_initiative
    ON disco_initiative_folders(initiative_id);

-- RLS policies (matching disco_initiative_documents pattern)
ALTER TABLE disco_initiative_folders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view initiative folders they have access to"
    ON disco_initiative_folders FOR SELECT
    USING (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Editors can manage initiative folders"
    ON disco_initiative_folders FOR ALL
    USING (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members
            WHERE user_id = auth.uid()
            AND role IN ('owner', 'editor')
        )
    );

-- Add comment
COMMENT ON TABLE disco_initiative_folders IS 'Folder subscriptions for DISCO initiatives. New documents synced into linked folders are auto-linked to the initiative.';
COMMENT ON COLUMN disco_initiative_folders.recursive IS 'When true, documents in subfolders are also auto-linked';

-- Notify PostgREST to reload schema cache
SELECT pg_notify('pgrst', 'reload schema');
