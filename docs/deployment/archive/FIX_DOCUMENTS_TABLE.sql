-- Quick Fix: Add processed column to documents table and reload PostgREST schema cache
-- Run this in your Supabase SQL Editor

-- Add the processed column if it doesn't exist
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

-- Add the processing_status column if it doesn't exist
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';

-- Add the processing_error column if it doesn't exist
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS processing_error TEXT;

-- Add the chunk_count column if it doesn't exist
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;

-- Add storage_url column if it doesn't exist
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS storage_url TEXT;

-- Add comments for documentation
COMMENT ON COLUMN public.documents.processed IS 'Whether document has been chunked and embedded';
COMMENT ON COLUMN public.documents.processing_status IS 'Processing status: pending, processing, completed, failed';
COMMENT ON COLUMN public.documents.storage_url IS 'Public URL to access the document in storage';

-- CRITICAL: Force PostgREST to reload its schema cache
-- This tells PostgREST about the new columns immediately
NOTIFY pgrst, 'reload schema';

-- Verify the columns were added
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'documents'
  AND column_name IN ('processed', 'processing_status', 'storage_url', 'chunk_count')
ORDER BY column_name;
