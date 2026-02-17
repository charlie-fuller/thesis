-- Migration 076: Add user_corrections field to disco_initiatives
-- Supports ground-truth corrections that override document content in agent prompts

ALTER TABLE disco_initiatives
ADD COLUMN IF NOT EXISTS user_corrections TEXT DEFAULT NULL;
