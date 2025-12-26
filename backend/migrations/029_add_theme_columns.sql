-- Migration: Add missing theme setting columns
-- Adds header customization, panel styling, and additional color options

-- Add button text colors
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS color_text_on_primary VARCHAR(7) DEFAULT '#ffffff';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS color_text_on_secondary VARCHAR(7) DEFAULT '#1d1d22';

-- Add font weight controls
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS font_weight_heading VARCHAR(10) DEFAULT '700';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS font_weight_body VARCHAR(10) DEFAULT '400';

-- Add panel/card styling
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS panel_border_width VARCHAR(10) DEFAULT '1px';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS panel_border_color VARCHAR(7) DEFAULT '#e5e5e9';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS panel_shadow_size VARCHAR(10) DEFAULT '1px';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS panel_shadow_color VARCHAR(20) DEFAULT 'rgba(0, 0, 0, 0.1)';

-- Add header/nav bar customization
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS header_logo_url TEXT;
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS header_bg_color VARCHAR(7) DEFAULT '#ffffff';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS header_title_color VARCHAR(7) DEFAULT '#14b8a6';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS header_nav_color VARCHAR(7) DEFAULT '#6b7280';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS header_nav_active_color VARCHAR(7) DEFAULT '#14b8a6';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS header_font_size VARCHAR(10) DEFAULT '20px';
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS header_height VARCHAR(10) DEFAULT '64px';

-- Add page title font size
ALTER TABLE theme_settings ADD COLUMN IF NOT EXISTS page_title_font_size VARCHAR(10) DEFAULT '32px';

-- Update existing default row if it exists
UPDATE theme_settings
SET
    color_text_on_primary = COALESCE(color_text_on_primary, '#ffffff'),
    color_text_on_secondary = COALESCE(color_text_on_secondary, '#1d1d22'),
    font_weight_heading = COALESCE(font_weight_heading, '700'),
    font_weight_body = COALESCE(font_weight_body, '400'),
    panel_border_width = COALESCE(panel_border_width, '1px'),
    panel_border_color = COALESCE(panel_border_color, '#e5e5e9'),
    panel_shadow_size = COALESCE(panel_shadow_size, '1px'),
    panel_shadow_color = COALESCE(panel_shadow_color, 'rgba(0, 0, 0, 0.1)'),
    header_bg_color = COALESCE(header_bg_color, '#ffffff'),
    header_title_color = COALESCE(header_title_color, '#14b8a6'),
    header_nav_color = COALESCE(header_nav_color, '#6b7280'),
    header_nav_active_color = COALESCE(header_nav_active_color, '#14b8a6'),
    header_font_size = COALESCE(header_font_size, '20px'),
    header_height = COALESCE(header_height, '64px'),
    page_title_font_size = COALESCE(page_title_font_size, '32px')
WHERE client_id = '00000000-0000-0000-0000-000000000001';
