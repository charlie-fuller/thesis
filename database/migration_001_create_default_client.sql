-- Migration: Create Default Client for Single-Tenant Mode
-- Date: 2025-11-05
-- Purpose: Simplify architecture by creating a hidden default organization
-- Status: Safe to run multiple times (idempotent)

-- ============================================================================
-- PHASE 1.1: Create Default Client
-- ============================================================================

-- Create the default organization with well-known UUID
INSERT INTO clients (id, name, assistant_name, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000001',  -- Well-known UUID for easy reference
  'Default Organization',
  'Thesis',
  NOW(),
  NOW()
)
ON CONFLICT (id) DO UPDATE SET
  name = 'Default Organization',
  updated_at = NOW();

-- Verify the default client was created
SELECT
  id,
  name,
  assistant_name,
  created_at
FROM clients
WHERE id = '00000000-0000-0000-0000-000000000001';

-- ============================================================================
-- PHASE 1.2: Migrate Orphaned Users
-- ============================================================================

-- Count users without a client assignment (should be 0 in most cases)
SELECT
  'Users without client_id' as description,
  COUNT(*) as count
FROM users
WHERE client_id IS NULL;

-- Assign any orphaned users to the default client
UPDATE users
SET client_id = '00000000-0000-0000-0000-000000000001',
    updated_at = NOW()
WHERE client_id IS NULL;

-- Migrate conversations without a client to default client
UPDATE conversations
SET client_id = '00000000-0000-0000-0000-000000000001',
    updated_at = NOW()
WHERE client_id IS NULL;

-- Migrate documents without a client to default client
UPDATE documents
SET client_id = '00000000-0000-0000-0000-000000000001'
WHERE client_id IS NULL;

-- Migrate interview sessions without a client to default client
UPDATE interview_sessions
SET client_id = '00000000-0000-0000-0000-000000000001'
WHERE client_id IS NULL;

-- ============================================================================
-- PHASE 1.3: Verify Database Integrity
-- ============================================================================

-- Comprehensive integrity check
SELECT
  'Database Integrity Check' as report_section,
  'After Migration' as timing;

-- Check 1: All users should have the default client
SELECT
  'Users with NULL client_id' as check_name,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM users
WHERE client_id IS NULL;

-- Check 2: All conversations should have a client
SELECT
  'Conversations with NULL client_id' as check_name,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM conversations
WHERE client_id IS NULL;

-- Check 3: All documents should have a client
SELECT
  'Documents with NULL client_id' as check_name,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM documents
WHERE client_id IS NULL;

-- Check 4: All interview sessions should have a client
SELECT
  'Interview Sessions with NULL client_id' as check_name,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM interview_sessions
WHERE client_id IS NULL;

-- Summary statistics
SELECT
  'Summary Statistics' as report_section;

SELECT
  'Total Clients' as metric,
  COUNT(*) as count
FROM clients;

SELECT
  'Users in Default Client' as metric,
  COUNT(*) as count
FROM users
WHERE client_id = '00000000-0000-0000-0000-000000000001';

SELECT
  'Conversations in Default Client' as metric,
  COUNT(*) as count
FROM conversations
WHERE client_id = '00000000-0000-0000-0000-000000000001';

SELECT
  'Documents in Default Client' as metric,
  COUNT(*) as count
FROM documents
WHERE client_id = '00000000-0000-0000-0000-000000000001';

-- ============================================================================
-- ROLLBACK PLAN (if needed)
-- ============================================================================

-- If you need to undo this migration, run:
-- DELETE FROM clients WHERE id = '00000000-0000-0000-0000-000000000001';
-- Note: This will fail if there are foreign key constraints, which is good!
-- To properly rollback, you'd need to reassign users/conversations/documents first.

-- ============================================================================
-- NOTES
-- ============================================================================

-- 1. This migration is SAFE to run multiple times (idempotent)
-- 2. It does NOT delete any existing client data
-- 3. All existing data relationships are preserved
-- 4. RLS policies continue to work correctly
-- 5. The default client ID should be added to environment variables:
--    DEFAULT_CLIENT_ID=00000000-0000-0000-0000-000000000001
