-- Migration: Task Management System
-- Date: 2026-01-15
-- Description: Adds Kanban-style task management with multi-source extraction
--              from transcripts, conversations, research, and manual entry.
--
-- New Tables:
--   - project_tasks: Core task table with Kanban status, assignment, source tracking
--   - task_comments: Comment threads on tasks
--   - task_history: Audit trail for status/assignee/priority changes
--
-- New Views:
--   - v_tasks_with_assignee: Tasks joined with assignee details
--   - v_task_counts_by_status: Task counts per status per client

-- ============================================================================
-- PROJECT TASKS TABLE
-- ============================================================================
-- Primary task tracking with Kanban status workflow
-- Sources: transcript action_items, conversations, research tasks, manual entry

CREATE TABLE IF NOT EXISTS project_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Task Content
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Kanban Status (VARCHAR for flexibility, not enum)
    -- Values: pending, in_progress, blocked, completed
    status VARCHAR(50) DEFAULT 'pending',

    -- Priority (1-5 scale, 5 = highest priority)
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),

    -- Assignment (flexible: stakeholder, user, or just name string)
    assignee_stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
    assignee_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assignee_name VARCHAR(255),  -- Denormalized for display when no FK match

    -- Dates
    due_date DATE,
    completed_at TIMESTAMPTZ,

    -- Source Tracking (polymorphic references)
    -- Values: transcript, conversation, research, opportunity, manual
    source_type VARCHAR(50),
    source_transcript_id UUID REFERENCES meeting_transcripts(id) ON DELETE SET NULL,
    source_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    source_research_task_id UUID REFERENCES research_tasks(id) ON DELETE SET NULL,
    source_opportunity_id UUID REFERENCES ai_opportunities(id) ON DELETE SET NULL,

    -- Original text from source (for deduplication matching)
    source_text TEXT,
    source_extracted_at TIMESTAMPTZ,

    -- Task Categorization
    category VARCHAR(100),  -- meeting_action, research_followup, stakeholder_task, etc.
    tags TEXT[],

    -- Related Entities
    related_stakeholder_ids UUID[],  -- Stakeholders mentioned/involved
    related_opportunity_id UUID REFERENCES ai_opportunities(id) ON DELETE SET NULL,

    -- Blocker Details (when status = 'blocked')
    blocker_reason TEXT,
    blocked_at TIMESTAMPTZ,

    -- User Tracking
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Position for manual ordering within status columns
    position INTEGER DEFAULT 0
);

COMMENT ON TABLE project_tasks IS 'Kanban-style task management with multi-source extraction';
COMMENT ON COLUMN project_tasks.status IS 'Kanban status: pending, in_progress, blocked, completed';
COMMENT ON COLUMN project_tasks.priority IS 'Priority 1-5 (5=highest): 1=low, 2=medium-low, 3=medium, 4=high, 5=critical';
COMMENT ON COLUMN project_tasks.source_type IS 'Origin: transcript, conversation, research, opportunity, manual';
COMMENT ON COLUMN project_tasks.source_text IS 'Original extracted text for deduplication matching';
COMMENT ON COLUMN project_tasks.position IS 'Sort order within status column for Kanban board';

-- ============================================================================
-- TASK COMMENTS TABLE
-- ============================================================================
-- Discussion thread on tasks

CREATE TABLE IF NOT EXISTS task_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    content TEXT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE task_comments IS 'Discussion thread on tasks';

-- ============================================================================
-- TASK HISTORY TABLE
-- ============================================================================
-- Audit trail for task modifications

CREATE TABLE IF NOT EXISTS task_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Change Details
    field_name VARCHAR(100) NOT NULL,  -- status, assignee, priority, due_date, etc.
    old_value TEXT,
    new_value TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE task_history IS 'Audit trail for task modifications';
COMMENT ON COLUMN task_history.field_name IS 'Field that changed: status, priority, assignee_stakeholder_id, due_date, etc.';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Primary query patterns
CREATE INDEX IF NOT EXISTS idx_project_tasks_client_id
    ON project_tasks(client_id);

