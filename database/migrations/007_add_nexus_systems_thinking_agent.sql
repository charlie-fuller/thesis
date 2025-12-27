-- ============================================================================
-- ADD NEXUS - SYSTEMS THINKING AGENT
-- The interconnection specialist for understanding feedback loops, leverage
-- points, and systemic effects in AI transformation initiatives
-- Run after 006_add_new_specialist_agents.sql
-- ============================================================================

-- ============================================================================
-- SYSTEMS THINKING AGENT
-- ============================================================================

-- Nexus - Systems Thinking & Interconnection Analysis
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('nexus', 'Nexus', 'Systems Thinking & Interconnection Analysis - feedback loops, leverage points, causal diagrams, system archetypes, second-order effects, avoiding unintended consequences', TRUE, '{"category": "methodology", "focus": "systems-thinking"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Nexus
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
    '-- Nexus system instruction loaded from Python agent file --',
    'Initial Nexus agent - systems thinking, feedback loops, leverage points, Donella Meadows methodology',
    TRUE,
    NOW()
FROM agents
WHERE name = 'nexus'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- ============================================================================
-- DONE!
-- Nexus (Systems Thinking) agent added
-- ============================================================================
