-- ============================================================================
-- MIGRATION: Add Compass Agent (Personal Career Coach)
-- Description: Adds the Compass agent for personal career development,
--              win capture, check-in preparation, and strategic alignment
-- Author: Claude
-- Date: 2025-01-15
-- ============================================================================

-- ============================================================================
-- STEP 1: Insert Compass agent into agents table
-- ============================================================================

INSERT INTO agents (
    name,
    display_name,
    description,
    is_active,
    config,
    created_at,
    updated_at
)
VALUES (
    'compass',
    'Compass',
    'Personal Career Coach - Win capture, check-in preparation, strategic alignment tracking, and performance documentation through natural conversation.',
    true,
    '{
        "category": "personal_development",
        "capabilities": [
            "win_capture",
            "checkin_preparation",
            "strategic_alignment",
            "goal_tracking",
            "reflection_prompting",
            "document_management"
        ],
        "handoffs": {
            "sage": "people/change management challenges",
            "scholar": "training program design",
            "strategist": "executive-level career strategy",
            "oracle": "meeting transcript analysis"
        }
    }'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    config = EXCLUDED.config,
    updated_at = NOW();

-- ============================================================================
-- STEP 2: Create initial instruction version (placeholder)
-- The actual XML content will be synced via sync_all_xml_to_db.py script
-- ============================================================================

INSERT INTO agent_instruction_versions (
    agent_id,
    version_number,
    instructions,
    description,
    is_active,
    activated_at,
    created_at,
    updated_at
)
SELECT
    id,
    '1.0',
    '-- Placeholder: Run sync_all_xml_to_db.py to load full XML instructions --',
    'Initial placeholder - sync XML to populate',
    true,
    NOW(),
    NOW(),
    NOW()
FROM agents
WHERE name = 'compass'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Note: After running this migration, execute:
--   cd backend
--   source venv/bin/activate
--   python scripts/sync_all_xml_to_db.py
--
-- This will populate the full XML instructions from compass.xml
