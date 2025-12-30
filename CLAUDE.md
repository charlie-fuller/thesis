# Thesis - Multi-Agent GenAI Strategy Platform

## Memory Protocol (IMPORTANT)

### Session Start
At the beginning of each conversation, query Mem0 for recent context:
```
query: "recent decisions, issues, and context"
filters: {"repo": "thesis"}
```
Briefly mention any relevant memories found.

### During Session
Save important information to Mem0 when:
- A significant decision is made (architecture, approach, library choice)
- A tricky bug is solved (save the cause and fix)
- User states a preference or convention
- A TODO or next step is identified for future sessions
- Important stakeholder insights are discovered

### When Saving/Querying
Always use:
- **Save**: `metadata: {"repo": "thesis"}`
- **Query**: `filters: {"repo": "thesis"}`

### Session End
If the conversation included important decisions or unfinished work, save a summary to Mem0 before ending.

## Project Overview

Thesis is a multi-agent platform for enterprise GenAI strategy implementation. It helps AI Solutions Partners guide and manage successful AI initiatives by providing specialized agents for research, finance, IT/governance, legal, and meeting analysis.

### Agent Roster (17 Agents)

#### Meta-Agents (Always Present in Meetings)
| Agent | Name | Purpose |
|-------|------|---------|
| Facilitator | Facilitator | Meeting orchestration - welcomes users, clarifies intent, routes to specialists, ensures balanced participation, invokes systems thinking before conclusions. Not a domain expert - makes others brilliant. |
| Reporter | Reporter | Meeting synthesis and documentation - creates unified summaries, action items, and executive briefs from multi-agent discussions. Single voice for all documentation requests. Uses domain labels (Research, Financial, Security) instead of agent names for shareable output. |

#### Stakeholder Perspective Agents
| Agent | Name | Persona Alignment | Purpose |
|-------|------|-------------------|---------|
| Atlas | Research | Chris Baumgartner | GenAI research, Lean methodology, benchmarking |
| Fortuna | Finance | Raul Rivera III | ROI analysis, SOX compliance, business cases |
| Guardian | IT/Governance | Danny Leal | Security, compliance, shadow IT, vendor evaluation |
| Counselor | Legal | Ashley Adams | Contracts, AI risks, liability, data privacy |
| Sage | People | Chad Meek | Change management, human flourishing, adoption |
| Oracle | Meeting Intelligence | CIPHER v2.1 | Transcript analysis, stakeholder dynamics, sentiment extraction with evidence |

#### Consulting/Implementation Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Strategist | Executive Strategy | C-suite engagement, organizational politics, governance |
| Architect | Technical Architecture | Enterprise AI patterns, RAG, integration, build vs. buy |
| Operator | Business Operations | Process optimization, automation, operational metrics |
| Pioneer | Innovation/R&D | Emerging technology, hype filtering, maturity assessment |

#### Internal Enablement Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Catalyst | Internal Communications | AI messaging, employee engagement, AI anxiety |
| Scholar | Learning & Development | Training programs, champion enablement, adult learning |
| Echo | Brand Voice | Voice analysis, style profiling, AI emulation guidelines |

#### Systems/Coordination Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Nexus | Systems Thinking | Interconnections, feedback loops, leverage points, unintended consequences |
| Coordinator | Thesis | Central orchestrator for chat (not meetings), query routing, response synthesis |

### Key Capabilities

1. **Agent Selection in Chat**: Select specific agents or use Auto mode (Coordinator routes to best agent)
   - UI selector above chat input to pick agents (max 3)
   - `@mention` syntax in messages (e.g., `@atlas`, `@fortuna`) to invoke agents inline
   - Agent badge displayed on each response showing which agent answered
2. **Knowledge Base**: Unified document and conversation management (`/kb` page)
   - Upload documents (txt, md, docx, csv, json, xml)
   - Connect Google Drive and Notion for auto-sync
   - Assign documents to specific agents or make them global (available to all)
   - Edit agent visibility for existing documents via document info modal
   - Search and filter documents by name or source (Direct Upload, Google Drive, Notion)
   - View and manage conversation history
