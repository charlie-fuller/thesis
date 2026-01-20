-- ============================================================================
-- MIGRATION: Add document type classification
-- Description: Adds document_type and use_case columns to classify documents
--              for smarter RAG retrieval based on query intent
-- Author: Claude
-- Date: 2026-01-20
-- ============================================================================

-- Document type enum - what kind of document is this?
CREATE TYPE document_type AS ENUM (
    'transcript',      -- Meeting transcripts, call recordings, interviews
    'article',         -- Published articles, blog posts, news
    'report',          -- Research reports, analysis documents, whitepapers
    'instructions',    -- How-to guides, manuals, agent instructions, playbooks
    'notes',           -- Personal notes, meeting notes, summaries
    'email',           -- Email threads, correspondence
    'presentation',    -- Slides, decks
    'spreadsheet',     -- Data files, CSVs, Excel
    'code',            -- Source code, scripts, configs
    'reference',       -- Reference material, documentation, specs
    'other'            -- Uncategorized
);

-- Use case enum - how is this document likely to be used?
CREATE TYPE document_use_case AS ENUM (
    'action_source',   -- Contains action items, tasks, follow-ups (transcripts, meeting notes)
    'knowledge',       -- Reference knowledge, facts, background info (articles, reports)
    'guidance',        -- How to do things, instructions (playbooks, guides)
    'evidence',        -- Proof points, examples, case studies
    'context',         -- Background context, history, relationships
    'learning'         -- Educational content, training material
);

-- Add columns to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_type document_type;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS primary_use_case document_use_case;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS classification_confidence FLOAT DEFAULT 0.0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS classification_method VARCHAR(50); -- 'auto', 'manual', 'filename'

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_primary_use_case ON documents(primary_use_case);

-- Add comments
COMMENT ON COLUMN documents.document_type IS 'Classification of what kind of document this is (transcript, article, report, etc.)';
COMMENT ON COLUMN documents.primary_use_case IS 'How this document is primarily intended to be used in queries';
COMMENT ON COLUMN documents.classification_confidence IS 'Confidence score (0-1) for auto-classification';
COMMENT ON COLUMN documents.classification_method IS 'How the document was classified: auto, manual, or filename-based';

-- ============================================================================
-- Auto-classification rules based on filename patterns
-- ============================================================================

-- Update existing documents based on filename patterns
UPDATE documents SET
    document_type = 'transcript',
    primary_use_case = 'action_source',
    classification_method = 'filename',
    classification_confidence = 0.9
WHERE (filename ILIKE '%transcript%' OR filename ILIKE '%-transcript.md')
  AND document_type IS NULL;

UPDATE documents SET
    document_type = 'notes',
    primary_use_case = 'action_source',
    classification_method = 'filename',
    classification_confidence = 0.8
WHERE (filename ILIKE '%meeting-notes%' OR filename ILIKE '%meeting notes%' OR filename ILIKE '%notes.md')
  AND document_type IS NULL;

UPDATE documents SET
    document_type = 'instructions',
    primary_use_case = 'guidance',
    classification_method = 'filename',
    classification_confidence = 0.85
WHERE (filename ILIKE '%instructions%' OR filename ILIKE '%guide%' OR filename ILIKE '%playbook%' OR filename ILIKE '%how-to%')
  AND document_type IS NULL;

UPDATE documents SET
    document_type = 'report',
    primary_use_case = 'knowledge',
    classification_method = 'filename',
    classification_confidence = 0.8
WHERE (filename ILIKE '%report%' OR filename ILIKE '%analysis%' OR filename ILIKE '%whitepaper%' OR filename ILIKE '%research%')
  AND document_type IS NULL;

UPDATE documents SET
    document_type = 'presentation',
    primary_use_case = 'knowledge',
    classification_method = 'filename',
    classification_confidence = 0.9
WHERE (filename ILIKE '%.pptx' OR filename ILIKE '%.ppt' OR filename ILIKE '%slides%' OR filename ILIKE '%deck%')
  AND document_type IS NULL;

UPDATE documents SET
    document_type = 'spreadsheet',
    primary_use_case = 'evidence',
    classification_method = 'filename',
    classification_confidence = 0.9
WHERE (filename ILIKE '%.csv' OR filename ILIKE '%.xlsx' OR filename ILIKE '%.xls')
  AND document_type IS NULL;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- After running this migration:
-- 1. Existing documents with recognizable filenames are auto-classified
-- 2. New documents should be classified during upload (via LLM or filename rules)
-- 3. RAG search can filter/boost by document_type and primary_use_case
