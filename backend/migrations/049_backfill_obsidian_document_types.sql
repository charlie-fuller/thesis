-- ============================================================================
-- MIGRATION: Backfill document_type for Obsidian-synced documents
-- Description: Classifies existing documents that weren't classified during sync
--              Adds support for Granola meeting notes (Person1 __ Person2 format)
-- Author: Claude
-- Date: 2026-01-29
-- ============================================================================

-- Granola meeting notes (contain " __ " separator, e.g., "Charlie __ Dave.md")
-- These are auto-transcribed meetings from Granola.ai
UPDATE documents SET
    document_type = 'transcript',
    primary_use_case = 'action_source',
    classification_method = 'filename',
    classification_confidence = 0.85
WHERE filename LIKE '% __ %'
  AND document_type IS NULL;

-- Re-run the original classification rules for any documents that were missed
-- (e.g., documents synced after migration 027 ran but before this code fix)

-- Transcripts
UPDATE documents SET
    document_type = 'transcript',
    primary_use_case = 'action_source',
    classification_method = 'filename',
    classification_confidence = 0.9
WHERE (filename ILIKE '%transcript%' OR filename ILIKE '%-transcript.md')
  AND document_type IS NULL;

-- Meeting notes
UPDATE documents SET
    document_type = 'notes',
    primary_use_case = 'action_source',
    classification_method = 'filename',
    classification_confidence = 0.8
WHERE (filename ILIKE '%meeting-notes%' OR filename ILIKE '%meeting notes%'
       OR filename ILIKE '%notes.md' OR filename ILIKE '%meeting_notes%')
  AND document_type IS NULL;

-- Instructions/guides
UPDATE documents SET
    document_type = 'instructions',
    primary_use_case = 'guidance',
    classification_method = 'filename',
    classification_confidence = 0.85
WHERE (filename ILIKE '%instructions%' OR filename ILIKE '%guide%'
       OR filename ILIKE '%playbook%' OR filename ILIKE '%how-to%' OR filename ILIKE '%howto%')
  AND document_type IS NULL;

-- Reports/analysis
UPDATE documents SET
    document_type = 'report',
    primary_use_case = 'knowledge',
    classification_method = 'filename',
    classification_confidence = 0.8
WHERE (filename ILIKE '%report%' OR filename ILIKE '%analysis%'
       OR filename ILIKE '%whitepaper%' OR filename ILIKE '%research%')
  AND document_type IS NULL;

-- Presentations
UPDATE documents SET
    document_type = 'presentation',
    primary_use_case = 'knowledge',
    classification_method = 'filename',
    classification_confidence = 0.9
WHERE (filename ILIKE '%.pptx' OR filename ILIKE '%.ppt'
       OR filename ILIKE '%slides%' OR filename ILIKE '%deck%' OR filename ILIKE '%presentation%')
  AND document_type IS NULL;

-- Spreadsheets
UPDATE documents SET
    document_type = 'spreadsheet',
    primary_use_case = 'evidence',
    classification_method = 'filename',
    classification_confidence = 0.9
WHERE (filename ILIKE '%.csv' OR filename ILIKE '%.xlsx' OR filename ILIKE '%.xls')
  AND document_type IS NULL;

-- Path-based classification for documents in meeting/transcript folders
-- (for Obsidian-synced documents, check obsidian_file_path)
UPDATE documents SET
    document_type = 'transcript',
    primary_use_case = 'action_source',
    classification_method = 'path',
    classification_confidence = 0.7
WHERE (obsidian_file_path ILIKE 'meetings/%'
       OR obsidian_file_path ILIKE 'transcripts/%'
       OR obsidian_file_path ILIKE 'calls/%'
       OR obsidian_file_path ILIKE '%/meetings/%'
       OR obsidian_file_path ILIKE '%/transcripts/%')
  AND document_type IS NULL;

UPDATE documents SET
    document_type = 'notes',
    primary_use_case = 'context',
    classification_method = 'path',
    classification_confidence = 0.6
WHERE (obsidian_file_path ILIKE 'notes/%'
       OR obsidian_file_path ILIKE 'journal/%'
       OR obsidian_file_path ILIKE '%/notes/%')
  AND document_type IS NULL;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- After running this migration:
-- 1. Existing Granola meeting notes are classified as transcripts
-- 2. Other unclassified documents are classified by filename/path patterns
-- 3. Future syncs will auto-classify via the updated obsidian_sync.py code