CREATE INDEX IF NOT EXISTS idx_project_tasks_status
    ON project_tasks(status);

CREATE INDEX IF NOT EXISTS idx_project_tasks_assignee_stakeholder
    ON project_tasks(assignee_stakeholder_id);

CREATE INDEX IF NOT EXISTS idx_project_tasks_assignee_user
    ON project_tasks(assignee_user_id);

CREATE INDEX IF NOT EXISTS idx_project_tasks_due_date
    ON project_tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_project_tasks_priority
    ON project_tasks(priority);

-- Composite index for Kanban queries (client + status)
CREATE INDEX IF NOT EXISTS idx_project_tasks_client_status
    ON project_tasks(client_id, status);

-- Composite index for filtering (client + status + due_date)
CREATE INDEX IF NOT EXISTS idx_project_tasks_client_status_due
    ON project_tasks(client_id, status, due_date);

-- Composite index for Kanban ordering (client + status + position)
CREATE INDEX IF NOT EXISTS idx_project_tasks_client_status_position
    ON project_tasks(client_id, status, position);

-- Source deduplication indexes
CREATE INDEX IF NOT EXISTS idx_project_tasks_source_transcript
    ON project_tasks(source_transcript_id)
    WHERE source_transcript_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_project_tasks_source_conversation
    ON project_tasks(source_conversation_id)
    WHERE source_conversation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_project_tasks_source_research
    ON project_tasks(source_research_task_id)
    WHERE source_research_task_id IS NOT NULL;

-- Task comments indexes
CREATE INDEX IF NOT EXISTS idx_task_comments_task_id
    ON task_comments(task_id);

CREATE INDEX IF NOT EXISTS idx_task_comments_user_id
    ON task_comments(user_id);

-- Task history indexes
CREATE INDEX IF NOT EXISTS idx_task_history_task_id
    ON task_history(task_id);

