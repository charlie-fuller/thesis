-- Migration: Add auto-generation support to user_prompts
-- Purpose: Track which prompts are auto-generated vs user-created
-- Date: 2025-11-21

-- Add columns for auto-generation tracking
ALTER TABLE user_prompts
ADD COLUMN IF NOT EXISTS is_auto_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Add index for filtering auto-generated prompts
CREATE INDEX IF NOT EXISTS idx_user_prompts_auto_generated
ON user_prompts(user_id, is_auto_generated);

-- Add comment explaining the new columns
COMMENT ON COLUMN user_prompts.is_auto_generated IS
'TRUE if prompt was auto-generated from function library during deployment, FALSE if user-created';

COMMENT ON COLUMN user_prompts.metadata IS
'JSON metadata including: function (which function generated this), generated_at (when/why it was generated)';

-- Sample auto-generated prompt structure:
-- {
--   "user_id": "uuid",
--   "title": "Help me prioritize my tasks for today",
--   "prompt_text": "Help me prioritize my tasks for today",
--   "category": "Productivity",
--   "is_auto_generated": true,
--   "metadata": {
--     "function": "priority_sorting_context_switching",
--     "generated_at": "deployment"
--   }
-- }
