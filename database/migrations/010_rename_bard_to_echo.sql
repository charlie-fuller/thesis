-- ============================================================================
-- RENAME BARD AGENT TO ECHO
-- Run after 009_add_bard_agent.sql
-- ============================================================================

-- Rename the agent from bard to echo
UPDATE agents
SET
    name = 'echo',
    display_name = 'Echo',
    description = 'Brand Voice Analysis & Emulation Partner - comprehensive voice profiling, writing style documentation, AI emulation guidelines, tone consistency auditing, multi-channel voice adaptation',
    updated_at = NOW()
WHERE name = 'bard';

-- Update the instruction version description to reflect the new name
UPDATE agent_instruction_versions
SET
    description = 'Initial Echo agent - brand voice analysis, style profiling, AI emulation guidelines'
WHERE agent_id = (SELECT id FROM agents WHERE name = 'echo')
  AND description LIKE '%Bard%';

-- ============================================================================
-- DONE!
-- Bard agent renamed to Echo
-- ============================================================================
