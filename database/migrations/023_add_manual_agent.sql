-- Migration: Add Manual Agent
-- Date: 2026-01-16
-- Description: Adds the Manual agent - an in-app documentation assistant
--              that helps users understand Thesis features, navigate the
--              platform, and troubleshoot issues.
--
-- Category: Internal Enablement (alongside Scholar, Catalyst, Glean Evaluator)

-- ============================================================================
-- INSERT MANUAL AGENT
-- ============================================================================

INSERT INTO agents (name, display_name, description, is_active, capabilities, config)
VALUES (
    'manual',
    'Manual',
    'In-app documentation assistant. Helps users understand Thesis features, navigate the platform, troubleshoot issues, and learn best practices. Has access to all platform documentation.',
    true,
    ARRAY[
        'feature_explanation',
        'navigation_guidance',
        'troubleshooting_support',
        'best_practices',
        'onboarding_help',
        'workflow_guidance'
    ],
    jsonb_build_object(
        'agent_type', 'internal_enablement',
        'domain', 'platform_documentation',
        'kb_access', 'manual_docs_only',
        'responds_to', ARRAY['how do i', 'where is', 'help', 'what is', 'how to', 'explain', 'tutorial'],
        'handoffs', ARRAY['scholar']
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
    '-- Manual agent instructions loaded from XML file: backend/system_instructions/agents/manual.xml',
    'Initial Manual agent creation - platform documentation assistant',
    true
FROM agents
WHERE name = 'manual'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- DONE!
-- ============================================================================
