-- ============================================================================
-- ADD BARD AGENT - Brand Voice Analysis & Emulation Partner
-- Run after previous migrations
-- ============================================================================

-- Bard - Brand Voice Analysis & Emulation Partner
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('bard', 'Bard', 'Brand Voice Analysis & Emulation Partner - comprehensive voice profiling, writing style documentation, AI emulation guidelines, tone consistency auditing, multi-channel voice adaptation', TRUE, '{"category": "enablement", "focus": "brand-voice"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Bard
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
    '-- Bard system instruction loaded from XML file --',
    'Initial Bard agent - brand voice analysis, style profiling, AI emulation guidelines',
    TRUE,
    NOW()
FROM agents
WHERE name = 'bard'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- ============================================================================
-- DONE!
-- Bard agent added (Brand Voice Analysis & Emulation Partner)
-- Total agents now: 14
-- ============================================================================
