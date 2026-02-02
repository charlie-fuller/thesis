-- Migration: Add initiative_ids to projects
-- Date: 2026-02-02
-- Description: Allows projects to be linked to multiple DISCo initiatives.
--              This enables tracking which initiatives contributed to or are
--              related to a project.

-- ============================================================================
-- ADD INITIATIVE_IDS COLUMN
-- ============================================================================

ALTER TABLE ai_projects
ADD COLUMN IF NOT EXISTS initiative_ids UUID[] DEFAULT '{}';

COMMENT ON COLUMN ai_projects.initiative_ids IS 'Array of DISCo initiative IDs linked to this project';

-- Create index for efficient queries on initiative_ids
CREATE INDEX IF NOT EXISTS idx_ai_projects_initiative_ids ON ai_projects USING GIN (initiative_ids);

-- ============================================================================
-- DONE
-- ============================================================================