CREATE INDEX IF NOT EXISTS idx_task_history_created_at
    ON task_history(created_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Project Tasks RLS
ALTER TABLE project_tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view tasks in their client" ON project_tasks;
CREATE POLICY "Users can view tasks in their client" ON project_tasks
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can manage tasks in their client" ON project_tasks;
CREATE POLICY "Users can manage tasks in their client" ON project_tasks
    FOR ALL USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Service role has full access to project_tasks" ON project_tasks;
CREATE POLICY "Service role has full access to project_tasks" ON project_tasks
    FOR ALL USING (auth.role() = 'service_role');

-- Task Comments RLS
ALTER TABLE task_comments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view comments on accessible tasks" ON task_comments;
CREATE POLICY "Users can view comments on accessible tasks" ON task_comments
    FOR SELECT USING (
        task_id IN (
            SELECT id FROM project_tasks
            WHERE client_id IN (
                SELECT client_id FROM users WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Users can manage comments on accessible tasks" ON task_comments;
CREATE POLICY "Users can manage comments on accessible tasks" ON task_comments
    FOR ALL USING (
        task_id IN (
            SELECT id FROM project_tasks
            WHERE client_id IN (
                SELECT client_id FROM users WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Service role has full access to task_comments" ON task_comments;
CREATE POLICY "Service role has full access to task_comments" ON task_comments
    FOR ALL USING (auth.role() = 'service_role');

-- Task History RLS
ALTER TABLE task_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view history on accessible tasks" ON task_history;
CREATE POLICY "Users can view history on accessible tasks" ON task_history
    FOR SELECT USING (
        task_id IN (
            SELECT id FROM project_tasks
            WHERE client_id IN (
                SELECT client_id FROM users WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Service role has full access to task_history" ON task_history;
CREATE POLICY "Service role has full access to task_history" ON task_history
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp on project_tasks
CREATE OR REPLACE FUNCTION update_project_task_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_project_task_timestamp ON project_tasks;
CREATE TRIGGER trigger_update_project_task_timestamp
BEFORE UPDATE ON project_tasks
FOR EACH ROW
EXECUTE FUNCTION update_project_task_timestamp();

-- Auto-update updated_at timestamp on task_comments
CREATE OR REPLACE FUNCTION update_task_comment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_task_comment_timestamp ON task_comments;
CREATE TRIGGER trigger_update_task_comment_timestamp
BEFORE UPDATE ON task_comments
FOR EACH ROW
EXECUTE FUNCTION update_task_comment_timestamp();

-- Record task history and auto-set timestamps on status changes
CREATE OR REPLACE FUNCTION record_task_history()
RETURNS TRIGGER AS $$
BEGIN
    -- Status change
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO task_history (task_id, user_id, field_name, old_value, new_value)
        VALUES (NEW.id, NEW.updated_by, 'status', OLD.status, NEW.status);

        -- Set completed_at when moving to completed
        IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
            NEW.completed_at = NOW();
        END IF;

        -- Clear completed_at when moving away from completed
        IF NEW.status != 'completed' AND OLD.status = 'completed' THEN
            NEW.completed_at = NULL;
        END IF;

        -- Set blocked_at when moving to blocked
        IF NEW.status = 'blocked' AND OLD.status != 'blocked' THEN
            NEW.blocked_at = NOW();
        END IF;

        -- Clear blocked_at when moving away from blocked
        IF NEW.status != 'blocked' AND OLD.status = 'blocked' THEN
            NEW.blocked_at = NULL;
        END IF;
    END IF;

    -- Priority change
    IF OLD.priority IS DISTINCT FROM NEW.priority THEN
        INSERT INTO task_history (task_id, user_id, field_name, old_value, new_value)
        VALUES (NEW.id, NEW.updated_by, 'priority', OLD.priority::TEXT, NEW.priority::TEXT);
    END IF;

    -- Assignee stakeholder change
    IF OLD.assignee_stakeholder_id IS DISTINCT FROM NEW.assignee_stakeholder_id THEN
        INSERT INTO task_history (task_id, user_id, field_name, old_value, new_value)
        VALUES (NEW.id, NEW.updated_by, 'assignee_stakeholder_id',
                OLD.assignee_stakeholder_id::TEXT, NEW.assignee_stakeholder_id::TEXT);
    END IF;

    -- Assignee user change
    IF OLD.assignee_user_id IS DISTINCT FROM NEW.assignee_user_id THEN
        INSERT INTO task_history (task_id, user_id, field_name, old_value, new_value)
        VALUES (NEW.id, NEW.updated_by, 'assignee_user_id',
                OLD.assignee_user_id::TEXT, NEW.assignee_user_id::TEXT);
    END IF;

    -- Due date change
    IF OLD.due_date IS DISTINCT FROM NEW.due_date THEN
        INSERT INTO task_history (task_id, user_id, field_name, old_value, new_value)
        VALUES (NEW.id, NEW.updated_by, 'due_date', OLD.due_date::TEXT, NEW.due_date::TEXT);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_record_task_history ON project_tasks;
CREATE TRIGGER trigger_record_task_history
BEFORE UPDATE ON project_tasks
FOR EACH ROW
EXECUTE FUNCTION record_task_history();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Tasks with assignee details resolved
CREATE OR REPLACE VIEW v_tasks_with_assignee AS
SELECT
    t.*,
    s.name as stakeholder_name,
    s.email as stakeholder_email,
    s.department as stakeholder_department,
    u.email as user_email,
    COALESCE(t.assignee_name, s.name, u.email) as display_assignee
FROM project_tasks t
LEFT JOIN stakeholders s ON t.assignee_stakeholder_id = s.id
LEFT JOIN users u ON t.assignee_user_id = u.id;

-- View: Task counts by status per client (for dashboard)
CREATE OR REPLACE VIEW v_task_counts_by_status AS
SELECT
    client_id,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
    COUNT(*) FILTER (WHERE status = 'blocked') as blocked_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) as total_count,
    COUNT(*) FILTER (WHERE due_date < CURRENT_DATE AND status NOT IN ('completed')) as overdue_count
FROM project_tasks
GROUP BY client_id;

-- ============================================================================
-- DONE!
-- ============================================================================
