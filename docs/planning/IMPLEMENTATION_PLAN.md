# Thesis Platform - Implementation Plan

## Summary

Build a multi-agent platform for enterprise GenAI strategy implementation, forking from Thesis's proven infrastructure and adding agent coordination capabilities.

**Timeline:** MVP ready before January 5, 2025 (~10 days)
**Day 1 Value:** Transcript analyzer (Oracle) - upload meeting transcripts, get stakeholder insights
**Usage Pattern:** Morning dashboard + post-meeting processing + on-demand queries
**Initial User:** Charlie only (demos to other AI Solutions Partners later)
**Data Sensitivity:** Moderate - internal discussions, standard security

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent conflict | Surface both perspectives | Transparency over forced resolution |
| Agent memory | Mem0 integration | Persistent cross-conversation learning |
| Stakeholder depth | Full CRM-style | Contact info, history, touchpoints, preferences |
| Speaker auto-linking | Confident auto-link | Match by name/role without confirmation |
| Transcript format | Markdown/TXT | Granola/Otter export format |
| Exit strategy | Exportable + open source + transferable | All of the above |
| Mobile access | Full mobile capability | Upload transcripts, chat with agents from phone |
| Notifications | In-app only | No email/Slack for MVP |
| Data corrections | Multiple methods | Inline edit, feedback loop, re-analyze |
| Platform design | Generic from start | Ready to open-source, configure for Contentful |
| Data backup | Sync to Obsidian/Notion | Redundancy and offline access |

### Pre-Launch Actions
- [ ] **Compliance check**: Verify with Contentful what data can be stored externally
- [ ] Import some existing transcripts to seed the system

---

## ACCELERATED MVP (Before Jan 5)

### Priority 1: Oracle (Transcript Analyzer) - Days 1-4

This is the **Day 1 value** - ability to upload Granola/Otter transcripts (markdown/txt format) and extract stakeholder insights.

**Minimal viable Oracle:**
- [ ] Upload transcript (markdown/txt)
- [ ] Parse speaker-labeled text
- [ ] Extract attendees with inferred roles
- [ ] Analyze sentiment per speaker
- [ ] Identify concerns and enthusiasm signals
- [ ] Generate meeting summary
- [ ] Store insights in stakeholder database

**Files to create:**
- `/thesis/backend/services/transcript_analyzer.py`
- `/thesis/backend/api/routes/transcripts.py`
- `/thesis/frontend/app/transcripts/page.tsx`
- `/thesis/frontend/components/TranscriptUpload.tsx`

### Priority 2: Basic Infrastructure - Days 1-2 (Parallel)

- [ ] Fork Thesis to Thesis
- [ ] Set up Supabase with minimal schema (stakeholders, transcripts)
- [ ] Deploy to Railway + Vercel
- [ ] Single-user auth (just Charlie)

### Priority 3: Rich Dashboard - Days 5-6

**Morning briefing view with key metrics:**
- **Sentiment trends**: Sparklines showing stakeholder sentiment over time
- **Engagement frequency**: Who haven't I talked to recently?
- **Open concerns**: Unresolved issues surfaced across meetings
- **Alignment scores**: Visual indicator of stakeholder alignment with AI initiatives
- Recent transcripts with summaries
- Stakeholder cards with quick actions

### Priority 3.5: Mem0 Integration - Day 6

**Agent memory using Mem0 MCP:**
- Store user preferences across conversations
- Remember past discussions and decisions
- Enable agents to say "You mentioned last week that..."
- Track what works/doesn't work for Charlie's style

**Integration approach:**
- Use existing Mem0 MCP server (already configured)
- Store memories per agent + global memories
- Query relevant memories before each response
- Add new learnings after significant interactions

### Priority 4: Atlas (Research) - Days 7-10 (If time permits)

- Basic chat with Claude
- Web search capability
- Store research in knowledge base

---

## POST-LAUNCH PHASES (After Jan 5)

## Phase 1: Foundation (Week 1)

### 1.1 Repository Setup
- [ ] Fork Thesis repository structure to Thesis
- [ ] Update `CLAUDE.md` with Thesis-specific guidance
- [ ] Create new Supabase project
- [ ] Apply Thesis base schema + Thesis extensions

**Key files to create:**
- `/thesis/CLAUDE.md`
- `/thesis/README.md`
- `/thesis/backend/migrations/001_thesis_schema.sql`

