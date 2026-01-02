-- Migration: Rename Fortuna agent to Capital
-- Date: 2025-01-02
-- Description: Renames the finance agent from "Fortuna" to "Capital" for better intuitive recognition

-- Update the agent name in the agents table
UPDATE agents
SET
    name = 'capital',
    display_name = 'Capital',
    updated_at = NOW()
WHERE name = 'fortuna';

-- Update any agent_knowledge_base references (foreign key should handle this, but just in case)
-- The agent_id column references agents.id, so no change needed there

-- Update any meeting_room_participants that reference the agent by name
-- (if there's a name column - check schema)

-- Update agent_handoffs table if it references agent names
UPDATE agent_handoffs
SET from_agent = 'capital'
WHERE from_agent = 'fortuna';

UPDATE agent_handoffs
SET to_agent = 'capital'
WHERE to_agent = 'fortuna';

-- Update agent_topic_mapping if it exists
UPDATE agent_topic_mapping
SET agent_name = 'capital'
WHERE agent_name = 'fortuna';

-- Note: Run this migration in production after deploying the code changes
-- The code changes rename all references from fortuna to capital