3. **Meeting Intelligence**: Upload meeting transcripts (Granola/Otter/Teams/Zoom), extract stakeholder insights with evidence-based sentiment analysis, power dynamics, and strategic recommendations
4. **Stakeholder Tracking**: Full CRM-style tracking with sentiment, engagement, alignment scores
5. **Research Intelligence**: Proactive monitoring of GenAI implementation research
   - Atlas auto-performs web research when no knowledge base results found
   - Uses Anthropic's native web search tool (`web_search_20250305`) with Claude 3.7 Sonnet
   - Requires beta header: `anthropic-beta: web-search-2025-03-05`
   - Credibility-tiered source filtering (Tier 1: consulting firms, Tier 2: Big 4/tech, Tier 3: industry pubs, Tier 4: blogs)
   - Sources appended with citations organized by tier
6. **Agent Coordination**: Hybrid model - some agents work independently, others collaborate
7. **Persistent Memory**: Mem0 integration for cross-conversation learning
8. **Meeting Room**: Multi-agent collaboration with selected agents for focused discussions
   - Meeting list shows "Autonomous" badge (emerald) for rooms that used autonomous discussion
   - Badge tooltip shows the discussion topic
9. **Autonomous Discussion**: Agents discuss topics amongst themselves with discourse moves (Question, Connect, Challenge, Extend, Synthesize) - user can interject anytime
   - Conversational coherence: Agents build on each other's points, not disconnected monologues
   - Each response acknowledges and connects to the previous speaker's insight
10. **Dig Deeper**: One-click elaboration on any assistant response for more detail
11. **Auto-Generated Titles**: Conversation titles auto-generated from initial message using Claude

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4 |
| Backend | FastAPI (Python 3.12), Uvicorn, Pydantic |
| Database | Supabase (PostgreSQL) with Row-Level Security |
| Graph DB | Neo4j Aura (stakeholder networks, agent expertise routing) |
| AI/ML | Anthropic Claude, Voyage AI embeddings, Google Gemini 2.5 Flash (images) |
| Memory | Mem0 for persistent agent memory |
| Integrations | Google Drive, Notion |
| Deployment | Railway (backend), Vercel (frontend) |

## Key Directories

```
/frontend
  /app           - Next.js App Router pages
    /kb          - Knowledge Base page (documents + conversations management)
    /chat        - Main chat interface
    /meeting-room - Multi-agent meeting rooms
    /admin       - Admin dashboard
  /components    - React components
    /kb          - Knowledge Base components (KBDocumentsContent)
  /contexts      - AuthContext, HelpChatContext, ThemeContext

/backend
  /api/routes    - FastAPI endpoints
  /agents        - Agent implementations (17 agents)
  /services      - Business logic including transcript_analyzer
  /system_instructions - Agent-specific prompts (XML files)

/database
  /migrations    - SQL migration scripts
  thesis_schema.sql - Complete schema including agents, stakeholders, ROI

/docs
  /planning      - Implementation plan and session transcripts
  CONTEXT.md     - Discovery context for the project
```

## Development Commands

```bash
# Frontend (from /frontend)
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint check

# Backend (from /backend)
uvicorn main:app --reload --port 8000   # Dev server
python -m pytest                         # Run tests
```

## Architecture Patterns

- **Multi-agent**: Router + orchestrator for agent coordination
- **Multi-tenancy**: Client-based data isolation via Supabase RLS
- **Streaming**: Server-sent events for real-time chat responses
- **Type safety**: Strict TypeScript + Pydantic validation throughout
- **Agent memory**: Mem0 for persistent cross-conversation context
- **People-first**: All recommendations consider change management

## Code Conventions

- **Frontend**: ESLint + Prettier, functional components, Context API for state
- **Backend**: Black + Ruff formatting, async/await, Pydantic models for all requests
- **Commits**: Conventional commits (fix:, feat:, docs:, etc.)
- **No emojis**: Keep documentation and code professional

## Agent Instruction Methodology

Agent system instructions use the **Gigawatt v4.0 RCCI Framework** with:

- **XML Structure**: `<version>`, `<role>`, `<context>`, `<capabilities>`, `<instructions>`, `<criteria>`, `<few_shot_examples>`, `<wisdom>`, `<anti_patterns>`
- **Smart Brevity**: All agents include `shared/smart_brevity.xml` for concise, scannable responses (100-150 words max, ask-first behavior for unclear intent)
- **Conversational Awareness**: All agents include `shared/conversational_awareness.xml` for multi-agent coherence - agents build on each other's points, never respond as if starting fresh
- **Chain-of-Thought**: Step-by-step analysis processes
- **Evidence-Based**: All insights backed by quotes/data
- **Persona Alignment**: Agents embody specific stakeholder perspectives
- **Few-Shot Examples**: Comprehensive examples showing expected output format
- **No Emojis**: Professional formatting throughout - emojis are explicitly banned

