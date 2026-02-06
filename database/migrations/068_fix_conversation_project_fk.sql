-- Migration: Fix conversations.project_id foreign key to reference ai_projects instead of projects
-- The FK constraint fk_conversations_project was incorrectly bound to a "projects" table
-- instead of "ai_projects". This causes 500 errors when creating project-scoped conversations.

-- Drop the bad constraint (may have different auto-generated names)
ALTER TABLE conversations
  DROP CONSTRAINT IF EXISTS fk_conversations_project;

ALTER TABLE conversations
  DROP CONSTRAINT IF EXISTS conversations_project_id_fkey;

-- Recreate with correct reference to ai_projects
ALTER TABLE conversations
  ADD CONSTRAINT conversations_project_id_fkey
  FOREIGN KEY (project_id) REFERENCES ai_projects(id) ON DELETE SET NULL;
