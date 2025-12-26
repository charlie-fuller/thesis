-- Migration 020: Add mime_type column to documents table
-- Date: 2025-11-18
-- Purpose: Fix PostgREST schema cache error for mime_type column

-- Add mime_type column (optional field for storing content type)
ALTER TABLE public.documents
ADD COLUMN IF NOT EXISTS mime_type TEXT;

COMMENT ON COLUMN public.documents.mime_type IS 'MIME type of the document (e.g., text/plain, application/pdf) - optional field';

-- No data migration needed - column is optional
