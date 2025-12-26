-- Migration: Recalculate storage_used for all users
-- Date: 2025-11-16
-- Description: Fix storage_used values that may have been incorrectly calculated due to double increment/decrement bug
-- This migration uses the recalculate_all_user_storage() function from migration 018

-- Run the recalculation to fix any inconsistencies
SELECT recalculate_all_user_storage();

COMMENT ON FUNCTION recalculate_all_user_storage() IS 'Recalculates storage_used for all users, excluding external sources (Google Drive, Notion)';