### 1.2 Database Schema Extensions

Add these tables to Thesis's schema:

```sql
-- Agent Registry
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE,  -- "atlas", "capital", etc.
    display_name VARCHAR(100),
    system_instruction TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}'
);

-- Stakeholders (Full CRM-style tracking)
CREATE TABLE stakeholders (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(255),
    department VARCHAR(100),  -- finance, it, legal, governance
    organization VARCHAR(255) DEFAULT 'Contentful',

    -- Sentiment & Engagement
    sentiment_score FLOAT DEFAULT 0.0,  -- -1 to 1
    sentiment_trend VARCHAR(20),  -- improving, stable, declining
    engagement_level VARCHAR(50),  -- champion, supporter, neutral, skeptic, blocker
    alignment_score FLOAT DEFAULT 0.0,  -- 0 to 1, alignment with AI initiatives

    -- Interaction History
    first_interaction DATE,
    last_interaction TIMESTAMPTZ,
    total_interactions INTEGER DEFAULT 0,

    -- Preferences & Notes
    communication_preferences JSONB DEFAULT '{}',  -- {preferred_channel, best_times, etc.}
    key_concerns JSONB DEFAULT '[]',  -- Array of active concerns
    interests JSONB DEFAULT '[]',  -- What they care about
    notes TEXT,

    -- Relationships
    reports_to UUID REFERENCES stakeholders(id),
    influences JSONB DEFAULT '[]',  -- Array of stakeholder IDs they influence

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stakeholder Insights
CREATE TABLE stakeholder_insights (
    id UUID PRIMARY KEY,
    stakeholder_id UUID REFERENCES stakeholders(id),
    source_document_id UUID REFERENCES documents(id),
    insight_type VARCHAR(50),  -- concern, enthusiasm, question, commitment
    content TEXT,
    confidence FLOAT
);

-- Meeting Transcripts
CREATE TABLE meeting_transcripts (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    meeting_date DATE,
    attendees JSONB,
    summary TEXT,
    sentiment_summary JSONB,
    action_items JSONB
);

-- ROI Opportunities
CREATE TABLE roi_opportunities (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    department VARCHAR(100),
    estimated_value_usd DECIMAL,
    confidence_level VARCHAR(50),
    status VARCHAR(50),  -- identified, validated, in_progress, completed
    stakeholder_alignment JSONB
);

-- Agent Handoffs
CREATE TABLE agent_handoffs (
    id UUID PRIMARY KEY,
    conversation_id UUID,
    from_agent VARCHAR(50),
    to_agent VARCHAR(50),
    reason TEXT
);
```

### 1.3 Agent Foundation

**Create base agent class:**
- `/thesis/backend/agents/base_agent.py`

**Create agent router:**
- `/thesis/backend/services/agent_router.py`
- Intent detection via keywords + LLM fallback
- Returns primary agent + optional supporting agents

**Create first agent (Atlas - Research):**
- `/thesis/backend/agents/atlas.py`
- `/thesis/backend/system_instructions/atlas.xml`
- Tools: web_search, knowledge_search, synthesize, arxiv_search

**Atlas Core Capabilities:**
1. **Consulting Landscape**: Track what Big 4, McKinsey, BCG, Accenture are recommending for GenAI implementation
2. **Corporate Case Studies**: Monitor what companies (similar to Contentful) are doing - successes and failures
3. **Thought Leadership**: Ingest articles, blog posts, whitepapers on GenAI implementation methodologies
4. **Academic Research**: Track MIT Sloan, Harvard Business Review, Gartner, Forrester findings
5. **Proactive Alerts**: Notify when new research relates to active work streams

**Atlas Proactive Features (Phase 2):**
- Scheduled web searches on key topics (daily/weekly)
- RSS/feed monitoring for key publications
- Pattern matching: "This new article relates to your Finance stakeholder concerns about X"
- Research digest generation: Weekly summary of relevant findings

### 1.4 Modify Chat Route

Update `/thesis/backend/api/routes/chat.py`:
- Add agent routing before Claude call
- Pass agent-specific system instructions
- Return agent name in response
- Support handoff triggers

### 1.5 Deploy MVP

- Railway: Backend deployment
- Vercel: Frontend deployment
- Environment variables configured

---

## Phase 2: Transcript Intelligence (Week 2)

