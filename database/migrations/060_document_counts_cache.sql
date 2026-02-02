-- Migration: Document counts cache for performance
-- Caches document counts by source platform to avoid slow exact count queries

-- Create the counts cache table
CREATE TABLE IF NOT EXISTS user_document_counts (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  total_count INTEGER DEFAULT 0,
  google_drive_count INTEGER DEFAULT 0,
  notion_count INTEGER DEFAULT 0,
  obsidian_count INTEGER DEFAULT 0,
  upload_count INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE user_document_counts ENABLE ROW LEVEL SECURITY;

-- Users can only see their own counts
CREATE POLICY "Users can view own document counts"
  ON user_document_counts
  FOR SELECT
  USING (auth.uid() = user_id);

-- System can update counts (via trigger function with SECURITY DEFINER)
CREATE POLICY "System can manage document counts"
  ON user_document_counts
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Function to update document counts for a user
CREATE OR REPLACE FUNCTION update_user_document_counts()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
  v_user_id UUID;
  v_source_platform TEXT;
BEGIN
  -- Determine which user and source platform to update
  IF TG_OP = 'DELETE' THEN
    v_user_id := OLD.uploaded_by;
    v_source_platform := COALESCE(OLD.source_platform, 'upload');
  ELSE
    v_user_id := NEW.uploaded_by;
    v_source_platform := COALESCE(NEW.source_platform, 'upload');
  END IF;

  -- Skip if no user ID
  IF v_user_id IS NULL THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  -- Upsert the counts - recalculate all counts for the user
  INSERT INTO user_document_counts (user_id, total_count, google_drive_count, notion_count, obsidian_count, upload_count, updated_at)
  SELECT
    v_user_id,
    COUNT(*),
    COUNT(*) FILTER (WHERE source_platform = 'google_drive'),
    COUNT(*) FILTER (WHERE source_platform = 'notion'),
    COUNT(*) FILTER (WHERE source_platform = 'obsidian'),
    COUNT(*) FILTER (WHERE source_platform IS NULL OR source_platform = 'upload'),
    NOW()
  FROM documents
  WHERE uploaded_by = v_user_id
  ON CONFLICT (user_id) DO UPDATE SET
    total_count = EXCLUDED.total_count,
    google_drive_count = EXCLUDED.google_drive_count,
    notion_count = EXCLUDED.notion_count,
    obsidian_count = EXCLUDED.obsidian_count,
    upload_count = EXCLUDED.upload_count,
    updated_at = NOW();

  RETURN COALESCE(NEW, OLD);
END;
$$;

-- Create trigger on documents table
DROP TRIGGER IF EXISTS update_document_counts_trigger ON documents;
CREATE TRIGGER update_document_counts_trigger
  AFTER INSERT OR DELETE ON documents
  FOR EACH ROW
  EXECUTE FUNCTION update_user_document_counts();

-- Also trigger on source_platform update (in case document is re-categorized)
DROP TRIGGER IF EXISTS update_document_counts_on_update_trigger ON documents;
CREATE TRIGGER update_document_counts_on_update_trigger
  AFTER UPDATE OF source_platform ON documents
  FOR EACH ROW
  WHEN (OLD.source_platform IS DISTINCT FROM NEW.source_platform)
  EXECUTE FUNCTION update_user_document_counts();

-- Initialize counts for all existing users
INSERT INTO user_document_counts (user_id, total_count, google_drive_count, notion_count, obsidian_count, upload_count, updated_at)
SELECT
  uploaded_by,
  COUNT(*),
  COUNT(*) FILTER (WHERE source_platform = 'google_drive'),
  COUNT(*) FILTER (WHERE source_platform = 'notion'),
  COUNT(*) FILTER (WHERE source_platform = 'obsidian'),
  COUNT(*) FILTER (WHERE source_platform IS NULL OR source_platform = 'upload'),
  NOW()
FROM documents
WHERE uploaded_by IS NOT NULL
GROUP BY uploaded_by
ON CONFLICT (user_id) DO UPDATE SET
  total_count = EXCLUDED.total_count,
  google_drive_count = EXCLUDED.google_drive_count,
  notion_count = EXCLUDED.notion_count,
  obsidian_count = EXCLUDED.obsidian_count,
  upload_count = EXCLUDED.upload_count,
  updated_at = NOW();

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_document_counts_user_id ON user_document_counts(user_id);

-- Add comment
COMMENT ON TABLE user_document_counts IS 'Cached document counts by source platform for performance. Updated via triggers on documents table.';
