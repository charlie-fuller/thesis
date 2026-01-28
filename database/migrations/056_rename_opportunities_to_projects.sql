-- Migration: Rename Opportunities to Projects
-- Date: 2026-01-28
-- Description: Renames "opportunities" terminology to "projects" throughout the database.
--              This is part of a codebase-wide refactoring to better reflect that these
--              entities represent multi-step strategic initiatives (projects) rather than
--              just potential opportunities.
--
-- Tables Renamed:
--   - ai_opportunities -> ai_projects
--   - opportunity_candidates -> project_candidates
--   - opportunity_stakeholder_link -> project_stakeholder_link
--   - opportunity_conversations -> project_conversations
--
-- Columns Renamed:
--   - opportunity_code -> project_code
--   - opportunity_summary -> project_summary (if exists)
--   - matched_opportunity_id -> matched_project_id
--   - created_opportunity_id -> created_project_id
--   - linked_opportunity_id -> linked_project_id
--   - related_opportunity_id -> related_project_id
--   - source_opportunity_id -> source_project_id

-- ============================================================================
-- PRE-MIGRATION: Drop dependent views
-- ============================================================================

DROP VIEW IF EXISTS v_opportunities_with_owner CASCADE;
DROP VIEW IF EXISTS v_opportunities_with_task_counts CASCADE;
DROP VIEW IF EXISTS v_tasks_with_opportunity CASCADE;

-- ============================================================================
-- TABLE RENAMES
-- ============================================================================

ALTER TABLE IF EXISTS ai_opportunities RENAME TO ai_projects;
ALTER TABLE IF EXISTS opportunity_candidates RENAME TO project_candidates;
ALTER TABLE IF EXISTS opportunity_stakeholder_link RENAME TO project_stakeholder_link;
ALTER TABLE IF EXISTS opportunity_conversations RENAME TO project_conversations;

-- ============================================================================
-- COLUMN RENAMES - ai_projects
-- ============================================================================

ALTER TABLE ai_projects RENAME COLUMN opportunity_code TO project_code;

-- Check and rename opportunity_summary if it exists (may have been added later)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'ai_projects' AND column_name = 'opportunity_summary') THEN
        ALTER TABLE ai_projects RENAME COLUMN opportunity_summary TO project_summary;
    END IF;
END $$;

-- ============================================================================
-- COLUMN RENAMES - project_candidates
-- ============================================================================

ALTER TABLE project_candidates RENAME COLUMN matched_opportunity_id TO matched_project_id;
ALTER TABLE project_candidates RENAME COLUMN created_opportunity_id TO created_project_id;

-- ============================================================================
-- COLUMN RENAMES - project_stakeholder_link
-- ============================================================================

ALTER TABLE project_stakeholder_link RENAME COLUMN opportunity_id TO project_id;

-- ============================================================================
-- COLUMN RENAMES - project_conversations
-- ============================================================================

ALTER TABLE project_conversations RENAME COLUMN opportunity_id TO project_id;

-- ============================================================================
-- COLUMN RENAMES - project_tasks (already named project_tasks)
-- ============================================================================

ALTER TABLE project_tasks RENAME COLUMN linked_opportunity_id TO linked_project_id;
ALTER TABLE project_tasks RENAME COLUMN related_opportunity_id TO related_project_id;
ALTER TABLE project_tasks RENAME COLUMN source_opportunity_id TO source_project_id;

-- ============================================================================
-- COLUMN RENAMES - task_candidates
-- ============================================================================

ALTER TABLE task_candidates RENAME COLUMN linked_opportunity_id TO linked_project_id;
ALTER TABLE task_candidates RENAME COLUMN source_opportunity_id TO source_project_id;

