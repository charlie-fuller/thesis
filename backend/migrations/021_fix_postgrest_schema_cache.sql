-- Migration 021: Fix PostgREST Schema Cache
-- Date: 2025-11-18
-- Purpose: Ensure all documents table columns exist and reload PostgREST schema cache

-- ============================================================================
-- STEP 1: Ensure all core columns exist
-- ============================================================================

-- Core document identification and storage
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
ADD COLUMN IF NOT EXISTS client_id UUID REFERENCES public.clients(id),
ADD COLUMN IF NOT EXISTS filename TEXT NOT NULL,
ADD COLUMN IF NOT EXISTS storage_path TEXT,
ADD COLUMN IF NOT EXISTS file_size BIGINT,
ADD COLUMN IF NOT EXISTS file_type TEXT,
ADD COLUMN IF NOT EXISTS mime_type TEXT;

-- Processing and status
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS processing_error TEXT,
ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;

-- User and timing information
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES public.users(id),
ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0;

-- Google Drive integration
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS google_drive_id TEXT,
ADD COLUMN IF NOT EXISTS google_drive_modified_time TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE;

-- Notion integration
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS notion_page_id TEXT,
ADD COLUMN IF NOT EXISTS notion_last_edited_time TIMESTAMP WITH TIME ZONE;

-- Source tracking
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'upload';

-- ============================================================================
-- STEP 2: Add column comments for documentation
-- ============================================================================

COMMENT ON COLUMN public.documents.storage_path IS 'Path in Supabase Storage bucket';
COMMENT ON COLUMN public.documents.mime_type IS 'MIME type of the document (e.g., text/plain, application/pdf)';
COMMENT ON COLUMN public.documents.processed IS 'Whether document has been chunked and embedded';
COMMENT ON COLUMN public.documents.processing_status IS 'Processing status: pending, processing, completed, failed';
COMMENT ON COLUMN public.documents.uploaded_by IS 'User ID who uploaded this document';
COMMENT ON COLUMN public.documents.source IS 'Source of document: upload, google_drive, or notion';

-- ============================================================================
-- STEP 3: Force PostgREST to reload schema cache
-- ============================================================================

-- This NOTIFY command tells PostgREST to reload its schema cache
-- It must be executed AFTER all schema changes
NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- List all columns in documents table
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'documents'
ORDER BY ordinal_position;
