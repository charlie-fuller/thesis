-- Migration 027: Drop alignment_documents table
-- Purpose: Removing alignment review step - Solomon Stage 1 → Stage 2 is now automatic
-- Created: November 21, 2025

-- Drop alignment_documents table and all dependencies
DROP TABLE IF EXISTS alignment_documents CASCADE;

-- Drop related functions
DROP FUNCTION IF EXISTS update_alignment_documents_updated_at() CASCADE;
DROP FUNCTION IF EXISTS set_alignment_approval_timestamp() CASCADE;

-- Note: Review will happen on system_instructions instead, not alignment documents
