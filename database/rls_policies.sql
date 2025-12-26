-- Row Level Security Policies for Thesis
-- This file contains RLS policies to ensure users can only access their own data

-- ============================================
-- ENABLE RLS ON TABLES
-- ============================================

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- ============================================
-- DOCUMENTS TABLE POLICIES
-- ============================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users see own client documents" ON public.documents;
DROP POLICY IF EXISTS "Admins see all documents" ON public.documents;
DROP POLICY IF EXISTS "Client admins see their client documents" ON public.documents;
DROP POLICY IF EXISTS "Users can upload documents to their client" ON public.documents;

-- Users can only see documents from their client
CREATE POLICY "Users see own client documents"
ON public.documents
FOR SELECT
TO authenticated
USING (
  client_id IN (
    SELECT client_id FROM public.users WHERE id = auth.uid()
  )
);

-- Admins can see all documents
CREATE POLICY "Admins see all documents"
ON public.documents
FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Client admins can see and manage their client's documents
CREATE POLICY "Client admins see their client documents"
ON public.documents
FOR ALL
TO authenticated
USING (
  client_id IN (
    SELECT client_id FROM public.users
    WHERE id = auth.uid()
    AND role = 'client_admin'
  )
);

-- Users can upload documents to their client
CREATE POLICY "Users can upload documents to their client"
ON public.documents
FOR INSERT
TO authenticated
WITH CHECK (
  client_id IN (
    SELECT client_id FROM public.users WHERE id = auth.uid()
  )
);

-- ============================================
-- CONVERSATIONS TABLE POLICIES
-- ============================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users see own conversations" ON public.conversations;
DROP POLICY IF EXISTS "Users create conversations" ON public.conversations;
DROP POLICY IF EXISTS "Users update own conversations" ON public.conversations;
DROP POLICY IF EXISTS "Admins see all conversations" ON public.conversations;
DROP POLICY IF EXISTS "Client admins see their client conversations" ON public.conversations;

-- Users can only see their own conversations
CREATE POLICY "Users see own conversations"
ON public.conversations
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

-- Users can create conversations
CREATE POLICY "Users create conversations"
ON public.conversations
FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid());

-- Users can update their own conversations
CREATE POLICY "Users update own conversations"
ON public.conversations
FOR UPDATE
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Admins can see all conversations
CREATE POLICY "Admins see all conversations"
ON public.conversations
FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Client admins can see conversations for their client
CREATE POLICY "Client admins see their client conversations"
ON public.conversations
FOR ALL
TO authenticated
USING (
  client_id IN (
    SELECT client_id FROM public.users
    WHERE id = auth.uid()
    AND role = 'client_admin'
  )
);

-- ============================================
-- MESSAGES TABLE POLICIES
-- ============================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users see own messages" ON public.messages;
DROP POLICY IF EXISTS "Users create messages" ON public.messages;
DROP POLICY IF EXISTS "Admins see all messages" ON public.messages;
DROP POLICY IF EXISTS "Client admins see their client messages" ON public.messages;

-- Users can see messages from their conversations
CREATE POLICY "Users see own messages"
ON public.messages
FOR SELECT
TO authenticated
USING (
  conversation_id IN (
    SELECT id FROM public.conversations WHERE user_id = auth.uid()
  )
);

-- Users can create messages in their conversations
CREATE POLICY "Users create messages"
ON public.messages
FOR INSERT
TO authenticated
WITH CHECK (
  conversation_id IN (
    SELECT id FROM public.conversations WHERE user_id = auth.uid()
  )
);

-- Admins can see all messages
CREATE POLICY "Admins see all messages"
ON public.messages
FOR ALL
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

-- Client admins can see messages for their client's conversations
CREATE POLICY "Client admins see their client messages"
ON public.messages
FOR ALL
TO authenticated
USING (
  conversation_id IN (
    SELECT id FROM public.conversations
    WHERE client_id IN (
      SELECT client_id FROM public.users
      WHERE id = auth.uid()
      AND role = 'client_admin'
    )
  )
);

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Run these queries to verify the policies are in place:

-- Check RLS is enabled
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE tablename IN ('documents', 'conversations', 'messages');

-- List all policies
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
-- FROM pg_policies
-- WHERE tablename IN ('documents', 'conversations', 'messages')
-- ORDER BY tablename, policyname;
