-- Migration: Theme Settings
-- Allows admins to customize the app's visual appearance

CREATE TABLE IF NOT EXISTS theme_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Brand colors
    color_primary VARCHAR(7) DEFAULT '#6366f1',        -- Primary brand color
    color_primary_hover VARCHAR(7) DEFAULT '#4f46e5',  -- Primary hover state
    color_secondary VARCHAR(7) DEFAULT '#8b5cf6',      -- Secondary/accent color

    -- Background colors
    color_bg_page VARCHAR(7) DEFAULT '#0a0a0a',        -- Page background
    color_bg_card VARCHAR(7) DEFAULT '#111111',        -- Card/panel background
    color_bg_hover VARCHAR(7) DEFAULT '#1a1a1a',       -- Hover state background

    -- Text colors
    color_text_primary VARCHAR(7) DEFAULT '#ffffff',   -- Primary text
    color_text_secondary VARCHAR(7) DEFAULT '#a1a1aa', -- Secondary/muted text
    color_text_muted VARCHAR(7) DEFAULT '#71717a',     -- Muted/disabled text

    -- Border colors
    color_border VARCHAR(7) DEFAULT '#27272a',         -- Default borders
    color_border_focus VARCHAR(7) DEFAULT '#6366f1',   -- Focus state borders

    -- Status colors
    color_success VARCHAR(7) DEFAULT '#22c55e',
    color_warning VARCHAR(7) DEFAULT '#f59e0b',
    color_error VARCHAR(7) DEFAULT '#ef4444',

    -- Typography
    font_family_heading VARCHAR(100) DEFAULT 'Inter, system-ui, sans-serif',
    font_family_body VARCHAR(100) DEFAULT 'Inter, system-ui, sans-serif',
    font_size_base VARCHAR(10) DEFAULT '16px',

    -- Border radius
    border_radius_sm VARCHAR(10) DEFAULT '0.25rem',
    border_radius_md VARCHAR(10) DEFAULT '0.5rem',
    border_radius_lg VARCHAR(10) DEFAULT '0.75rem',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(client_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_theme_settings_client_id ON theme_settings(client_id);

-- Insert default theme for the default client
INSERT INTO theme_settings (client_id)
VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (client_id) DO NOTHING;

-- Add RLS policies
ALTER TABLE theme_settings ENABLE ROW LEVEL SECURITY;

-- Admins can manage theme settings
CREATE POLICY "Admins can manage theme settings"
ON theme_settings
FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.role = 'admin'
        AND users.client_id = theme_settings.client_id
    )
);

-- All authenticated users can read theme settings
CREATE POLICY "Users can read theme settings"
ON theme_settings
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.client_id = theme_settings.client_id
    )
);