-- Add linked_project_candidate_id for linking tasks to project candidates during extraction
-- When both task and project candidates are accepted, this enables automatic linking
ALTER TABLE task_candidates ADD COLUMN IF NOT EXISTS linked_project_candidate_id UUID REFERENCES project_candidates(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_task_candidates_linked_project_candidate ON task_candidates(linked_project_candidate_id);
COMMENT ON COLUMN task_candidates.linked_project_candidate_id IS 'Project candidate this task is linked to (for automatic linking when accepted)';

-- ============================================================================
-- COLUMN RENAMES - stakeholder_candidates (related_opportunity_ids array)
-- ============================================================================

ALTER TABLE stakeholder_candidates RENAME COLUMN related_opportunity_ids TO related_project_ids;

-- ============================================================================
-- COLUMN RENAMES - documents (opportunities_scanned_at)
-- ============================================================================

ALTER TABLE documents RENAME COLUMN opportunities_scanned_at TO projects_scanned_at;

-- ============================================================================
-- UPDATE UNIQUE CONSTRAINTS
-- ============================================================================

-- Drop old constraint and create new one with updated name
ALTER TABLE ai_projects DROP CONSTRAINT IF EXISTS ai_opportunities_client_id_opportunity_code_key;
ALTER TABLE ai_projects ADD CONSTRAINT ai_projects_client_id_project_code_key UNIQUE (client_id, project_code);

-- ============================================================================
-- UPDATE COMMENTS
-- ============================================================================

COMMENT ON TABLE ai_projects IS 'AI implementation projects with 4-dimension scoring and auto-tiering';
COMMENT ON COLUMN ai_projects.project_code IS 'Short identifier like F01 (Finance #1), L02 (Legal #2)';

COMMENT ON TABLE project_candidates IS 'Potential AI projects extracted from meeting documents, pending user review';
COMMENT ON COLUMN project_candidates.matched_project_id IS 'Existing project this might be a duplicate of';

COMMENT ON TABLE project_stakeholder_link IS 'Links stakeholders to projects with role designation';
COMMENT ON COLUMN project_stakeholder_link.project_id IS 'Project this stakeholder is linked to';

COMMENT ON TABLE project_conversations IS 'Q&A history for projects - stores user questions and AI responses';

COMMENT ON COLUMN project_tasks.linked_project_id IS 'Parent project this task belongs to';
COMMENT ON COLUMN project_tasks.related_project_id IS 'Loosely related project (for context)';
COMMENT ON COLUMN project_tasks.source_project_id IS 'Project where this task was discovered';

COMMENT ON COLUMN task_candidates.linked_project_id IS 'Project this task should be linked to when accepted';
COMMENT ON COLUMN task_candidates.source_project_id IS 'Project where this task was discovered (e.g., via Taskmaster chat)';

COMMENT ON COLUMN documents.projects_scanned_at IS 'When this document was last scanned for project extraction (NULL = never scanned)';

-- ============================================================================
-- RECREATE VIEWS WITH NEW TABLE/COLUMN NAMES
-- ============================================================================

-- View: Projects with owner name joined
CREATE OR REPLACE VIEW v_projects_with_owner AS
SELECT
    p.*,
    s.name as owner_name,
    s.email as owner_email,
    s.department as owner_department
FROM ai_projects p
LEFT JOIN stakeholders s ON p.owner_stakeholder_id = s.id;

-- View: Projects with task counts
CREATE OR REPLACE VIEW v_projects_with_task_counts AS
SELECT
    p.*,
    COUNT(t.id) as task_count,
    COUNT(t.id) FILTER (WHERE t.status = 'completed') as completed_task_count,
    COUNT(t.id) FILTER (WHERE t.status = 'in_progress') as in_progress_task_count,
    COUNT(t.id) FILTER (WHERE t.status = 'pending') as pending_task_count,
    COUNT(t.id) FILTER (WHERE t.status = 'blocked') as blocked_task_count
FROM ai_projects p
LEFT JOIN project_tasks t ON t.linked_project_id = p.id
GROUP BY p.id;

-- View: Tasks with project details
CREATE OR REPLACE VIEW v_tasks_with_project AS
SELECT
    t.*,
    p.title as project_title,
    p.project_code,
    p.status as project_status
FROM project_tasks t
LEFT JOIN ai_projects p ON t.linked_project_id = p.id;

-- ============================================================================
-- UPDATE RLS POLICIES - ai_projects
-- ============================================================================

-- Drop old policies with "opportunity" naming
DROP POLICY IF EXISTS "Users can view opportunities in their client" ON ai_projects;
DROP POLICY IF EXISTS "Users can manage opportunities in their client" ON ai_projects;
DROP POLICY IF EXISTS "Service role has full access to ai_opportunities" ON ai_projects;

-- Create new policies with "project" naming
CREATE POLICY "Users can view projects in their client" ON ai_projects
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can manage projects in their client" ON ai_projects
    FOR ALL USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Service role has full access to ai_projects" ON ai_projects
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- UPDATE RLS POLICIES - project_candidates
-- ============================================================================

DROP POLICY IF EXISTS "Users can view opportunity candidates in their client" ON project_candidates;
DROP POLICY IF EXISTS "Users can update opportunity candidates in their client" ON project_candidates;
DROP POLICY IF EXISTS "Service role can insert opportunity candidates" ON project_candidates;
DROP POLICY IF EXISTS "Service role can delete opportunity candidates" ON project_candidates;

CREATE POLICY "Users can view project candidates in their client" ON project_candidates
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can update project candidates in their client" ON project_candidates
    FOR UPDATE USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Service role can insert project candidates" ON project_candidates
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can delete project candidates" ON project_candidates
    FOR DELETE USING (true);

-- ============================================================================
-- UPDATE RLS POLICIES - project_stakeholder_link
-- ============================================================================

DROP POLICY IF EXISTS "Users can view links via opportunity access" ON project_stakeholder_link;
DROP POLICY IF EXISTS "Users can manage links via opportunity access" ON project_stakeholder_link;
DROP POLICY IF EXISTS "Service role has full access to opportunity_stakeholder_link" ON project_stakeholder_link;

CREATE POLICY "Users can view project stakeholder links" ON project_stakeholder_link
    FOR SELECT USING (
        project_id IN (
            SELECT id FROM ai_projects
            WHERE client_id IN (
                SELECT client_id FROM users WHERE id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can manage project stakeholder links" ON project_stakeholder_link
    FOR ALL USING (
        project_id IN (
            SELECT id FROM ai_projects
            WHERE client_id IN (
                SELECT client_id FROM users WHERE id = auth.uid()
            )
        )
    );

CREATE POLICY "Service role has full access to project_stakeholder_link" ON project_stakeholder_link
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- UPDATE RLS POLICIES - project_conversations
-- ============================================================================

DROP POLICY IF EXISTS "Users can view conversations in their client" ON project_conversations;
DROP POLICY IF EXISTS "Users can create conversations in their client" ON project_conversations;
DROP POLICY IF EXISTS "Service role has full access to opportunity_conversations" ON project_conversations;

CREATE POLICY "Users can view project conversations in their client" ON project_conversations
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can create project conversations in their client" ON project_conversations
    FOR INSERT WITH CHECK (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Service role has full access to project_conversations" ON project_conversations
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- UPDATE TRIGGER FUNCTIONS
-- ============================================================================

-- Update the opportunity timestamp function name
DROP FUNCTION IF EXISTS update_opportunity_timestamp() CASCADE;

CREATE OR REPLACE FUNCTION update_project_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_opportunity_timestamp ON ai_projects;
CREATE TRIGGER trigger_update_project_timestamp
BEFORE UPDATE ON ai_projects
FOR EACH ROW
EXECUTE FUNCTION update_project_timestamp();

-- Update the opportunity candidate timestamp function name
DROP FUNCTION IF EXISTS update_opportunity_candidate_timestamp() CASCADE;

CREATE OR REPLACE FUNCTION update_project_candidate_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_opportunity_candidate_timestamp ON project_candidates;
CREATE TRIGGER trigger_update_project_candidate_timestamp
BEFORE UPDATE ON project_candidates
FOR EACH ROW
EXECUTE FUNCTION update_project_candidate_timestamp();

-- Update the copy_opportunity_link_on_task_accept function
DROP FUNCTION IF EXISTS copy_opportunity_link_on_task_accept() CASCADE;

CREATE OR REPLACE FUNCTION copy_project_link_on_task_accept()
RETURNS TRIGGER AS $$
BEGIN
    -- When a task_candidate is accepted, copy linked_project_id to the task
    IF NEW.status = 'accepted' AND OLD.status = 'pending' THEN
        -- Update the created task with the linked_project_id if it exists
        IF NEW.created_task_id IS NOT NULL AND NEW.linked_project_id IS NOT NULL THEN
            UPDATE project_tasks
            SET linked_project_id = NEW.linked_project_id
            WHERE id = NEW.created_task_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_copy_opportunity_link ON task_candidates;
CREATE TRIGGER trigger_copy_project_link
    AFTER UPDATE ON task_candidates
    FOR EACH ROW
    EXECUTE FUNCTION copy_project_link_on_task_accept();

-- ============================================================================
-- RENAME INDEXES (optional, for clarity)
-- ============================================================================

-- ai_projects indexes
ALTER INDEX IF EXISTS idx_ai_opportunities_client_id RENAME TO idx_ai_projects_client_id;
ALTER INDEX IF EXISTS idx_ai_opportunities_code RENAME TO idx_ai_projects_code;
ALTER INDEX IF EXISTS idx_ai_opportunities_department RENAME TO idx_ai_projects_department;
ALTER INDEX IF EXISTS idx_ai_opportunities_tier RENAME TO idx_ai_projects_tier;
ALTER INDEX IF EXISTS idx_ai_opportunities_status RENAME TO idx_ai_projects_status;
ALTER INDEX IF EXISTS idx_ai_opportunities_owner RENAME TO idx_ai_projects_owner;
ALTER INDEX IF EXISTS idx_ai_opportunities_client_tier_status RENAME TO idx_ai_projects_client_tier_status;
ALTER INDEX IF EXISTS idx_ai_opportunities_scoring_confidence RENAME TO idx_ai_projects_scoring_confidence;

-- project_candidates indexes
ALTER INDEX IF EXISTS idx_opportunity_candidates_pending RENAME TO idx_project_candidates_pending;
ALTER INDEX IF EXISTS idx_opportunity_candidates_document RENAME TO idx_project_candidates_document;
ALTER INDEX IF EXISTS idx_opportunity_candidates_status_date RENAME TO idx_project_candidates_status_date;
ALTER INDEX IF EXISTS idx_opportunity_candidates_match RENAME TO idx_project_candidates_match;

-- project_stakeholder_link indexes
ALTER INDEX IF EXISTS idx_opp_stakeholder_link_opportunity RENAME TO idx_project_stakeholder_link_project;
ALTER INDEX IF EXISTS idx_opp_stakeholder_link_stakeholder RENAME TO idx_project_stakeholder_link_stakeholder;
ALTER INDEX IF EXISTS idx_opp_stakeholder_link_role RENAME TO idx_project_stakeholder_link_role;

-- project_conversations indexes
ALTER INDEX IF EXISTS idx_opp_conversations_opportunity_id RENAME TO idx_project_conversations_project_id;
ALTER INDEX IF EXISTS idx_opp_conversations_client_id RENAME TO idx_project_conversations_client_id;
ALTER INDEX IF EXISTS idx_opp_conversations_user_id RENAME TO idx_project_conversations_user_id;
ALTER INDEX IF EXISTS idx_opp_conversations_created_at RENAME TO idx_project_conversations_created_at;
ALTER INDEX IF EXISTS idx_opp_conversations_opp_created RENAME TO idx_project_conversations_project_created;

-- project_tasks indexes (linked_opportunity -> linked_project)
ALTER INDEX IF EXISTS idx_project_tasks_linked_opportunity RENAME TO idx_project_tasks_linked_project;
ALTER INDEX IF EXISTS idx_project_tasks_client_linked_opportunity RENAME TO idx_project_tasks_client_linked_project;

-- task_candidates indexes
ALTER INDEX IF EXISTS idx_task_candidates_linked_opportunity RENAME TO idx_task_candidates_linked_project;
ALTER INDEX IF EXISTS idx_task_candidates_source_opportunity RENAME TO idx_task_candidates_source_project;

-- documents index
ALTER INDEX IF EXISTS idx_documents_opportunities_scanned_at RENAME TO idx_documents_projects_scanned_at;

-- ============================================================================
-- VERIFICATION QUERY (run manually to verify migration)
-- ============================================================================

-- SELECT 'ai_projects' as tbl, COUNT(*) FROM ai_projects
-- UNION ALL SELECT 'project_candidates', COUNT(*) FROM project_candidates
-- UNION ALL SELECT 'project_stakeholder_link', COUNT(*) FROM project_stakeholder_link
-- UNION ALL SELECT 'project_conversations', COUNT(*) FROM project_conversations
-- UNION ALL SELECT 'project_tasks', COUNT(*) FROM project_tasks;

-- ============================================================================
-- DONE!
-- ============================================================================
