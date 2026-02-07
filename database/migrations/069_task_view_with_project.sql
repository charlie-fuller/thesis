-- Migration 069: Update v_tasks_with_assignee to include linked project info
-- This allows the Kanban board to display project details on task cards

CREATE OR REPLACE VIEW v_tasks_with_assignee AS
SELECT
    t.*,
    s.name as stakeholder_name,
    s.email as stakeholder_email,
    s.department as stakeholder_department,
    u.email as user_email,
    COALESCE(t.assignee_name, s.name, u.email) as display_assignee,
    p.project_code as project_code,
    p.title as project_title,
    p.department as project_department
FROM project_tasks t
LEFT JOIN stakeholders s ON t.assignee_stakeholder_id = s.id
LEFT JOIN users u ON t.assignee_user_id = u.id
LEFT JOIN ai_projects p ON t.linked_project_id = p.id;
