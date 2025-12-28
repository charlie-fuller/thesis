-- ============================================================================
-- MEETING ROOMS FEATURE
-- Multi-agent conversation rooms for cross-functional collaboration
-- and stakeholder meeting preparation
-- ============================================================================

-- ============================================================================
-- MEETING ROOMS TABLE
-- Container for multi-agent conversations
-- ============================================================================

CREATE TABLE IF NOT EXISTS meeting_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Meeting metadata
    title VARCHAR(500) NOT NULL,
    description TEXT,
    meeting_type VARCHAR(50) NOT NULL DEFAULT 'collaboration',  -- 'collaboration', 'meeting_prep'
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'completed', 'archived'

    -- Configuration
    config JSONB DEFAULT '{}',  -- {turn_mode: 'coordinated', etc.}

    -- Tracking
    total_tokens_used INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- MEETING ROOM PARTICIPANTS
-- Tracks which agents are participating in each meeting
-- ============================================================================

CREATE TABLE IF NOT EXISTS meeting_room_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    -- Participant configuration
    role_description TEXT,  -- For meeting prep: "Playing skeptical CFO"
    priority INTEGER DEFAULT 0,  -- Order of speaking preference

    -- Stats
    turns_taken INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(meeting_room_id, agent_id)
);

-- ============================================================================
-- MEETING ROOM MESSAGES
-- Messages with agent attribution
-- ============================================================================

CREATE TABLE IF NOT EXISTS meeting_room_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,

    -- Message attribution
    role VARCHAR(50) NOT NULL,  -- 'user', 'agent', 'system'
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,  -- NULL for user/system messages
    agent_name VARCHAR(100),  -- Denormalized for display efficiency
    agent_display_name VARCHAR(200),  -- Denormalized for display efficiency

    -- Content
    content TEXT NOT NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',  -- {tokens: {input, output}, reasoning: "..."}
    turn_number INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_meeting_rooms_client_id ON meeting_rooms(client_id);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_user_id ON meeting_rooms(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_status ON meeting_rooms(status);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_created_at ON meeting_rooms(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_meeting_room_participants_meeting_id ON meeting_room_participants(meeting_room_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_participants_agent_id ON meeting_room_participants(agent_id);

CREATE INDEX IF NOT EXISTS idx_meeting_room_messages_meeting_id ON meeting_room_messages(meeting_room_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_messages_created_at ON meeting_room_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_meeting_room_messages_agent_id ON meeting_room_messages(agent_id);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE meeting_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_room_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_room_messages ENABLE ROW LEVEL SECURITY;

-- Meeting rooms policies
DROP POLICY IF EXISTS "Users can view their own meeting rooms" ON meeting_rooms;
CREATE POLICY "Users can view their own meeting rooms" ON meeting_rooms
    FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can create meeting rooms" ON meeting_rooms;
CREATE POLICY "Users can create meeting rooms" ON meeting_rooms
    FOR INSERT WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update their own meeting rooms" ON meeting_rooms;
CREATE POLICY "Users can update their own meeting rooms" ON meeting_rooms
    FOR UPDATE USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can delete their own meeting rooms" ON meeting_rooms;
CREATE POLICY "Users can delete their own meeting rooms" ON meeting_rooms
    FOR DELETE USING (user_id = auth.uid());

-- Participants follow meeting room access
DROP POLICY IF EXISTS "Users can view participants in their meetings" ON meeting_room_participants;
CREATE POLICY "Users can view participants in their meetings" ON meeting_room_participants
    FOR SELECT USING (
        meeting_room_id IN (SELECT id FROM meeting_rooms WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can manage participants in their meetings" ON meeting_room_participants;
CREATE POLICY "Users can manage participants in their meetings" ON meeting_room_participants
    FOR ALL USING (
        meeting_room_id IN (SELECT id FROM meeting_rooms WHERE user_id = auth.uid())
    );

-- Messages follow meeting room access
DROP POLICY IF EXISTS "Users can view messages in their meetings" ON meeting_room_messages;
CREATE POLICY "Users can view messages in their meetings" ON meeting_room_messages
    FOR SELECT USING (
        meeting_room_id IN (SELECT id FROM meeting_rooms WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can create messages in their meetings" ON meeting_room_messages;
CREATE POLICY "Users can create messages in their meetings" ON meeting_room_messages
    FOR INSERT WITH CHECK (
        meeting_room_id IN (SELECT id FROM meeting_rooms WHERE user_id = auth.uid())
    );

-- ============================================================================
-- SERVICE ROLE POLICIES
-- Backend needs full access for orchestration
-- ============================================================================

DROP POLICY IF EXISTS "Service role has full access to meeting_rooms" ON meeting_rooms;
CREATE POLICY "Service role has full access to meeting_rooms" ON meeting_rooms
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role has full access to meeting_room_participants" ON meeting_room_participants;
CREATE POLICY "Service role has full access to meeting_room_participants" ON meeting_room_participants
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role has full access to meeting_room_messages" ON meeting_room_messages;
CREATE POLICY "Service role has full access to meeting_room_messages" ON meeting_room_messages
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION update_meeting_rooms_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS meeting_rooms_updated_at ON meeting_rooms;
CREATE TRIGGER meeting_rooms_updated_at
    BEFORE UPDATE ON meeting_rooms
    FOR EACH ROW
    EXECUTE FUNCTION update_meeting_rooms_updated_at();

-- ============================================================================
-- DONE!
-- Meeting rooms feature tables created:
-- - meeting_rooms: Container for multi-agent conversations
-- - meeting_room_participants: Agent membership in meetings
-- - meeting_room_messages: Messages with agent attribution
-- ============================================================================
