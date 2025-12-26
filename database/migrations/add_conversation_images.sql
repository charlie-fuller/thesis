-- ============================================================================
-- CONVERSATION IMAGES TABLE MIGRATION
-- Adds support for storing generated images in conversations
-- Run this migration on existing Thesis database
-- ============================================================================

-- Create conversation_images table
CREATE TABLE IF NOT EXISTS conversation_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    aspect_ratio VARCHAR(10) NOT NULL DEFAULT '16:9', -- '1:1', '16:9', '9:16', '4:3'
    model VARCHAR(100) NOT NULL DEFAULT 'gemini-2.5-flash-image',
    storage_url TEXT NOT NULL, -- Supabase Storage URL
    storage_path TEXT, -- Path in storage bucket for easy deletion
    mime_type VARCHAR(50) DEFAULT 'image/png',
    file_size BIGINT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    -- Ensure valid aspect ratios
    CONSTRAINT valid_aspect_ratio CHECK (aspect_ratio IN ('1:1', '16:9', '9:16', '4:3'))
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_conversation_images_conversation_id ON conversation_images(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_images_message_id ON conversation_images(message_id);
CREATE INDEX IF NOT EXISTS idx_conversation_images_generated_at ON conversation_images(generated_at DESC);

-- Add comment for documentation
COMMENT ON TABLE conversation_images IS 'Stores generated images associated with conversations and messages';
COMMENT ON COLUMN conversation_images.aspect_ratio IS 'Image aspect ratio: 1:1 (square), 16:9 (landscape), 9:16 (portrait), 4:3 (standard)';
COMMENT ON COLUMN conversation_images.model IS 'AI model used: gemini-2.5-flash-image (fast) or gemini-3-pro-image-preview (quality)';
COMMENT ON COLUMN conversation_images.storage_url IS 'Public URL from Supabase Storage';
COMMENT ON COLUMN conversation_images.storage_path IS 'Internal storage path for management operations';

-- Enable Row Level Security
ALTER TABLE conversation_images ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view images in their own conversations
DROP POLICY IF EXISTS "Users can view images in own conversations" ON conversation_images;
CREATE POLICY "Users can view images in own conversations" ON conversation_images
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM conversations
        WHERE conversations.id = conversation_images.conversation_id
        AND conversations.user_id = auth.uid()
    )
);

-- RLS Policy: Users can insert images in their own conversations
DROP POLICY IF EXISTS "Users can create images in own conversations" ON conversation_images;
CREATE POLICY "Users can create images in own conversations" ON conversation_images
FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM conversations
        WHERE conversations.id = conversation_images.conversation_id
        AND conversations.user_id = auth.uid()
    )
);

-- RLS Policy: Users can delete images in their own conversations
DROP POLICY IF EXISTS "Users can delete own conversation images" ON conversation_images;
CREATE POLICY "Users can delete own conversation images" ON conversation_images
FOR DELETE USING (
    EXISTS (
        SELECT 1 FROM conversations
        WHERE conversations.id = conversation_images.conversation_id
        AND conversations.user_id = auth.uid()
    )
);

-- Function to count images in a conversation (for limit enforcement)
CREATE OR REPLACE FUNCTION count_conversation_images(p_conversation_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    image_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO image_count
    FROM conversation_images
    WHERE conversation_id = p_conversation_id;

    RETURN image_count;
END;
$$;

-- Function to get recent image suggestion count (for throttling)
CREATE OR REPLACE FUNCTION count_recent_suggestions(
    p_conversation_id UUID,
    p_message_count INTEGER DEFAULT 5
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    suggestion_count INTEGER;
BEGIN
    -- Count messages with image_suggestion metadata in last N messages
    SELECT COUNT(*) INTO suggestion_count
    FROM (
        SELECT id, metadata
        FROM messages
        WHERE conversation_id = p_conversation_id
        ORDER BY created_at DESC
        LIMIT p_message_count
    ) recent_messages
    WHERE metadata->>'image_suggestion' IS NOT NULL;

    RETURN suggestion_count;
END;
$$;

-- ============================================================================
-- STORAGE BUCKET SETUP (Run in Supabase Dashboard SQL Editor)
-- ============================================================================
-- Note: This should be run separately in Supabase dashboard if bucket doesn't exist
--
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('conversation-images', 'conversation-images', true)
-- ON CONFLICT (id) DO NOTHING;
--
-- CREATE POLICY "Users can upload images to own conversations"
-- ON storage.objects FOR INSERT
-- WITH CHECK (
--     bucket_id = 'conversation-images' AND
--     auth.role() = 'authenticated'
-- );
--
-- CREATE POLICY "Anyone can view conversation images"
-- ON storage.objects FOR SELECT
-- USING (bucket_id = 'conversation-images');
--
-- CREATE POLICY "Users can delete own conversation images"
-- ON storage.objects FOR DELETE
-- USING (
--     bucket_id = 'conversation-images' AND
--     auth.uid()::text = (storage.foldername(name))[1]
-- );

-- ============================================================================
-- DONE!
-- ============================================================================
