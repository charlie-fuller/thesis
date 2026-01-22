-- Migration: Task Candidates Opportunity Link
-- Date: 2026-01-22
-- Description: Adds opportunity linking to task_candidates for Taskmaster-created tasks.
--              When Taskmaster extracts tasks from opportunity/project context,
--              they are linked to the source opportunity for filtering and context.

-- ============================================================================
-- ADD OPPORTUNITY LINK COLUMNS
-- ============================================================================

-- Link to the opportunity this task candidate was created for
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS linked_opportunity_id UUID REFERENCES ai_opportunities(id) ON DELETE SET NULL;

-- Source opportunity (which opportunity spawned this candidate)
-- Slightly different semantics: linked = where task belongs, source = where discovered
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS source_opportunity_id UUID REFERENCES ai_opportunities(id) ON DELETE SET NULL;

COMMENT ON COLUMN task_candidates.linked_opportunity_id IS 'Opportunity/project this task should be linked to when accepted';
COMMENT ON COLUMN task_candidates.source_opportunity_id IS 'Opportunity where this task was discovered (e.g., via Taskmaster chat)';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- For finding candidates linked to a specific opportunity
CREATE INDEX IF NOT EXISTS idx_task_candidates_linked_opportunity
ON task_candidates(linked_opportunity_id)
WHERE linked_opportunity_id IS NOT NULL;

-- For finding candidates from a specific opportunity source
CREATE INDEX IF NOT EXISTS idx_task_candidates_source_opportunity
ON task_candidates(source_opportunity_id)
WHERE source_opportunity_id IS NOT NULL;

-- ============================================================================
-- UPDATE ACCEPT BEHAVIOR (via function)
-- ============================================================================

-- Function to auto-set linked_opportunity_id when accepting task candidates
-- This ensures tasks created from candidates inherit the opportunity link
CREATE OR REPLACE FUNCTION copy_opportunity_link_on_task_accept()
RETURNS TRIGGER AS $$
BEGIN
    -- When a task_candidate is accepted, copy linked_opportunity_id to the task
    IF NEW.status = 'accepted' AND OLD.status = 'pending' THEN
        -- Update the created task with the linked_opportunity_id if it exists
        IF NEW.created_task_id IS NOT NULL AND NEW.linked_opportunity_id IS NOT NULL THEN
            UPDATE project_tasks
            SET linked_opportunity_id = NEW.linked_opportunity_id
            WHERE id = NEW.created_task_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists, then create
DROP TRIGGER IF EXISTS trigger_copy_opportunity_link ON task_candidates;
CREATE TRIGGER trigger_copy_opportunity_link
    AFTER UPDATE ON task_candidates
    FOR EACH ROW
    EXECUTE FUNCTION copy_opportunity_link_on_task_accept();

-- ============================================================================
-- DONE!
-- ============================================================================
