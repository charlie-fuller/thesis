-- Migration 026: Add ADDIE Phase Categories to Quick Prompts
-- Purpose: Add ADDIE workflow awareness to quick prompts
-- Created: December 18, 2025

-- Add ADDIE phase and category columns
ALTER TABLE user_quick_prompts
  ADD COLUMN IF NOT EXISTS addie_phase VARCHAR(50),
  ADD COLUMN IF NOT EXISTS category VARCHAR(100),
  ADD COLUMN IF NOT EXISTS contextual_keywords TEXT[]; -- Array of keywords for context detection

-- Add index for efficient category filtering
CREATE INDEX IF NOT EXISTS idx_quick_prompts_addie_phase ON user_quick_prompts(addie_phase);
CREATE INDEX IF NOT EXISTS idx_quick_prompts_category ON user_quick_prompts(category);

-- Add check constraint for valid ADDIE phases
ALTER TABLE user_quick_prompts
  ADD CONSTRAINT check_addie_phase
  CHECK (addie_phase IS NULL OR addie_phase IN ('Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'General'));

-- Comment on new columns
COMMENT ON COLUMN user_quick_prompts.addie_phase IS 'ADDIE model phase this prompt belongs to (Analysis, Design, Development, Implementation, Evaluation, General)';
COMMENT ON COLUMN user_quick_prompts.category IS 'Category label for grouping prompts (e.g., "Needs Analysis", "Learning Objectives")';
COMMENT ON COLUMN user_quick_prompts.contextual_keywords IS 'Keywords for detecting when this prompt is contextually relevant';
