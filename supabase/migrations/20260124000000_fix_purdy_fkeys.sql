-- Migration: 041_fix_purdy_fkeys
-- Description: Fix PuRDy foreign keys to reference public.users instead of auth.users
-- This allows PostgREST joins to work correctly
-- Date: 2026-01-23

-- ============================================================================
-- FIX PURDY_INITIATIVES FOREIGN KEY
-- ============================================================================

-- Drop existing foreign key constraint on created_by
ALTER TABLE purdy_initiatives
    DROP CONSTRAINT IF EXISTS purdy_initiatives_created_by_fkey;

-- Add new foreign key referencing public.users
ALTER TABLE purdy_initiatives
    ADD CONSTRAINT purdy_initiatives_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES public.users(id);

-- ============================================================================
-- FIX PURDY_RUNS FOREIGN KEY
-- ============================================================================

-- Drop existing foreign key constraint on run_by
ALTER TABLE purdy_runs
    DROP CONSTRAINT IF EXISTS purdy_runs_run_by_fkey;

-- Add new foreign key referencing public.users
ALTER TABLE purdy_runs
    ADD CONSTRAINT purdy_runs_run_by_fkey
    FOREIGN KEY (run_by) REFERENCES public.users(id);

-- ============================================================================
-- FIX PURDY_INITIATIVE_MEMBERS FOREIGN KEY
-- ============================================================================

-- Drop existing foreign key constraint on user_id
ALTER TABLE purdy_initiative_members
    DROP CONSTRAINT IF EXISTS purdy_initiative_members_user_id_fkey;

-- Add new foreign key referencing public.users
ALTER TABLE purdy_initiative_members
    ADD CONSTRAINT purdy_initiative_members_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

-- ============================================================================
-- FIX PURDY_CONVERSATIONS FOREIGN KEY
-- ============================================================================

-- Drop existing foreign key constraint on user_id
ALTER TABLE purdy_conversations
    DROP CONSTRAINT IF EXISTS purdy_conversations_user_id_fkey;

-- Add new foreign key referencing public.users
ALTER TABLE purdy_conversations
    ADD CONSTRAINT purdy_conversations_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES public.users(id);
