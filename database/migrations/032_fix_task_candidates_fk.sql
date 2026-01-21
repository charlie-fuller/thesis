-- Migration: Fix task_candidates foreign key constraint
-- Date: 2026-01-21
-- Description: Add ON DELETE SET NULL to created_task_id foreign key
--              so tasks can be deleted without constraint violations.

-- Drop the existing foreign key constraint
ALTER TABLE task_candidates
DROP CONSTRAINT IF EXISTS task_candidates_created_task_id_fkey;

-- Recreate with ON DELETE SET NULL
ALTER TABLE task_candidates
ADD CONSTRAINT task_candidates_created_task_id_fkey
FOREIGN KEY (created_task_id)
REFERENCES project_tasks(id)
ON DELETE SET NULL;

-- ============================================================================
-- DONE!
-- ============================================================================
