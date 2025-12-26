-- Migration 025: User Quick Prompts
-- Purpose: Store auto-generated and custom quick prompts for users
-- Created: November 21, 2025

-- Create user_quick_prompts table
CREATE TABLE IF NOT EXISTS user_quick_prompts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  prompt_text TEXT NOT NULL,
  function_name VARCHAR(100), -- Which function this activates (e.g., 'Signal_Analyzer')
  system_generated BOOLEAN DEFAULT false, -- True if auto-generated, false if user-created
  editable BOOLEAN DEFAULT true, -- Can user edit/delete this prompt?
  active BOOLEAN DEFAULT true, -- Is this prompt currently active/visible?
  display_order INTEGER, -- Order in UI (lower numbers appear first)
  usage_count INTEGER DEFAULT 0, -- Track how often this prompt is used
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

  -- Prevent duplicate prompts for same user
  CONSTRAINT unique_user_prompt UNIQUE(user_id, prompt_text)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_quick_prompts_user ON user_quick_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_quick_prompts_client ON user_quick_prompts(client_id);
CREATE INDEX IF NOT EXISTS idx_quick_prompts_active ON user_quick_prompts(active);
CREATE INDEX IF NOT EXISTS idx_quick_prompts_function ON user_quick_prompts(function_name);
CREATE INDEX IF NOT EXISTS idx_quick_prompts_user_active ON user_quick_prompts(user_id, active);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_quick_prompts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_quick_prompts_updated_at
  BEFORE UPDATE ON user_quick_prompts
  FOR EACH ROW
  EXECUTE FUNCTION update_quick_prompts_updated_at();

-- Grant permissions (adjust based on your RLS policies)
ALTER TABLE user_quick_prompts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own quick prompts
CREATE POLICY quick_prompts_select_own
  ON user_quick_prompts
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own quick prompts
CREATE POLICY quick_prompts_insert_own
  ON user_quick_prompts
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own quick prompts
CREATE POLICY quick_prompts_update_own
  ON user_quick_prompts
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Policy: Users can delete their own quick prompts
CREATE POLICY quick_prompts_delete_own
  ON user_quick_prompts
  FOR DELETE
  USING (auth.uid() = user_id);

-- Comment on table and columns for documentation
COMMENT ON TABLE user_quick_prompts IS 'Stores quick prompts (shortcuts) for users to activate specific AI assistant functions';
COMMENT ON COLUMN user_quick_prompts.prompt_text IS 'The text of the quick prompt (e.g., "What can I delegate from this list?")';
COMMENT ON COLUMN user_quick_prompts.function_name IS 'Which core function this prompt activates (e.g., "Independence_Identifier")';
COMMENT ON COLUMN user_quick_prompts.system_generated IS 'True if auto-generated during Solomon setup, false if user-created';
COMMENT ON COLUMN user_quick_prompts.editable IS 'Whether user can edit/delete this prompt (normally true)';
COMMENT ON COLUMN user_quick_prompts.active IS 'Whether this prompt is currently visible/active in the UI';
COMMENT ON COLUMN user_quick_prompts.display_order IS 'Sort order for displaying prompts (lower = higher priority)';
COMMENT ON COLUMN user_quick_prompts.usage_count IS 'Number of times this prompt has been used (for analytics)';
