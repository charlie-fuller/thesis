-- Migration: Fix storage calculation to exclude external sources
-- Date: 2025-11-12
-- Description: Modify trigger to only count storage for direct uploads, not Google Drive or Notion documents

-- Drop the existing trigger
DROP TRIGGER IF EXISTS trg_update_user_storage ON documents;

-- Recreate function to update user storage_used (excluding external sources)
CREATE OR REPLACE FUNCTION update_user_storage()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Only decrement storage for documents that are NOT from external sources
        IF OLD.source_platform IS NULL OR OLD.source_platform NOT IN ('google_drive', 'notion') THEN
            UPDATE users
            SET storage_used = storage_used - COALESCE(OLD.file_size, 0)
            WHERE id = OLD.uploaded_by;
        END IF;
        RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
        -- Only increment storage for documents that are NOT from external sources
        IF NEW.source_platform IS NULL OR NEW.source_platform NOT IN ('google_drive', 'notion') THEN
            UPDATE users
            SET storage_used = storage_used + COALESCE(NEW.file_size, 0)
            WHERE id = NEW.uploaded_by;
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Handle updates carefully based on source_platform changes
        -- If source changed from external to direct or vice versa, adjust accordingly
        DECLARE
            old_is_external BOOLEAN := OLD.source_platform IN ('google_drive', 'notion');
            new_is_external BOOLEAN := NEW.source_platform IN ('google_drive', 'notion');
        BEGIN
            IF NOT old_is_external AND NOT new_is_external THEN
                -- Both direct uploads - adjust by difference
                UPDATE users
                SET storage_used = storage_used - COALESCE(OLD.file_size, 0) + COALESCE(NEW.file_size, 0)
                WHERE id = NEW.uploaded_by;
            ELSIF old_is_external AND NOT new_is_external THEN
                -- Changed from external to direct - add new size
                UPDATE users
                SET storage_used = storage_used + COALESCE(NEW.file_size, 0)
                WHERE id = NEW.uploaded_by;
            ELSIF NOT old_is_external AND new_is_external THEN
                -- Changed from direct to external - subtract old size
                UPDATE users
                SET storage_used = storage_used - COALESCE(OLD.file_size, 0)
                WHERE id = NEW.uploaded_by;
            END IF;
            -- If both external, do nothing
        END;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Recreate trigger
CREATE TRIGGER trg_update_user_storage
AFTER INSERT OR UPDATE OR DELETE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_user_storage();

-- Recalculate storage_used for all users to fix any inconsistencies
-- Only count documents that are NOT from external sources
CREATE OR REPLACE FUNCTION recalculate_all_user_storage()
RETURNS void AS $$
BEGIN
    UPDATE users u
    SET storage_used = COALESCE(
        (SELECT SUM(file_size)
         FROM documents d
         WHERE d.uploaded_by = u.id
         AND (d.source_platform IS NULL OR d.source_platform NOT IN ('google_drive', 'notion'))),
        0
    );
END;
$$ LANGUAGE plpgsql;

-- Run the recalculation
SELECT recalculate_all_user_storage();

COMMENT ON FUNCTION update_user_storage() IS 'Automatically updates user storage_used, excluding external sources (Google Drive, Notion)';
COMMENT ON FUNCTION recalculate_all_user_storage() IS 'Recalculates storage_used for all users, excluding external sources';
