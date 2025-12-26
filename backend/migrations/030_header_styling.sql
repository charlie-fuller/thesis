-- Migration: Add Header Styling and Logo to Theme Settings
-- Allows customization of header appearance including logo, colors, and height

-- Add logo URL (stored in Supabase Storage)
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS header_logo_url TEXT DEFAULT NULL;

-- Add header background color
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS header_bg_color VARCHAR(7) DEFAULT '#111111';

-- Add header text color
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS header_text_color VARCHAR(7) DEFAULT '#ffffff';

-- Add header font size
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS header_font_size VARCHAR(10) DEFAULT '20px';

-- Add header height
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS header_height VARCHAR(10) DEFAULT '64px';

-- Add comments
COMMENT ON COLUMN theme_settings.header_logo_url IS 'URL to the uploaded logo image';
COMMENT ON COLUMN theme_settings.header_bg_color IS 'Background color for the header/navigation bar';
COMMENT ON COLUMN theme_settings.header_text_color IS 'Text color for the header/navigation bar';
COMMENT ON COLUMN theme_settings.header_font_size IS 'Font size for header text (e.g., 16px, 20px)';
COMMENT ON COLUMN theme_settings.header_height IS 'Height of the header bar (e.g., 48px, 64px, 80px)';
