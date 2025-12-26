-- Migration 022: Add metadata column to messages table
-- Date: 2025-12-14
-- Purpose: Add JSONB metadata column to messages table for image suggestions and other metadata
--          This fixes image generation feature which requires metadata storage

-- ============================================================================
-- STEP 1: Add metadata column to messages table
-- ============================================================================

ALTER TABLE public.messages
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT NULL;

-- ============================================================================
-- STEP 2: Add column comment for documentation
-- ============================================================================

COMMENT ON COLUMN public.messages.metadata IS 'JSON metadata for message (e.g., image_suggestion, has_image, image_id)';

-- ============================================================================
-- STEP 3: Create index for faster JSON queries
-- ============================================================================

-- Index for querying messages with image suggestions
CREATE INDEX IF NOT EXISTS idx_messages_metadata_image_suggestion
ON public.messages
USING GIN ((metadata->'image_suggestion'))
WHERE metadata->'image_suggestion' IS NOT NULL;

-- ============================================================================
-- STEP 4: Force PostgREST to reload schema cache
-- ============================================================================

-- This NOTIFY command tells PostgREST to reload its schema cache
-- It must be executed AFTER all schema changes
NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify the metadata column was added
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'messages'
  AND column_name = 'metadata';