Canonical instructions live in `/backend/system_instructions/agents/*.xml` with fallbacks in each agent's `_get_default_instruction()` method.

### Smart Brevity Format

All agent responses follow this mandatory structure:
1. **The Big Thing** (1-2 sentences) - Key insight with metric
2. **Why It Matters** (1-2 sentences) - Business impact
3. **Key Details** (3-5 bullets or table) - Scannable facts
4. **Dig-Deeper Links** (2-4 links) - Expandable detail via `[text](dig-deeper:section_id)`

### Knowledge Base Context Usage (CRITICAL)

All agents have a 5th absolute rule: **ALWAYS USE KB CONTEXT**. When knowledge base context is provided in prompts:
- **PRIORITIZE** KB content over general knowledge - it's REAL data from user documents
- **CITE** sources explicitly: "According to [Source 1 - Interview Transcript]..."
- **QUOTE** relevant passages when they directly answer the question
- **NEVER** ignore KB content to give generic advice when specific data exists
- Mantra: "When in doubt, ask. When too long, cut. When KB exists, USE IT."

KB context retrieval in meeting rooms:
- **Vector search**: 10 chunks via Voyage AI, 1000 chars each (regular mode) or 8 chunks at 800 chars (autonomous)
- **Graph context**: Neo4j provides stakeholders, concerns, ROI opportunities, and relationships
- **Deduplication**: Context sources are deduplicated by document_id (highest similarity kept)
- **SSE event**: `context_sources` event sent before agent responses for frontend display

### Ask-First Behavior

When user intent is unclear (greetings, broad topics, first messages), agents ask a clarifying question before providing detailed answers:
- Present 2-4 domain-specific options
- Keep clarifying responses under 75 words
- Include dig-deeper link to capabilities
- Mantra: "When in doubt, ask. When too long, cut."

### Meeting Room Behavior

In multi-agent meetings, stricter limits and specific behaviors apply:

**Brevity Limits:**
- **50-100 words MAX** per agent turn (not 150)
- **75 words MAX** in autonomous discussions
- ONE key insight per turn - defer if not your domain
- No preamble, no "Great question!", no filler

**Facilitator Single-Agent Turn-Taking:**
- Facilitator invites ONE agent at a time (never "Fortuna and Sage, thoughts?")
- After agent responds, Facilitator returns to bridge/synthesize or invite next agent
- Creates natural back-and-forth conversation rhythm

**Reporter Domain Labels (No Agent Names):**
- Reports use domain labels: "Financial analysis shows..." NOT "Fortuna noted..."
- Ensures all output is shareable externally without explanation
- Domain labels: Research, Financial, Security/Compliance, People/Change, Technical, etc.

**Conversational Coherence (CRITICAL):**
- Agents are intelligent colleagues who specialize, NOT narrow experts who only understand their domain
- **Cardinal rule**: Never respond as if starting a fresh conversation
- Every response must acknowledge and build on what the previous speaker said
- Show cross-domain intelligence: understand WHY you're deferring, not just THAT you're deferring
- Facilitator weaves threads together with connected handoffs

See `/docs/AGENT_GUARDRAILS.md` for complete rules

## Thesis-Specific Tables

```sql
-- Agent System
agents                       -- Agent registry (17 agents) with capabilities column
agent_instruction_versions   -- Per-agent versioned instructions (single source of truth)
agent_handoffs               -- Agent-to-agent handoff tracking
agent_knowledge_base         -- Document-to-agent links for RAG

-- Stakeholder Management
stakeholders                 -- CRM-style stakeholder tracking
stakeholder_insights         -- Extracted insights from transcripts

-- Meeting Intelligence
meeting_transcripts          -- Processed transcript metadata
meeting_rooms                -- Multi-agent meeting sessions
meeting_room_participants    -- Agents in each meeting
meeting_room_messages        -- Messages with agent attribution

-- Business Intelligence
roi_opportunities            -- Identified ROI opportunities

-- Research Intelligence (Atlas)
research_tasks               -- Research task queue and history
research_schedule            -- Daily/weekly research schedule by focus area
research_sources             -- Credible sources with tier ratings (1-4)
knowledge_gaps               -- Detected knowledge gaps from agent conversations
agent_topic_mapping          -- Maps topics to relevant agents for distribution
```

