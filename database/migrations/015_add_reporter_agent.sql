-- Migration: Add Reporter Meta-Agent
-- Version: 015
-- Date: 2025-12-28
-- Description:
--   Adds the Reporter meta-agent for meeting synthesis and documentation.
--   Reporter is ALWAYS present in meetings alongside Facilitator.
--   - Facilitator: Manages conversation flow, routes to agents
--   - Reporter: Synthesizes discussions, creates summaries and action items

-- ============================================================================
-- STEP 1: Insert Reporter agent
-- ============================================================================
INSERT INTO agents (name, display_name, description, is_active, capabilities, config)
VALUES (
    'reporter',
    'Reporter',
    'Meeting synthesis meta-agent. Distills multi-agent discussions into clear summaries, action items, and executive briefs. Provides one unified voice for documentation with proper attribution. Does not offer domain expertise.',
    true,
    ARRAY[
        'meeting_synthesis',
        'summary_generation',
        'action_items',
        'executive_briefs',
        'disagreement_documentation',
        'attribution_tracking'
    ],
    jsonb_build_object(
        'agent_type', 'meta',
        'always_present', true,
        'domain', 'documentation',
        'kb_access', 'all',
        'responds_to', ARRAY['summary', 'recap', 'action_items', 'takeaways', 'brief']
    )
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    capabilities = EXCLUDED.capabilities,
    config = agents.config || EXCLUDED.config;

-- ============================================================================
-- STEP 2: Create initial instruction version for Reporter
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
    '1',
    '-- Reporter instructions loaded from XML file: backend/system_instructions/agents/reporter.xml',
    'Initial Reporter agent creation - meta-agent for meeting synthesis and documentation',
    true
FROM agents
WHERE name = 'reporter'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- STEP 3: Update CLAUDE.md agent count reference (optional comment)
-- ============================================================================
-- Note: Update CLAUDE.md to reflect 17 agents (was 16):
--   - 15 domain specialists
--   - 2 meta-agents (Facilitator + Reporter)
