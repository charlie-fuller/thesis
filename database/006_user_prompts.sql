-- Migration 006: User Prompts (Quick Prompt Templates)
-- Created: 2025-11-03
-- Description: Add user_prompts table for per-user quick prompt templates

-- Create user_prompts table
CREATE TABLE IF NOT EXISTS user_prompts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  prompt_text TEXT NOT NULL,
  display_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_prompts_user_id ON user_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_prompts_display_order ON user_prompts(user_id, display_order);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_user_prompts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_prompts_updated_at
  BEFORE UPDATE ON user_prompts
  FOR EACH ROW
  EXECUTE FUNCTION update_user_prompts_updated_at();

-- Insert default prompts for existing users
-- These are generic starter prompts that work for any user
INSERT INTO user_prompts (user_id, title, prompt_text, display_order)
SELECT
  u.id,
  'Weekly Status Update',
  'Please provide a comprehensive status update on my current projects, including:
- What I accomplished this week
- What I''m working on now
- Any blockers or challenges
- Next week''s priorities',
  1
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM user_prompts up WHERE up.user_id = u.id
);

INSERT INTO user_prompts (user_id, title, prompt_text, display_order)
SELECT
  u.id,
  'Summarize Email',
  'Please summarize the key points from this email and suggest action items:

[Paste email content here]',
  2
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM user_prompts up WHERE up.user_id = u.id AND up.title = 'Summarize Email'
);

INSERT INTO user_prompts (user_id, title, prompt_text, display_order)
SELECT
  u.id,
  'Meeting Prep',
  'Help me prepare for an upcoming meeting:
- Meeting topic: [TOPIC]
- Attendees: [NAMES]
- My goals: [GOALS]

Please suggest:
1. Key talking points
2. Questions to ask
3. Potential objections and responses',
  3
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM user_prompts up WHERE up.user_id = u.id AND up.title = 'Meeting Prep'
);

INSERT INTO user_prompts (user_id, title, prompt_text, display_order)
SELECT
  u.id,
  'Draft Response',
  'Help me draft a professional response to this message:

[Paste message here]

Tone should be: [professional/friendly/formal]
Key points to address: [POINTS]',
  4
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM user_prompts up WHERE up.user_id = u.id AND up.title = 'Draft Response'
);

INSERT INTO user_prompts (user_id, title, prompt_text, display_order)
SELECT
  u.id,
  'Research Summary',
  'Please research and summarize information about:

Topic: [TOPIC]

Include:
- Key facts and statistics
- Current trends
- Notable examples or case studies
- Relevant resources for deeper reading',
  5
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM user_prompts up WHERE up.user_id = u.id AND up.title = 'Research Summary'
);

-- Grant permissions (if using RLS)
-- Note: Admins can manage all prompts, users can only read their own
ALTER TABLE user_prompts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own prompts
CREATE POLICY user_prompts_select_own ON user_prompts
  FOR SELECT
  USING (
    auth.uid() IN (
      SELECT id FROM users WHERE id = user_id
    )
  );

-- Policy: Admins can manage all prompts
CREATE POLICY user_prompts_all_admin ON user_prompts
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE id = auth.uid()
      AND role = 'admin'
    )
  );

-- Policy: Client admins can manage prompts for their client's users
CREATE POLICY user_prompts_client_admin ON user_prompts
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users u1
      JOIN users u2 ON u1.client_id = u2.client_id
      WHERE u1.id = auth.uid()
      AND u1.role = 'client_admin'
      AND u2.id = user_prompts.user_id
    )
  );

COMMENT ON TABLE user_prompts IS 'User-specific quick prompt templates for chat interface';
COMMENT ON COLUMN user_prompts.title IS 'Short display name for the prompt (shown in sidebar)';
COMMENT ON COLUMN user_prompts.prompt_text IS 'Full prompt text (populated into chat input when clicked)';
COMMENT ON COLUMN user_prompts.display_order IS 'Order in which prompts appear (1 = first, 2 = second, etc.)';
