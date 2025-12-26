-- Migration 009: User-Level Document Isolation
-- Date: 2025-11-06
-- Purpose: Fix document sharing issue - ensure users can only see their own documents
--
-- ISSUE: Current RLS policies filter documents by client_id, but all users share
-- the same default client_id, meaning everyone can see everyone's documents.
--
-- SOLUTION: Add uploaded_by column and filter by user_id instead.

-- ============================================================================
-- STEP 1: ADD uploaded_by COLUMN TO DOCUMENTS TABLE
-- ============================================================================

ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES public.users(id) ON DELETE SET NULL;

COMMENT ON COLUMN public.documents.uploaded_by IS 'User ID who uploaded this document - used for user-level isolation';

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON public.documents(uploaded_by);

-- ============================================================================
-- STEP 2: MIGRATE EXISTING DOCUMENTS (Best Effort)
-- ============================================================================
-- For existing documents, try to assign to a user based on client_id
-- This is best-effort - some documents might not get assigned if no users exist

UPDATE public.documents
SET uploaded_by = (
  SELECT id
  FROM public.users
  WHERE client_id = documents.client_id
  ORDER BY created_at ASC
  LIMIT 1
)
WHERE uploaded_by IS NULL;

-- ============================================================================
-- STEP 3: UPDATE RLS POLICIES FOR DOCUMENTS TABLE
-- ============================================================================

-- Drop old client-based policies
DROP POLICY IF EXISTS "Users see own client documents" ON public.documents;
DROP POLICY IF EXISTS "Users can upload documents to their client" ON public.documents;
DROP POLICY IF EXISTS "users_view_own_client_documents" ON public.documents;
DROP POLICY IF EXISTS "users_upload_to_own_client" ON public.documents;
DROP POLICY IF EXISTS "users_update_own_client_documents" ON public.documents;
DROP POLICY IF EXISTS "users_delete_own_client_documents" ON public.documents;

-- Create new user-based policies

-- Policy: Users can view their own documents
CREATE POLICY "users_view_own_documents"
ON public.documents
FOR SELECT
TO authenticated
USING (uploaded_by = auth.uid());

-- Policy: Admins can view all documents
CREATE POLICY "admins_view_all_documents"
ON public.documents
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Policy: Users can upload documents (must set uploaded_by to themselves)
CREATE POLICY "users_upload_own_documents"
ON public.documents
FOR INSERT
TO authenticated
WITH CHECK (uploaded_by = auth.uid());

-- Policy: Admins can insert documents for any user
CREATE POLICY "admins_insert_documents"
ON public.documents
FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Policy: Users can update their own documents
CREATE POLICY "users_update_own_documents"
ON public.documents
FOR UPDATE
TO authenticated
USING (uploaded_by = auth.uid())
WITH CHECK (uploaded_by = auth.uid());

-- Policy: Admins can update all documents
CREATE POLICY "admins_update_all_documents"
ON public.documents
FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Policy: Users can delete their own documents
CREATE POLICY "users_delete_own_documents"
ON public.documents
FOR DELETE
TO authenticated
USING (uploaded_by = auth.uid());

-- Policy: Admins can delete all documents
CREATE POLICY "admins_delete_all_documents"
ON public.documents
FOR DELETE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- ============================================================================
-- STEP 4: UPDATE RLS POLICIES FOR DOCUMENT_CHUNKS TABLE
-- ============================================================================

-- Drop old client-based policies
DROP POLICY IF EXISTS "users_view_own_client_chunks" ON public.document_chunks;
DROP POLICY IF EXISTS "users_insert_chunks_for_own_client" ON public.document_chunks;

-- Create new user-based policies (chunks inherit from documents)

-- Policy: Users can view chunks from their own documents
CREATE POLICY "users_view_own_document_chunks"
ON public.document_chunks
FOR SELECT
TO authenticated
USING (
  document_id IN (
    SELECT id FROM public.documents
    WHERE uploaded_by = auth.uid()
  )
);

-- Policy: Admins can view all chunks
CREATE POLICY "admins_view_all_chunks"
ON public.document_chunks
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Policy: Users can insert chunks for their own documents
CREATE POLICY "users_insert_own_document_chunks"
ON public.document_chunks
FOR INSERT
TO authenticated
WITH CHECK (
  document_id IN (
    SELECT id FROM public.documents
    WHERE uploaded_by = auth.uid()
  )
);

-- Policy: Admins can insert chunks for any document
CREATE POLICY "admins_insert_all_chunks"
ON public.document_chunks
FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Policy: Users can update chunks for their own documents
CREATE POLICY "users_update_own_document_chunks"
ON public.document_chunks
FOR UPDATE
TO authenticated
USING (
  document_id IN (
    SELECT id FROM public.documents
    WHERE uploaded_by = auth.uid()
  )
);

-- Policy: Users can delete chunks for their own documents
CREATE POLICY "users_delete_own_document_chunks"
ON public.document_chunks
FOR DELETE
TO authenticated
USING (
  document_id IN (
    SELECT id FROM public.documents
    WHERE uploaded_by = auth.uid()
  )
);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check that uploaded_by column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'documents' AND column_name = 'uploaded_by';

-- Check RLS policies on documents
SELECT policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'documents'
ORDER BY policyname;

-- Check RLS policies on document_chunks
SELECT policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'document_chunks'
ORDER BY policyname;

-- Verify documents have uploaded_by set
SELECT
  COUNT(*) as total_documents,
  COUNT(uploaded_by) as documents_with_owner,
  COUNT(*) - COUNT(uploaded_by) as orphaned_documents
FROM public.documents;

-- ============================================================================
-- NOTES
-- ============================================================================
--
-- SECURITY FIX: This migration ensures complete user-level isolation for documents.
--
-- Before this migration:
--   - All users shared the same client_id
--   - Documents were filtered by client_id
--   - Result: ALL users could see ALL documents (SECURITY ISSUE!)
--
-- After this migration:
--   - Documents are filtered by uploaded_by (user_id)
--   - Each user can ONLY see their own documents
--   - Admins can see all documents
--   - Complete user-level isolation achieved
--
-- BACKEND UPDATE REQUIRED:
--   - Document upload endpoint must set uploaded_by = current_user['id']
--   - See: backend/main.py - /api/documents/upload endpoint
--
-- ============================================================================
