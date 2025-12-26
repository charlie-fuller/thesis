-- Migration: Add core document flag
-- Date: 2025-11-18
-- Description: Add flag to mark core/system documents that cannot be deleted

-- Add column to track core documents
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS is_core_document BOOLEAN DEFAULT false;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_documents_is_core ON documents(is_core_document);

-- Add comment
COMMENT ON COLUMN documents.is_core_document IS 'Marks documents referenced in system instructions that cannot be deleted';

-- Mark the current core documents for user d3ba5354-873a-435a-a36a-853373c4f6e5
-- These match the documents referenced in their system instructions
UPDATE documents
SET is_core_document = true
WHERE client_id = '4e94bfa4-d02c-4e52-b4d5-f0701f5c320b'
AND filename IN (
  'FOR_PAIGE.md',
  'DEPLOYMENT_AND_TESTING_GUIDE.md',
  'IMPLEMENTATION_CHECKLIST.md',
  'WEEK_2_SPRINT_SUMMARY.md',
  'README.md'
);
