-- Migration: Cleanup Digest Preferences
-- Date: 2026-01-20
-- Description: Removes the user_digest_preferences table that was created
--              before we simplified to KB-based digests instead of Slack.
--
-- Run this ONLY if you ran the original 027 migration that included
-- the user_digest_preferences table.

-- ============================================================================
-- DROP POLICIES FIRST
-- ============================================================================

DROP POLICY IF EXISTS "Users can manage their own digest preferences" ON user_digest_preferences;

-- ============================================================================
-- DROP INDEXES
-- ============================================================================

DROP INDEX IF EXISTS idx_user_digest_enabled_time;

-- ============================================================================
-- DROP TABLE
-- ============================================================================

DROP TABLE IF EXISTS user_digest_preferences;

-- ============================================================================
-- DONE!
-- ============================================================================