## Database Migrations

Run migrations in order from `/database/migrations/`:

| # | File | Description |
|---|------|-------------|
| 001 | thesis_agents_and_stakeholders | Core agents and stakeholders |
| 002 | agent_knowledge_base | Document-agent linking for RAG |
| 003 | add_coordinator | Coordinator agent |
| 004 | graph_sync_tracking | Neo4j sync tracking |
| 005 | add_sage_agent | Sage (People/Change) agent |
| 006 | add_new_specialist_agents | Strategist, Architect, Operator, Pioneer, Catalyst, Scholar |
| 007 | meeting_rooms | Multi-agent meeting rooms |
| 008 | add_nexus_systems_thinking_agent | Nexus (Systems Thinking) agent |
| 009 | add_bard_agent | Echo (Brand Voice) agent |
| 010 | rename_bard_to_echo | Rename bard to echo |
| 011 | research_system | Atlas research tables, sources, schedule, gaps |
| 012 | autonomous_discussion | Autonomous discussion mode for meeting rooms |
| 013 | document_title | Add title column to documents for clean display names |
| 014 | add_facilitator_agent | Facilitator meta-agent + capabilities column for all agents |
| 015 | add_reporter_agent | Reporter meta-agent for meeting synthesis and documentation |

## Environment Variables

See `/frontend/.env.example` and `/backend/.env.example` for complete reference.

