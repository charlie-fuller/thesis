-- Migration: Project Name and Team Fields
-- Date: 2026-01-21
-- Description: Adds project naming to opportunities and team/opportunity linking to tasks.
--              Enables project-based organization and task filtering by team/project.

-- ============================================================================
-- OPPORTUNITY PROJECT FIELDS
-- ============================================================================

-- Project name for opportunities (required when status moves to scoping/pilot)
ALTER TABLE ai_opportunities ADD COLUMN IF NOT EXISTS project_name VARCHAR(255);
ALTER TABLE ai_opportunities ADD COLUMN IF NOT EXISTS project_description TEXT;

COMMENT ON COLUMN ai_opportunities.project_name IS 'Named project when opportunity moves to scoping/pilot phase';
COMMENT ON COLUMN ai_opportunities.project_description IS 'Optional description of the project scope';

-- ============================================================================
-- TASK TEAM AND OPPORTUNITY LINK
-- ============================================================================

-- Team/department for tasks (enables filtering)
ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS team VARCHAR(100);

-- Direct link to parent opportunity (for project-based task grouping)
-- Note: related_opportunity_id already exists but is for loose associations
-- linked_opportunity_id is for explicit project ownership
ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS linked_opportunity_id UUID REFERENCES ai_opportunities(id) ON DELETE SET NULL;

COMMENT ON COLUMN project_tasks.team IS 'Team or department this task belongs to (e.g., Finance, Legal, IT)';
COMMENT ON COLUMN project_tasks.linked_opportunity_id IS 'Parent opportunity/project this task belongs to';

-- ============================================================================
-- TASK CANDIDATE TEAM FIELD
-- ============================================================================

-- Add suggested_team to task_candidates for extraction
-- Note: team column already exists from migration 029
-- Just adding a comment for clarity
COMMENT ON COLUMN task_candidates.team IS 'Suggested team or department for this task (extracted from context)';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- For filtering tasks by team
CREATE INDEX IF NOT EXISTS idx_project_tasks_team
ON project_tasks(team)
WHERE team IS NOT NULL;

-- For filtering tasks by linked opportunity
CREATE INDEX IF NOT EXISTS idx_project_tasks_linked_opportunity
ON project_tasks(linked_opportunity_id)
WHERE linked_opportunity_id IS NOT NULL;

-- Composite index for client + team filtering
CREATE INDEX IF NOT EXISTS idx_project_tasks_client_team
ON project_tasks(client_id, team);

-- Composite index for client + linked_opportunity filtering
CREATE INDEX IF NOT EXISTS idx_project_tasks_client_linked_opportunity
ON project_tasks(client_id, linked_opportunity_id);

-- For finding opportunities with project names (named projects)
CREATE INDEX IF NOT EXISTS idx_ai_opportunities_project_name
ON ai_opportunities(project_name)
WHERE project_name IS NOT NULL;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Tasks grouped by project/opportunity
CREATE OR REPLACE VIEW v_tasks_by_project AS
SELECT
    t.*,
    o.title as opportunity_title,
    o.project_name,
    o.status as opportunity_status,
    o.tier as opportunity_tier
FROM project_tasks t
LEFT JOIN ai_opportunities o ON t.linked_opportunity_id = o.id;

-- View: Opportunities with task counts
CREATE OR REPLACE VIEW v_opportunities_with_task_counts AS
SELECT
    o.*,
    COUNT(t.id) as total_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'pending') as pending_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'in_progress') as in_progress_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'completed') as completed_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'blocked') as blocked_tasks
FROM ai_opportunities o
LEFT JOIN project_tasks t ON t.linked_opportunity_id = o.id
GROUP BY o.id;

-- ============================================================================
-- DONE!
-- ============================================================================