### 2.1 Oracle Agent (Transcript Analyzer)

**Create transcript analyzer service:**
- `/thesis/backend/services/transcript_analyzer.py`

**Extraction capabilities:**
- Attendees and roles
- Sentiment by speaker
- Concerns (explicit and implicit)
- Enthusiasm signals
- Action items and commitments
- Key quotes

**Create Oracle agent:**
- `/thesis/backend/agents/oracle.py`
- `/thesis/backend/system_instructions/oracle.xml`

### 2.2 Transcript Upload Flow

**Backend:**
- `/thesis/backend/api/routes/transcripts.py`
- POST `/transcripts/upload` - Upload and process
- GET `/transcripts/{id}` - Get analysis results
- GET `/transcripts/{id}/stakeholders` - Extracted stakeholders

**Frontend:**
- `/thesis/frontend/app/transcripts/page.tsx`
- `/thesis/frontend/components/TranscriptUpload.tsx`
- `/thesis/frontend/components/StakeholderCard.tsx`

### 2.3 Stakeholder Database Population

Auto-populate stakeholders table from transcript analysis:
- Create/update stakeholder records
- Link insights to stakeholders
- Track sentiment over time across meetings

---

## Phase 3: Finance Agent + Handoffs (Week 3)

### 3.1 Capital Agent (Finance)

**Create Capital agent:**
- `/thesis/backend/agents/capital.py`
- `/thesis/backend/system_instructions/capital.xml`

**Capabilities:**
- ROI calculation assistance
- Budget justification framing
- Finance stakeholder preparation
- Opportunity identification

### 3.2 ROI Opportunity Detection

**Create ROI service:**
- `/thesis/backend/services/roi_detector.py`

**Detection from:**
- Meeting transcripts (pain points mentioned)
- Research documents (proven use cases)
- User-identified opportunities

### 3.3 Agent Handoff Mechanism

**Implement handoffs:**
- Atlas detects finance-related queries → handoff to Capital
- Capital detects research needs → handoff to Atlas
- Log handoffs for analytics

**Update chat route:**
- Check for handoff triggers in agent response
- Execute handoff with context preservation
- Notify user of agent switch

### 3.4 Knowledge Organization

**Implement tagging:**
- Domain tags: finance, it, legal, governance
- Stakeholder tags: link documents to people
- Agent access filters

**Agent-aware search:**
- Each agent filters knowledge by domain
- Cross-domain access for synthesis tasks

---

## System Instruction Management

### Architecture (Fork from Thesis's approach)

Thesis has a system instruction versioning system we'll extend for multi-agent:

**Database Tables:**
```sql
-- Extend Thesis's system_instruction_versions for multi-agent
CREATE TABLE agent_instruction_versions (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    version_number VARCHAR(20),
    instructions TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ
);

-- Track which version was used for each conversation
ALTER TABLE conversations ADD COLUMN agent_instruction_version_id UUID
    REFERENCES agent_instruction_versions(id);
```

**Admin Capabilities:**
- View all agents and their current active instructions
- Edit instructions with live preview
- Save new version (auto-versioned)
- Activate/deactivate versions
- Compare versions side-by-side
- Rollback to previous versions
- See which conversations used which version

**API Endpoints:**
- `GET /api/agents` - List all agents
- `GET /api/agents/{id}/instructions` - Get current instructions
- `GET /api/agents/{id}/instructions/versions` - List all versions
- `POST /api/agents/{id}/instructions` - Create new version
- `PATCH /api/agents/{id}/instructions/{version_id}` - Activate version
- `GET /api/agents/{id}/instructions/compare?v1=X&v2=Y` - Compare versions

**Frontend:**
- `/admin/agents` - Agent management dashboard
- `/admin/agents/{id}/instructions` - Instruction editor with version history
- Side-by-side diff view for version comparison
- "Test this version" preview mode

### User Management & Agent Access

**User Roles:**
- **Super Admin**: Full access to all agents, can create new agents
- **Admin**: Can edit instructions for assigned agents
- **User**: Can chat with assigned agents, no editing

