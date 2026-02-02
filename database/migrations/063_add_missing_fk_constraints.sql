-- Migration: Add missing foreign key constraints
-- Purpose: Ensure referential integrity and prevent orphaned records
-- Date: 2026-02-02

-- ============================================================================
-- DOCUMENTS TABLE
-- ============================================================================

-- Add FK on documents.uploaded_by if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'documents_uploaded_by_fkey'
    ) THEN
        ALTER TABLE documents
        ADD CONSTRAINT documents_uploaded_by_fkey
        FOREIGN KEY (uploaded_by) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add FK on documents.client_id if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'documents_client_id_fkey'
    ) THEN
        ALTER TABLE documents
        ADD CONSTRAINT documents_client_id_fkey
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add FK on documents.user_id (some tables use user_id instead of uploaded_by)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'user_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'documents_user_id_fkey'
    ) THEN
        ALTER TABLE documents
        ADD CONSTRAINT documents_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- CONVERSATIONS TABLE
-- ============================================================================

-- Add FK on conversations.user_id if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'conversations_user_id_fkey'
    ) THEN
        ALTER TABLE conversations
        ADD CONSTRAINT conversations_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add FK on conversations.client_id if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'conversations_client_id_fkey'
    ) THEN
        ALTER TABLE conversations
        ADD CONSTRAINT conversations_client_id_fkey
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================================================
-- MESSAGES TABLE
-- ============================================================================

-- Add FK on messages.conversation_id if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'messages_conversation_id_fkey'
    ) THEN
        ALTER TABLE messages
        ADD CONSTRAINT messages_conversation_id_fkey
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================================================
-- MESSAGE_DOCUMENTS TABLE (links messages to documents)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'message_documents'
    ) THEN
        -- Add FK on message_documents.message_id if not exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'message_documents_message_id_fkey'
        ) THEN
            ALTER TABLE message_documents
            ADD CONSTRAINT message_documents_message_id_fkey
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE;
        END IF;

        -- Add FK on message_documents.document_id if not exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'message_documents_document_id_fkey'
        ) THEN
            ALTER TABLE message_documents
            ADD CONSTRAINT message_documents_document_id_fkey
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- ============================================================================
-- DOCUMENT_CHUNKS TABLE
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'document_chunks_document_id_fkey'
    ) THEN
        ALTER TABLE document_chunks
        ADD CONSTRAINT document_chunks_document_id_fkey
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================================================
-- TASKS TABLE
-- ============================================================================

-- Add FK on tasks.client_id if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'tasks_client_id_fkey'
    ) THEN
        ALTER TABLE tasks
        ADD CONSTRAINT tasks_client_id_fkey
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add FK on tasks.created_by_user_id if not exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'created_by_user_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'tasks_created_by_user_id_fkey'
    ) THEN
        ALTER TABLE tasks
        ADD CONSTRAINT tasks_created_by_user_id_fkey
        FOREIGN KEY (created_by_user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- AI_PROJECTS TABLE (formerly opportunities)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ai_projects_client_id_fkey'
    ) THEN
        ALTER TABLE ai_projects
        ADD CONSTRAINT ai_projects_client_id_fkey
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ai_projects' AND column_name = 'owner_stakeholder_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ai_projects_owner_stakeholder_id_fkey'
    ) THEN
        ALTER TABLE ai_projects
        ADD CONSTRAINT ai_projects_owner_stakeholder_id_fkey
        FOREIGN KEY (owner_stakeholder_id) REFERENCES stakeholders(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- PROJECT_CONVERSATIONS TABLE
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'project_conversations'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'project_conversations_project_id_fkey'
        ) THEN
            ALTER TABLE project_conversations
            ADD CONSTRAINT project_conversations_project_id_fkey
            FOREIGN KEY (project_id) REFERENCES ai_projects(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- ============================================================================
-- USERS TABLE (link to clients)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'client_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_client_id_fkey'
    ) THEN
        ALTER TABLE users
        ADD CONSTRAINT users_client_id_fkey
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- This migration adds foreign key constraints to ensure:
-- 1. When a user is deleted, their documents become unowned (SET NULL)
-- 2. When a client is deleted, all associated data is cleaned up (CASCADE)
-- 3. When a conversation is deleted, messages are deleted (CASCADE)
-- 4. When a document is deleted, chunks and links are deleted (CASCADE)
-- 5. When a stakeholder is deleted, project ownership is cleared (SET NULL)
