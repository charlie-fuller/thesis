-- Migration: Simplify Project Statuses
-- Date: 2026-02-03
-- Description: Consolidates 7 project statuses into 4 simpler ones:
--   - backlog: Identified but not started (was: identified)
--   - active: Currently being worked on (was: scoping, pilot, scaling)
--   - completed: Successfully implemented (was: deployed)
--   - archived: Dropped/no longer relevant (was: paused, archived, blocked)

-- ============================================================================
-- MIGRATE EXISTING STATUS VALUES
-- ============================================================================

-- Map old statuses to new ones
UPDATE ai_projects SET status = 'backlog' WHERE status = 'identified';
UPDATE ai_projects SET status = 'active' WHERE status IN ('scoping', 'pilot', 'scaling');
UPDATE ai_projects SET status = 'completed' WHERE status = 'deployed';
UPDATE ai_projects SET status = 'archived' WHERE status IN ('paused', 'blocked', 'archived');

-- Also update any project_candidates that have status fields
UPDATE project_candidates SET status = 'backlog' WHERE status = 'identified';
UPDATE project_candidates SET status = 'active' WHERE status IN ('scoping', 'pilot', 'scaling');
UPDATE project_candidates SET status = 'completed' WHERE status = 'deployed';
UPDATE project_candidates SET status = 'archived' WHERE status IN ('paused', 'blocked', 'archived');

-- ============================================================================
-- ADD CHECK CONSTRAINT (optional - enforces valid values)
-- ============================================================================

-- Drop existing constraint if any
ALTER TABLE ai_projects DROP CONSTRAINT IF EXISTS ai_projects_status_check;

-- Add new constraint
ALTER TABLE ai_projects ADD CONSTRAINT ai_projects_status_check
  CHECK (status IN ('backlog', 'active', 'completed', 'archived'));

-- ============================================================================
-- UPDATE DEFAULT VALUE
-- ============================================================================

ALTER TABLE ai_projects ALTER COLUMN status SET DEFAULT 'backlog';

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN ai_projects.status IS 'Project status: backlog (not started), active (in progress), completed (done), archived (dropped)';