**Agent Assignment:**
```sql
CREATE TABLE user_agent_access (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    access_level VARCHAR(20),  -- "admin", "user"
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Custom Agent Creation (Phase 3+)

For federalization - allow admins to create custom agents:

**Workflow:**
1. Admin clicks "Create New Agent"
2. Provides: name, display_name, description
3. Writes initial system instructions
4. Configures: tools available, knowledge filters
5. Assigns users who can access this agent

**Use Case:** Marketing team wants their own agent focused on content strategy - they can create one without affecting core G&A agents.

---

## Phase 4: Remaining Agents (Weeks 4-6)

### 4.1 Guardian Agent (IT/Governance)
- `/thesis/backend/agents/guardian.py`
- Focus: Security, infrastructure, policy alignment

### 4.2 Counselor Agent (Legal)
- `/thesis/backend/agents/counselor.py`
- Focus: Contracts, compliance, risk mitigation

### 4.3 Multi-Agent Orchestration
- `/thesis/backend/services/agent_orchestrator.py`
- Synthesis workflows (all agents contribute)
- Sequential workflows (pass context through agents)

---

## Thesis Features to Preserve

### Help System (Critical)
Thesis's help system must be preserved in Thesis for both users and admins:

**Components to fork:**
- `/backend/api/routes/help.py` - Help API endpoints
- `/backend/services/help_service.py` - Help generation logic
- `/frontend/components/HelpChat.tsx` - Help chat interface
- `/frontend/contexts/HelpChatContext.tsx` - Help state management
- Help documentation tables in database

**Features to maintain:**
- Context-aware assistance based on current page/feature
- User help documentation
- Admin help documentation
- Help chat interface for real-time questions
- Documentation generation from system knowledge

### System Instruction Versioning
Already covered in the plan - extend for multi-agent with per-agent versioning.

---

## Key Files from Thesis to Modify

| Thesis File | Thesis Modification |
|-------------|---------------------|
| `/backend/api/routes/chat.py` | Add agent routing, handoffs |
| `/backend/api/routes/help.py` | Adapt for multi-agent context |
| `/backend/document_processor.py` | Add transcript-specific chunking |
| `/backend/system_instructions/` | Create agent-specific instructions |
| `/database/thesis_full_schema.sql` | Add agent/stakeholder/ROI tables |
| `/frontend/app/chat/page.tsx` | Add agent indicator, selector |
| `/frontend/components/HelpChat.tsx` | Fork as-is, adapt for Thesis branding |

## Key Files to Create

```
thesis/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── atlas.py
│   │   ├── capital.py
│   │   ├── guardian.py
│   │   ├── counselor.py
│   │   └── oracle.py
│   ├── services/
│   │   ├── agent_router.py
│   │   ├── agent_orchestrator.py
│   │   ├── transcript_analyzer.py
│   │   └── roi_detector.py
│   ├── api/routes/
│   │   ├── agents.py
│   │   ├── transcripts.py
│   │   ├── stakeholders.py
│   │   └── roi.py
│   └── system_instructions/
│       ├── atlas.xml
│       ├── capital.xml
│       ├── guardian.xml
│       ├── counselor.xml
│       └── oracle.xml
├── frontend/
│   ├── app/
│   │   ├── transcripts/page.tsx
│   │   ├── stakeholders/page.tsx
│   │   └── roi/page.tsx
│   └── components/
│       ├── AgentSelector.tsx
│       ├── AgentIndicator.tsx
│       ├── TranscriptUpload.tsx
│       └── StakeholderCard.tsx
└── docs/
    ├── CONTEXT.md (created)
    ├── planning/
    │   └── IMPLEMENTATION_PLAN.md (this file)
    └── architecture.md
```

---

## Deployment

**Backend (Railway):**
- Fork Thesis's `railway.json` configuration
- Add new environment variables for agent config

**Frontend (Vercel):**
- Fork Thesis's `vercel.json` configuration
- Update API endpoints

**Database (Supabase):**
- New project for Thesis
- Apply Thesis schema + Thesis extensions
- Configure RLS policies

---

## MVP Success Criteria

1. Can upload a meeting transcript and get stakeholder insights
2. Can ask research questions and get evidence-based answers
3. Can see which agent is responding
4. Basic handoff works between Atlas and Capital
5. Stakeholder database populated from transcripts
6. Deployed and accessible

---

## Next Steps After Plan Approval

1. Fork Thesis repository to Thesis
2. Set up new Supabase project
3. Apply database migrations
4. Create base agent infrastructure
5. Implement Atlas agent
6. Deploy to Railway + Vercel