Key variables:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` (graph database)
- `ANTHROPIC_API_KEY` (Claude)
- `VOYAGE_API_KEY` (embeddings)
- `MEM0_API_KEY` (agent memory)

## Planning Documents

- `/docs/CONTEXT.md` - Full discovery context
- `/docs/planning/IMPLEMENTATION_PLAN.md` - Detailed implementation roadmap
- `/docs/planning/2024-12-26-planning-session.md` - Planning session transcript

## Testing & Code Quality

### Testing Infrastructure
- `/docs/testing/TESTING_PROMPT.md` - Reusable prompt for comprehensive code review and auto-fix
- `/docs/testing/COMPREHENSIVE_TEST_PLAN.md` - Full testing framework and strategy
- `/docs/testing/CODE_REVIEW_FINDINGS.md` - Latest code review findings

### Running Tests
```bash
cd /backend
source venv/bin/activate
python -m pytest tests/ -v --tb=short
```

### Code Quality Targets
| Metric | Target |
|--------|--------|
| Code Quality Score | 9.0/10 |
| Test Pass Rate | 100% |
| Bare except blocks | 0 |
| Deprecated patterns | 0 |
| Print statements (prod) | 0 |

## Important Files

### Backend
- `/backend/main.py` - FastAPI app entry point
- `/backend/agents/` - Agent implementations (17 agents)
- `/backend/agents/agent_factory.py` - Agent creation and registration
- `/backend/agents/base_agent.py` - Base class with instruction loading
- `/backend/agents/atlas.py` - Research agent with web search capability
- `/backend/services/transcript_analyzer.py` - Meeting transcript analysis
- `/backend/services/meeting_orchestrator.py` - Multi-agent meeting coordination
- `/backend/services/instruction_loader.py` - XML instruction file loading
- `/backend/services/research_scheduler.py` - Daily Atlas research scheduler
- `/backend/services/research_context.py` - Topic prioritization from platform context
- `/backend/services/agent_observer.py` - Cross-agent conversation monitoring
- `/backend/services/web_researcher.py` - Anthropic web search with credibility filtering
- `/backend/services/graph/query_service.py` - Neo4j graph queries including `get_meeting_context()` for stakeholder/concern retrieval
- `/backend/services/graph/connection.py` - Neo4j connection management
- `/backend/system_instructions/agents/*.xml` - Agent behavior configuration (Gigawatt v4.0)
- `/backend/system_instructions/shared/smart_brevity.xml` - Mandatory response format directive + KB usage rules
- `/backend/system_instructions/shared/conversational_awareness.xml` - Multi-agent coherence directive (included by smart_brevity.xml)
- `/backend/services/chat_agent_service.py` - Agent selection, @mention parsing, instruction loading for chat
- `/backend/api/routes/chat.py` - Chat endpoints including Dig Deeper and agent routing
- `/backend/api/routes/meeting_rooms.py` - Meeting room CRUD and streaming
- `/backend/api/routes/agents.py` - Agent management endpoints (note: static routes like `/documents/available` must be defined before parameterized routes like `/{agent_id}/documents`)
- `/backend/api/routes/documents.py` - Document CRUD, upload, processing, and agent assignment endpoints
- `/backend/api/routes/research.py` - Atlas research API endpoints
- `/backend/api/routes/admin.py` - Admin dashboard with real API health checks

### Frontend
- `/frontend/app/layout.tsx` - Root layout with providers
- `/frontend/components/ChatInterface.tsx` - Main chat with agent selection and Dig Deeper
- `/frontend/components/AgentSelector.tsx` - Agent dropdown selector component
- `/frontend/components/AgentIcon.tsx` - Agent icons and color mapping
- `/frontend/components/ChatMessage.tsx` - Message display with agent badges
- `/frontend/app/meeting-room/` - Meeting room pages
- `/frontend/app/admin/agents/` - Agent admin interface

### Database
- `/database/thesis_schema.sql` - Complete DB schema
- `/database/migrations/` - All migration scripts (001-015)

### Documentation
- `/docs/AGENT_GUARDRAILS.md` - Agent brevity rules, word limits, conversational coherence, and behavioral constraints
- `/docs/atlas/PROACTIVE_RESEARCH_PLAN.md` - Atlas research system architecture
- `/docs/neo4j/SYNC_PLAN.md` - PostgreSQL to Neo4j sync architecture

## Removed Features (December 2025)

The following features were removed to simplify the platform:

- **Quick Prompts**: User-defined prompt shortcuts - removed in favor of agent commands
- **Projects**: Manual folder organization - replaced by vector DB + Neo4j graph for dynamic semantic search
- **Templates**: Template-based prompt generation - functionality moved to agent instructions
- **Core Documents**: Special protected documents - all documents now treated equally, deletable by owner
- **Standalone Documents Page**: `/documents` route removed - document management now integrated into `/kb` (Knowledge Base) page

Related database tables/columns that can be cleaned up:
- `user_quick_prompts` (migration 025)
- `documents.is_core_document` column

## Known Issues & Fixes

### Python 3.12 Compatibility
Railway runs Python 3.12 which has stricter f-string rules. Backslashes (`\n`, `\t`, etc.) cannot appear inside f-string expressions `{}`. Pre-compute strings with backslashes before using them in f-strings.

```python
# BAD - causes SyntaxError in Python 3.12
f"{('Header:\n' + content) if content else 'Empty'}"

# GOOD - pre-compute the string
header_text = f"Header:\n{content}" if content else "Empty"
f"{header_text}"
```

### Agent Icons & Colors (Single Source of Truth)
Agent icons, colors, and styling are centralized in `/frontend/components/AgentIcon.tsx`:
- `AGENT_ICONS` - Lucide icon mapping for each agent
- `AGENT_COLORS` - Transparent background colors with border (for badges/pills)
- `AGENT_AVATAR_COLORS` - Solid background colors (for message avatars)
- `getAgentColor()` - Returns combined class string for transparent style
- `getAgentAvatarColor()` - Returns `{bg, text}` for solid avatar style

Components that use these:
- `/frontend/components/meeting-room/ParticipantBar.tsx` - Uses `getAgentColor()` for participant list
- `/frontend/components/meeting-room/MeetingMessage.tsx` - Uses `getAgentColor()` for message avatars
- `/frontend/components/meeting-room/CreateMeetingModal.tsx` - Has its own `AGENT_SHORT_DESCRIPTIONS`

When adding new agents, update `AgentIcon.tsx` (icons and both color maps).

### FastAPI Route Ordering
In FastAPI, static routes must be defined **before** parameterized routes. Otherwise, the parameter captures the static path segment.

```python
# BAD - /documents/available gets matched as /{agent_id}/documents with agent_id="documents"
@router.get("/{agent_id}/documents")
async def get_agent_documents(...): ...

@router.get("/documents/available")  # Never reached!
async def get_available_documents(...): ...

# GOOD - static route defined first
@router.get("/documents/available")
async def get_available_documents(...): ...

@router.get("/{agent_id}/documents")
async def get_agent_documents(...): ...
```

### Lucide React Icons
Lucide icons don't support the `title` attribute directly. Wrap in a `<span>` for tooltips:

```tsx
// BAD - TypeScript error
<Check className="w-4 h-4" title="Tooltip text" />

// GOOD - wrap in span
<span title="Tooltip text">
  <Check className="w-4 h-4" />
</span>
```
