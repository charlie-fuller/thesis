-- Migration: Add avatar_url column to users table
-- Date: 2025-11-03
-- Description: Add support for user profile avatars

-- Add avatar_url column to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Create index on avatar_url for faster queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_users_avatar_url ON users(avatar_url);

-- Create avatars storage bucket (run this in Supabase dashboard SQL editor or via CLI)
-- Note: Storage buckets must be created via Supabase dashboard or API
-- Run this SQL in Supabase SQL Editor:
/*
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT (id) DO NOTHING;

-- Set up storage policies for avatars bucket
CREATE POLICY "Avatar uploads are allowed for authenticated users"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'avatars');

CREATE POLICY "Avatar updates are allowed for authenticated users"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'avatars');

CREATE POLICY "Avatar deletes are allowed for authenticated users"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'avatars');

CREATE POLICY "Avatars are publicly accessible"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'avatars');
*/

-- Update existing users to have NULL avatar_url (already default)
-- No action needed

COMMENT ON COLUMN users.avatar_url IS 'URL to user profile avatar image stored in Supabase Storage';
