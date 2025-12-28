-- ============================================================================
-- ADD NEW SPECIALIST AGENTS
-- Consulting/Implementation: Strategist, Architect, Operator, Pioneer
-- Internal Enablement: Catalyst, Scholar
-- Run after previous migrations
-- ============================================================================

-- ============================================================================
-- CONSULTING/IMPLEMENTATION AGENTS
-- ============================================================================

-- Strategist - Executive Strategy Partner
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('strategist', 'Strategist', 'Executive Strategy Partner - C-suite engagement, organizational politics, governance design, business case development for executives', TRUE, '{"category": "consulting", "focus": "executive-strategy"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Strategist
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
    '-- Strategist system instruction loaded from XML file --',
    'Initial Strategist agent - executive strategy, C-suite engagement, governance design',
    TRUE,
    NOW()
FROM agents
WHERE name = 'strategist'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- Architect - Technical Architecture Partner
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('architect', 'Architect', 'Technical Architecture Partner - enterprise AI patterns (RAG, agents), integration design, build vs buy analysis, security architecture, MLOps', TRUE, '{"category": "consulting", "focus": "technical-architecture"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Architect
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
    '-- Architect system instruction loaded from XML file --',
    'Initial Architect agent - technical architecture, enterprise AI patterns, integration',
    TRUE,
    NOW()
FROM agents
WHERE name = 'architect'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- Operator - Business Operations Partner
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('operator', 'Operator', 'Business Operations Partner - process analysis, workflow optimization, automation assessment, operational metrics and KPIs, ground-level change management', TRUE, '{"category": "consulting", "focus": "operations"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Operator
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
    '-- Operator system instruction loaded from XML file --',
    'Initial Operator agent - process optimization, automation, operational metrics',
    TRUE,
    NOW()
FROM agents
WHERE name = 'operator'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- Pioneer - Innovation/R&D Partner
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('pioneer', 'Pioneer', 'Innovation/R&D Partner - emerging technology scouting, technology maturity assessment, hype cycle navigation, innovation portfolio strategy', TRUE, '{"category": "consulting", "focus": "innovation"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Pioneer
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
    '-- Pioneer system instruction loaded from XML file --',
    'Initial Pioneer agent - emerging technology, innovation, hype filtering',
    TRUE,
    NOW()
FROM agents
WHERE name = 'pioneer'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- ============================================================================
-- INTERNAL ENABLEMENT AGENTS
-- ============================================================================

-- Catalyst - Internal Communications Partner
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('catalyst', 'Catalyst', 'Internal Communications Partner - AI initiative messaging, employee engagement, addressing AI anxiety, multi-channel communication strategies', TRUE, '{"category": "enablement", "focus": "internal-communications"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Catalyst
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
    '-- Catalyst system instruction loaded from XML file --',
    'Initial Catalyst agent - internal communications, AI messaging, employee engagement',
    TRUE,
    NOW()
FROM agents
WHERE name = 'catalyst'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- Scholar - Learning & Development Partner
INSERT INTO agents (name, display_name, description, is_active, config) VALUES
    ('scholar', 'Scholar', 'Learning & Development Partner - AI training program design, champion enablement, skill development, adult learning methodology', TRUE, '{"category": "enablement", "focus": "learning-development"}')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    is_active = TRUE,
    updated_at = NOW();

-- Add initial system instruction version for Scholar
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
    '-- Scholar system instruction loaded from XML file --',
    'Initial Scholar agent - L&D, training programs, champion enablement',
    TRUE,
    NOW()
FROM agents
WHERE name = 'scholar'
ON CONFLICT (agent_id, version_number) DO NOTHING;

-- ============================================================================
-- DONE!
-- All 6 new specialist agents added:
-- - Strategist (Executive Strategy)
-- - Architect (Technical Architecture)
-- - Operator (Business Operations)
-- - Pioneer (Innovation/R&D)
-- - Catalyst (Internal Communications)
-- - Scholar (Learning & Development)
-- ============================================================================
