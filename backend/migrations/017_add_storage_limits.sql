-- Migration: Add storage limits to users table
-- Date: 2025-11-11
-- Description: Add storage_quota and storage_used fields to track user storage limits

-- Add storage_quota column to users table (default 500MB)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS storage_quota BIGINT DEFAULT 524288000; -- 500MB in bytes

-- Add storage_used column to users table (default 0)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS storage_used BIGINT DEFAULT 0;

-- Create index on storage_used for faster queries
CREATE INDEX IF NOT EXISTS idx_users_storage_used ON users(storage_used);

-- Add constraint to ensure storage_used is never negative
ALTER TABLE users
ADD CONSTRAINT chk_storage_used_positive CHECK (storage_used >= 0);

-- Add constraint to ensure storage_quota is never negative
ALTER TABLE users
ADD CONSTRAINT chk_storage_quota_positive CHECK (storage_quota >= 0);

COMMENT ON COLUMN users.storage_quota IS 'Maximum storage allowed for user in bytes (default 500MB)';
COMMENT ON COLUMN users.storage_used IS 'Current storage used by user in bytes';

-- Create function to calculate user storage
CREATE OR REPLACE FUNCTION calculate_user_storage(user_id_param UUID)
RETURNS BIGINT AS $$
DECLARE
    total_size BIGINT;
BEGIN
    SELECT COALESCE(SUM(file_size), 0)
    INTO total_size
    FROM documents
    WHERE uploaded_by = user_id_param;

    RETURN total_size;
END;
$$ LANGUAGE plpgsql;

-- Create function to update user storage_used
CREATE OR REPLACE FUNCTION update_user_storage()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        UPDATE users
        SET storage_used = storage_used - OLD.file_size
        WHERE id = OLD.uploaded_by;
        RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
        UPDATE users
        SET storage_used = storage_used + NEW.file_size
        WHERE id = NEW.uploaded_by;
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        UPDATE users
        SET storage_used = storage_used - OLD.file_size + NEW.file_size
        WHERE id = NEW.uploaded_by;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update storage_used when documents are inserted/updated/deleted
DROP TRIGGER IF EXISTS trg_update_user_storage ON documents;
CREATE TRIGGER trg_update_user_storage
AFTER INSERT OR UPDATE OR DELETE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_user_storage();

-- Initialize storage_used for existing users
UPDATE users u
SET storage_used = calculate_user_storage(u.id)
WHERE storage_used IS NULL OR storage_used = 0;
