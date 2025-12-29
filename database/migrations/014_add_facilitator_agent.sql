-- Migration: Add Facilitator Meta-Agent
-- Version: 014
-- Date: 2025-12-28
-- Description: Adds the Facilitator agent which orchestrates multi-agent meetings
--              The Facilitator is a meta-agent (not a domain expert) that:
--              - Welcomes and orients users at meeting start
--              - Clarifies intent before opening the floor
--              - Routes to appropriate specialist agents
--              - Ensures balanced participation
--              - Invokes systems thinking before conclusions
--              - Synthesizes discussions

-- Insert Facilitator agent
INSERT INTO agents (name, display_name, description, is_active, capabilities, metadata)
VALUES (
    'facilitator',
    'Facilitator',
    'Meeting orchestration meta-agent. Welcomes participants, clarifies intent, routes to specialists, ensures balanced participation, and synthesizes discussions. Not a domain expert - makes others brilliant.',
    true,
    ARRAY[
        'meeting_orchestration',
        'intent_analysis',
        'agent_routing',
        'balance_enforcement',
        'discussion_synthesis',
        'user_engagement'
    ],
    jsonb_build_object(
        'agent_type', 'meta',
        'always_present', true,
        'domain', 'facilitation',
        'created_at', now()
    )
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    capabilities = EXCLUDED.capabilities,
    metadata = agents.metadata || EXCLUDED.metadata;

-- Create initial instruction version for Facilitator
-- The actual instruction content comes from the XML file
INSERT INTO agent_instruction_versions (
    agent_id,
    version_number,
    instructions,
    is_active,
    created_by,
    change_notes
)
SELECT
    id,
    1,
    '-- Facilitator instructions loaded from XML file: backend/system_instructions/agents/facilitator.xml',
    true,
    'system',
    'Initial Facilitator agent creation - meta-agent for meeting orchestration'
FROM agents
WHERE name = 'facilitator'
ON CONFLICT DO NOTHING;

-- Grant Facilitator access to all knowledge base documents
-- This is handled programmatically, but we can add a flag to the metadata
UPDATE agents
SET metadata = metadata || jsonb_build_object('kb_access', 'all')
WHERE name = 'facilitator';

COMMENT ON COLUMN agents.metadata IS 'For facilitator: kb_access=all means access to all KB docs including agent-specific ones';
