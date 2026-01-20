-- Migration: Add Taskmaster Agent
-- Date: 2026-01-20
-- Description: Adds the Taskmaster agent - a personal accountability partner
--              that surfaces tasks from KB content, tracks progress, detects
--              slippage, and provides focus guidance via daily KB digest documents.
--
-- Category: Personal Productivity (alongside Compass)

-- ============================================================================
-- INSERT TASKMASTER AGENT
-- ============================================================================

INSERT INTO agents (name, display_name, description, is_active, capabilities, config)
VALUES (
    'taskmaster',
    'Taskmaster',
    'Personal accountability partner. Surfaces your tasks from meetings and documents, tracks progress, alerts on slippage, and provides focus guidance. Can generate daily task digest documents.',
    true,
    ARRAY[
        'task_discovery',
        'task_extraction',
        'progress_tracking',
        'slippage_detection',
        'focus_guidance',
        'commitment_tracking',
        'digest_generation'
    ],
    jsonb_build_object(
        'agent_type', 'personal_productivity',
        'domain', 'task_management',
        'responds_to', ARRAY['tasks', 'overdue', 'focus', 'what should i', 'my commitments', 'slipping', 'todo', 'action items', 'digest'],
        'handoffs', ARRAY['oracle', 'compass', 'operator']
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
    '-- Taskmaster agent instructions loaded from XML file: backend/system_instructions/agents/taskmaster.xml',
    'Initial Taskmaster agent creation - personal accountability partner',
    true
FROM agents
WHERE name = 'taskmaster'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- DONE!
-- ============================================================================
