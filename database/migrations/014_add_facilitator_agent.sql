-- Migration: Add Facilitator Meta-Agent and Capabilities Column
-- Version: 014
-- Date: 2025-12-28
-- Description:
--   1. Adds capabilities column to agents table
--   2. Backfills capabilities for existing agents
--   3. Adds the Facilitator meta-agent for meeting orchestration

-- ============================================================================
-- STEP 1: Add capabilities column to agents table
-- ============================================================================
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS capabilities TEXT[] DEFAULT '{}';

COMMENT ON COLUMN agents.capabilities IS 'Array of capability tags for filtering and routing';

-- ============================================================================
-- STEP 2: Backfill capabilities for existing agents
-- ============================================================================

-- Atlas - Research
UPDATE agents SET capabilities = ARRAY[
    'research', 'benchmarking', 'case_studies', 'industry_trends',
    'lean_methodology', 'web_search', 'knowledge_synthesis'
] WHERE name = 'atlas';

-- Fortuna - Finance
UPDATE agents SET capabilities = ARRAY[
    'roi_analysis', 'financial_modeling', 'business_case',
    'sox_compliance', 'budget_justification', 'cost_analysis'
] WHERE name = 'fortuna';

-- Guardian - Security/IT
UPDATE agents SET capabilities = ARRAY[
    'security_assessment', 'compliance', 'governance',
    'vendor_evaluation', 'shadow_it', 'risk_analysis', 'infrastructure'
] WHERE name = 'guardian';

-- Counselor - Legal
UPDATE agents SET capabilities = ARRAY[
    'contract_review', 'legal_risk', 'data_privacy',
    'liability_assessment', 'regulatory_compliance', 'ai_ethics'
] WHERE name = 'counselor';

-- Oracle - Meeting Intelligence
UPDATE agents SET capabilities = ARRAY[
    'transcript_analysis', 'sentiment_extraction', 'stakeholder_mapping',
    'power_dynamics', 'meeting_insights', 'evidence_synthesis'
] WHERE name = 'oracle';

-- Sage - People/Change
UPDATE agents SET capabilities = ARRAY[
    'change_management', 'adoption_strategy', 'human_flourishing',
    'psychological_safety', 'champion_programs', 'resistance_handling'
] WHERE name = 'sage';

-- Strategist - Executive Strategy
UPDATE agents SET capabilities = ARRAY[
    'executive_engagement', 'stakeholder_management', 'governance_design',
    'coalition_building', 'strategic_alignment', 'sponsorship'
] WHERE name = 'strategist';

-- Architect - Technical
UPDATE agents SET capabilities = ARRAY[
    'architecture_design', 'integration_planning', 'rag_systems',
    'build_vs_buy', 'technical_assessment', 'mlops'
] WHERE name = 'architect';

-- Operator - Operations
UPDATE agents SET capabilities = ARRAY[
    'process_optimization', 'automation_assessment', 'metrics_design',
    'workflow_analysis', 'operational_readiness', 'baseline_measurement'
] WHERE name = 'operator';

-- Pioneer - Innovation
UPDATE agents SET capabilities = ARRAY[
    'emerging_tech', 'hype_filtering', 'maturity_assessment',
    'innovation_scouting', 'technology_evaluation', 'future_trends'
] WHERE name = 'pioneer';

-- Catalyst - Communications
UPDATE agents SET capabilities = ARRAY[
    'internal_communications', 'messaging_strategy', 'ai_anxiety_handling',
    'employee_engagement', 'narrative_development', 'change_communications'
] WHERE name = 'catalyst';

-- Scholar - Learning
UPDATE agents SET capabilities = ARRAY[
    'training_design', 'curriculum_development', 'champion_enablement',
    'adult_learning', 'skill_assessment', 'learning_programs'
] WHERE name = 'scholar';

-- Nexus - Systems Thinking
UPDATE agents SET capabilities = ARRAY[
    'systems_thinking', 'feedback_loops', 'leverage_points',
    'unintended_consequences', 'causal_analysis', 'complexity_mapping'
] WHERE name = 'nexus';

-- Echo - Brand Voice
UPDATE agents SET capabilities = ARRAY[
    'voice_analysis', 'style_profiling', 'brand_consistency',
    'tone_matching', 'ai_voice_guidelines', 'communication_style'
] WHERE name = 'echo';

-- Coordinator - Central orchestrator for chat
UPDATE agents SET capabilities = ARRAY[
    'query_routing', 'response_synthesis', 'agent_coordination',
    'context_management', 'multi_agent_orchestration'
] WHERE name = 'coordinator';

-- ============================================================================
-- STEP 3: Insert Facilitator agent
-- ============================================================================
INSERT INTO agents (name, display_name, description, is_active, capabilities, config)
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
        'kb_access', 'all'
    )
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    capabilities = EXCLUDED.capabilities,
    config = agents.config || EXCLUDED.config;

-- Create initial instruction version for Facilitator
-- The actual instruction content comes from the XML file
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
    '-- Facilitator instructions loaded from XML file: backend/system_instructions/agents/facilitator.xml',
    'Initial Facilitator agent creation - meta-agent for meeting orchestration',
    true
FROM agents
WHERE name = 'facilitator'
ON CONFLICT DO NOTHING;

-- Note: kb_access is already set in the config during INSERT above
-- The Facilitator's config.kb_access = 'all' grants access to all KB docs including agent-specific ones
