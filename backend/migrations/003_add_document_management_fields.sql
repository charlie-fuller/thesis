-- Migration: Add document management fields
-- Date: 2025-11-04
-- Description: Add fields for comprehensive document management and analytics

-- Add new columns to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS processing_error TEXT,
ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON documents(client_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);

-- Create trigger function to auto-update chunk_count
CREATE OR REPLACE FUNCTION update_document_chunk_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE documents
    SET chunk_count = (
      SELECT COUNT(*) FROM document_chunks WHERE document_id = NEW.document_id
    )
    WHERE id = NEW.document_id;
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE documents
    SET chunk_count = (
      SELECT COUNT(*) FROM document_chunks WHERE document_id = OLD.document_id
    )
    WHERE id = OLD.document_id;
    RETURN OLD;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update chunk_count on chunk insert/delete
DROP TRIGGER IF EXISTS update_chunk_count_trigger ON document_chunks;
CREATE TRIGGER update_chunk_count_trigger
AFTER INSERT OR DELETE ON document_chunks
FOR EACH ROW EXECUTE FUNCTION update_document_chunk_count();

-- Update existing documents to have correct chunk_count
UPDATE documents d
SET chunk_count = (
  SELECT COUNT(*) FROM document_chunks dc WHERE dc.document_id = d.id
);

-- Update processing_status based on existing 'processed' field
UPDATE documents
SET processing_status = CASE
  WHEN processed = true THEN 'completed'
  WHEN processed = false THEN 'pending'
  ELSE 'pending'
END;

-- Add comments for documentation
COMMENT ON COLUMN documents.processing_error IS 'Error message if document processing failed';
COMMENT ON COLUMN documents.chunk_count IS 'Number of chunks created from this document';
COMMENT ON COLUMN documents.last_accessed_at IS 'Timestamp of last RAG query that accessed this document';
COMMENT ON COLUMN documents.access_count IS 'Number of times this document was accessed in RAG queries';
COMMENT ON COLUMN documents.uploaded_by IS 'User ID who uploaded this document';
COMMENT ON COLUMN documents.processing_status IS 'Processing status: pending, processing, completed, failed';
