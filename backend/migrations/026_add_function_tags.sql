-- Migration: Add function tags to conversations
-- Date: 2025-11-23
-- Purpose: Tag conversations with AI function for future analysis (not used in KPIs yet)

-- Add function_tag column to conversations table
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS function_tag TEXT;

-- Add optional strategic classification for future use
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS is_strategic BOOLEAN DEFAULT NULL;

-- Add index for function queries
CREATE INDEX IF NOT EXISTS idx_conversations_function_tag ON conversations(function_tag) WHERE function_tag IS NOT NULL;

-- Add comments
COMMENT ON COLUMN conversations.function_tag IS 'AI function aligned with this conversation (e.g., Conceptual_Modeler, Independence_Identifier, etc.). NULL if no function alignment or not yet classified.';
COMMENT ON COLUMN conversations.is_strategic IS 'Whether this conversation involves strategic work (planning, decision-making, etc.). NULL if not yet classified. Not used for KPIs currently - all conversations count equally.';

-- Valid function tags (for documentation):
-- - Conceptual_Modeler: Frameworks, models, structuring thinking
-- - Independence_Identifier: Delegation, team empowerment
-- - Report_Builder: Written communications (memos, briefs, reports)
-- - Signal_Analyzer: Prioritization, focus, signal vs noise
-- - Meeting_Optimizer: Meeting preparation and follow-up
-- - NULL: No function alignment or not yet classified
