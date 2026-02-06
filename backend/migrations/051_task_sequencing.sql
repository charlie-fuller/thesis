-- Migration 051: Add task sequencing and dependency tracking
-- Enables Taskmaster to create sequenced task plans with dependencies

-- Add sequence number for task ordering within a project
ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS sequence_number INTEGER;

-- Add dependency tracking (array of task IDs that must complete first)
ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS depends_on UUID[];

-- Index for sequence ordering within a project
CREATE INDEX IF NOT EXISTS idx_project_tasks_project_sequence
    ON project_tasks(linked_project_id, sequence_number);
