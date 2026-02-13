-- Migration: Add Kraken Agent
-- Date: 2026-02-13
-- Description: Adds the Kraken agent - a task evaluation and autonomous execution
--              specialist that assesses project tasks for "agentic workability",
--              executes approved tasks non-destructively (output as comments + KB docs),
--              and computes an "agenticity" score on the project.
--
-- Category: Task Automation (separate from Taskmaster)

-- ============================================================================
-- ADD AGENTICITY COLUMNS TO PROJECTS
-- ============================================================================

ALTER TABLE ai_projects ADD COLUMN IF NOT EXISTS agenticity_score NUMERIC(5,2) DEFAULT NULL;
ALTER TABLE ai_projects ADD COLUMN IF NOT EXISTS agenticity_evaluated_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE ai_projects ADD COLUMN IF NOT EXISTS agenticity_evaluation JSONB DEFAULT NULL;
-- Stores the full evaluation result: [{task_id, category, confidence, reasoning, proposed_action}]
ALTER TABLE ai_projects ADD COLUMN IF NOT EXISTS agenticity_task_hash TEXT DEFAULT NULL;
-- MD5 hash of task IDs + updated_at timestamps, used to detect staleness

-- ============================================================================
-- INSERT KRAKEN AGENT
-- ============================================================================

INSERT INTO agents (name, display_name, description, is_active, capabilities, config)
VALUES (
    'kraken',
    'Kraken',
    'Task evaluation and autonomous execution specialist. Assesses project tasks for AI workability, executes approved tasks non-destructively via comments and KB documents, and computes agenticity scores to help prioritize work.',
    true,
    ARRAY[
        'task_evaluation',
        'task_execution',
        'agenticity_scoring',
        'kb_document_creation'
    ],
    jsonb_build_object(
        'agent_type', 'task_automation',
        'domain', 'project_tasks',
        'responds_to', ARRAY['evaluate tasks', 'automate', 'agenticity', 'kraken', 'release the kraken', 'which tasks can ai do'],
        'handoffs', ARRAY['taskmaster', 'oracle', 'operator']
    )
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    capabilities = EXCLUDED.capabilities,
    config = agents.config || EXCLUDED.config;

-- ============================================================================
-- INSERT INITIAL INSTRUCTION VERSION
-- ============================================================================

INSERT INTO agent_instruction_versions (
    agent_id,
    version_number,
    instructions,
    description,
    is_active
)
SELECT
    id,
    '1.0',
    '-- Kraken agent instructions loaded from XML file: backend/system_instructions/agents/kraken.xml',
    'Initial Kraken agent creation - task evaluation and autonomous execution specialist',
    true
FROM agents
WHERE name = 'kraken'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- DONE!
-- ============================================================================
