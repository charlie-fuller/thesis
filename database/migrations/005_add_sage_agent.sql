-- ============================================================================
-- ADD SAGE AGENT - People & Human Flourishing Specialist
-- Run after previous migrations
-- ============================================================================

-- Insert the Sage agent into the registry
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('sage', 'Sage', 'People & Human Flourishing agent - ensures AI initiatives are human-centered, addresses change resistance and fear, builds community and psychological safety, promotes meaningful work', TRUE, '{"philosophy": "people-first", "inspired_by": "Chad Meek approach"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Sage
INSERT INTO agent_instruction_versions (
    agent_id,
    version_number,
    instructions,
    description,
    is_active,
    activated_at
)
SELECT
    id,
    '1.0.0',
    '-- Sage system instruction is embedded in code for v1.0 --',
    'Initial Sage agent - human-centered change management, community building, psychological safety',
    TRUE,
    NOW()
FROM agents
WHERE name = 'sage'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- ============================================================================
-- DONE!
-- ============================================================================
