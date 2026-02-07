-- Migration 070: Add notes column to project_tasks
-- Provides a free-text notes field for additional context on tasks

ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS notes TEXT;
