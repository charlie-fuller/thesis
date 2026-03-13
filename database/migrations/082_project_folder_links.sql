-- Migration: 082_project_folder_links
-- Description: Add folder-level subscriptions for projects (mirroring disco_initiative_folders).
-- When a folder is linked to a project, new documents synced into that folder
-- are automatically linked to the project.
-- Date: 2026-03-13

-- Junction table: which folders each project watches
CREATE TABLE IF NOT EXISTS project_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES ai_projects(id) ON DELETE CASCADE,
    folder_path TEXT NOT NULL,
    recursive BOOLEAN NOT NULL DEFAULT TRUE,
    linked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    linked_by UUID REFERENCES auth.users(id),
    UNIQUE(project_id, folder_path)
);

-- Index for folder path lookups during sync
CREATE INDEX IF NOT EXISTS idx_project_folders_path
    ON project_folders(folder_path);

-- Index for project lookups
CREATE INDEX IF NOT EXISTS idx_project_folders_project
    ON project_folders(project_id);

-- RLS policies
ALTER TABLE project_folders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to project folders"
    ON project_folders FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Authenticated users can view project folders"
    ON project_folders FOR SELECT
    USING (auth.role() = 'authenticated');

-- Add comment
COMMENT ON TABLE project_folders IS 'Folder subscriptions for projects. New documents synced into linked folders are auto-linked to the project.';
COMMENT ON COLUMN project_folders.recursive IS 'When true, documents in subfolders are also auto-linked';

-- Notify PostgREST to reload schema cache
SELECT pg_notify('pgrst', 'reload schema');
