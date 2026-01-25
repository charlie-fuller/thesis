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

### Agent Roster (21 Agents)

#### Meta-Agents (Always Present in Meetings)
| Agent | Name | Purpose |
|-------|------|---------|
| Facilitator | Facilitator | Meeting orchestration - welcomes users, clarifies intent, routes to specialists, ensures balanced participation, invokes systems thinking before conclusions. Not a domain expert - makes others brilliant. |
| Reporter | Reporter | Meeting synthesis and documentation - creates unified summaries, action items, and executive briefs from multi-agent discussions. Single voice for all documentation requests. Uses domain labels (Research, Financial, Security) instead of agent names for shareable output. |

#### Stakeholder Perspective Agents
| Agent | Name | Persona Alignment | Purpose |
|-------|------|-------------------|---------|
| Atlas | Research | Chris Baumgartner | GenAI research, Lean methodology, benchmarking |
| Capital | Finance | Raul Rivera III | ROI analysis, SOX compliance, business cases |
| Guardian | IT/Governance | Danny Leal | Security, compliance, shadow IT, vendor evaluation |
| Counselor | Legal | Ashley Adams | Contracts, AI risks, liability, data privacy |
| Sage | People | Chad Meek | Change management, human flourishing, adoption |
| Oracle | Meeting Intelligence | CIPHER v2.1 | Transcript analysis, stakeholder dynamics, sentiment extraction with evidence |

#### Consulting/Implementation Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Strategist | Executive Strategy | C-suite engagement, organizational politics, governance |
| Architect | Technical Architecture | Enterprise AI patterns, RAG, integration, build vs. buy |
| Operator | Business Operations | Process optimization, automation, operational metrics, **Project Triage** pipeline management |
| Pioneer | Innovation/R&D | Emerging technology, hype filtering, maturity assessment |

#### Internal Enablement Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Catalyst | Internal Communications | AI messaging, employee engagement, AI anxiety |
| Scholar | Learning & Development | Training programs, champion enablement, adult learning |
| Echo | Brand Voice | Voice analysis, style profiling, AI emulation guidelines |
| Glean Evaluator | Can We Glean This? | Glean platform fit assessment, connector analysis, build vs. buy for search |
| Compass | Career Coach | Win capture, performance tracking, check-in prep, strategic alignment |
| Taskmaster | Personal Accountability | Task discovery from KB/meetings, progress tracking, slippage alerts, focus guidance, daily Slack digests |
| Manual | Documentation Assistant | In-app help, feature explanation, navigation guidance, troubleshooting |

#### Systems/Coordination Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Nexus | Systems Thinking | Interconnections, feedback loops, leverage points, unintended consequences |
| Coordinator | Thesis | Central orchestrator for chat (not meetings), query routing, response synthesis |

### Key Capabilities

1. **Agent Selection in Chat**: Select specific agents or use Auto mode (Coordinator routes to best agent)
   - UI selector above chat input to pick agents (max 3)
   - `@mention` syntax in messages (e.g., `@atlas`, `@capital`) to invoke agents inline
   - Agent badge displayed on each response showing which agent answered
2. **Knowledge Base**: Unified document and conversation management (`/kb` page)
   - Upload documents (txt, md, docx, csv, json, xml, pdf)
   - **Auto-classification**: Documents auto-analyzed for agent relevance on upload
     - Keyword scoring + LLM classification (Claude Haiku) for ambiguous cases
     - High-confidence matches (>80%) auto-tagged, ambiguous flagged for review
     - Review banner in KB page for user confirmation
   - **Agent-filtered RAG**: Retrieval prioritizes documents tagged for querying agent
     - Hybrid strategy: agent-filtered first, falls back to all docs if insufficient results
     - Relevance scores stored in `agent_knowledge_base.relevance_score`
   - Connect Google Drive, Notion, and **Obsidian vaults** for auto-sync
   - Assign documents to specific agents or make them global (available to all)
   - Edit agent visibility for existing documents via document info modal
   - Search and filter documents by name or source (Direct Upload, Google Drive, Notion)
   - View and manage conversation history
3. **Meeting Intelligence**: Upload meeting transcripts (Granola/Otter/Teams/Zoom), extract stakeholder insights with evidence-based sentiment analysis, power dynamics, and strategic recommendations
4. **Stakeholder Tracking**: Full CRM-style tracking with sentiment, engagement, alignment scores
   - **Auto-discovery from meetings**: Scan meeting documents to extract stakeholder mentions
     - Uses Claude Sonnet to identify names, roles, departments, concerns, interests, sentiment
     - Deduplication detects potential matches with existing stakeholders
     - Candidate review system: accept, reject, or merge into existing stakeholder
     - Auto-links accepted stakeholders to related opportunities and tasks
     - Manual scan via "Scan for Stakeholders" button (no auto-extraction on upload)
   - Dashboard panel shows count of pending stakeholder candidates
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
12. **Task Management**: Kanban-style task board (`/tasks` page) with drag-and-drop status updates
    - Task extraction from meeting transcripts
    - **Auto-extraction from KB documents**: Tasks automatically discovered on document upload
      - Uses Claude Sonnet for high-quality extraction (runs in background)
      - Simple, natural prompt: "Find action items from this document"
      - Documents tracked with `tasks_scanned_at` to prevent duplicate scanning
      - `force_rescan` option available to re-scan previously processed documents
    - Task candidates system: extracted tasks staged for user review before creation
    - Rich task context: description, meeting context, stakeholders, value proposition, topics
    - Priority levels, assignees, due dates
    - **Team/department assignment**: Optional dropdown (Finance, Legal, IT, Operations, HR, Marketing, Sales, Engineering, Executive, Other)
    - **Project linking**: Tasks can be linked to parent opportunities/projects
    - Filtering by team, linked project, and other criteria
    - Status history tracking
    - Wider modal UI, taller description fields, column add buttons
13. **Project Triage (Operator)**: AI opportunity pipeline management
    - Tier-based opportunity scoring (Tier 1-4)
    - Stakeholder-linked opportunities with owner tracking
    - Department filtering and status progression
    - Operator agent auto-injects triage context for relevant queries
14. **Opportunities Pipeline**: Dedicated opportunities management (`/opportunities` page)
    - **Two-tab interface**: Pipeline (tier/priority views) and Analysis (scatter plot)
    - Visual tier-based grouping with expandable sections
    - Status tracking (identified, scoping, pilot, scaling, completed, blocked)
    - **Analysis Tab**: ROI vs Effort scatter plot visualization
      - Quadrant view: Quick Wins, Strategic Bets, Low Priority, Questionable
      - Dots colored by tier (T1=rose, T2=amber, T3=blue, T4=slate)
      - Clickable dots open opportunity detail modal
      - Summary cards show count per quadrant
    - Click any opportunity card to open detail modal with:
      - **Edit Mode**: Click pencil icon to edit scores and details inline
        - Editable: title, description, department, current/desired state, next step
        - Score inputs: ROI Potential, Effort, Strategic Alignment, Readiness (1-5)
        - Status dropdown with all status options
        - Save/Cancel buttons in footer
      - **Convert to Project**: "Start as Project" CTA button for identified opportunities
        - Opens ProjectNameModal to name the project
        - Changes status to "scoping" and sets project_name
        - Enables Taskmaster section for task breakdown
      - **Score Justification**: Visual breakdown of 4 dimensions (ROI, Effort, Strategic, Readiness) with explanations of what each score level means
      - **Scoring Confidence**: 0-100% meter showing confidence in scores
        - Rubric-based evaluation of information completeness
        - Color-coded: green (80+), blue (60-79), amber (40-59), red (<40)
        - Lists questions that would raise confidence if answered
        - Auto-calculated when justifications are generated
      - **AI-Generated Justifications**: Claude generates 3-4 sentence descriptions for:
        - Opportunity summary (what it is and potential business impact)
        - Each scoring dimension (why it received that score)
        - Auto-generated on opportunity create (if scores provided) and score updates
        - Triggered by KB document uploads via relevance detection
        - Manual "Generate/Regenerate Analysis" button in modal
      - **Related Documents**: Vector search finds KB documents relevant to the opportunity's context
        - **Inline Document Viewer**: Click Eye icon to view document content in modal without leaving the page
        - External link icon opens document in Knowledge Base (new tab)
      - **Q&A Chat**: Ask questions about the opportunity and get AI answers with source citations
      - **Taskmaster Chat**: Break projects into tasks (only visible for projects with project_name)
        - Chat with Taskmaster agent using project context
        - Extracts tasks from conversation using `[TASK]...[/TASK]` format
        - Creates task_candidates linked to the opportunity
        - Tasks appear in Discovery Inbox for review
        - Suggested prompts for quick start
    - Create new opportunities with scoring criteria
    - **Confidence Evaluation**: `POST /api/opportunities/evaluate-confidence` to batch-evaluate all opportunities
15. **Meeting Prep**: Stakeholder briefing pages (`/meeting-prep/[stakeholder_id]`)
    - Pre-meeting context on stakeholder priorities and pain points
    - Recent interaction history and open questions
    - AI-recommended talking points
16. **Stakeholder Engagement Analytics**: Automatic engagement level calculation
    - Weekly scheduler (Sunday 4 AM UTC) recalculates levels
    - Sticky levels (only demote on explicit negative signals)
    - Engagement trends visualization with Recharts
    - History tracking for trend analysis
17. **Obsidian Vault Sync**: Sync markdown files from local Obsidian vaults to KB
    - File watcher monitors vault for changes (create/modify/delete)
    - Parses YAML frontmatter (including `thesis-agents` for auto-tagging)
    - Converts `[[wikilinks]]` to standard markdown links
    - Incremental sync via content hash change detection
    - **Empty content validation**: Rejects files with 0 bytes after frontmatter parsing
    - **Deduplication**: Checks `obsidian_file_path` before creating to prevent duplicates
    - CLI watcher: `python -m scripts.obsidian_watcher --user-id <uuid>`
    - Full resync: `POST /api/obsidian/sync/full` clears sync state and re-syncs all files
18. **Career Status Reports (Compass)**: AI-powered career performance assessment
    - 5-dimension rubric: Strategic Impact (25%), Execution Quality (25%), Relationship Building (20%), Growth Mindset (15%), Leadership Presence (15%)
    - Level descriptors (1-5 scale) with clear criteria for each dimension
    - AI-generated justifications citing evidence from KB documents
    - Areas of strength, growth opportunities, and recommended actions
    - Improvement actions per dimension with concrete next steps
    - Report history with period filtering
    - Generate from Agent Detail page (`/admin/agents/[compass_id]`)
19. **Enhanced RAG Search**: Improved document retrieval for context-aware responses
    - **Original date tracking**: Documents preserve their original creation date (not just upload date)
    - **Document type filtering**: RAG queries can target specific document types (transcripts, reports, etc.)
    - **Recency boost**: Recent documents weighted higher for work/task queries
    - Meeting/transcript documents prioritized in meeting-related queries
    - Cache clearing endpoint for admin (`POST /api/admin/rag-cache/clear`)
20. **Unified Discovery Inbox**: Dashboard panel for reviewing all pending candidates
    - Tabbed interface: Tasks | Opportunities | Stakeholders with count badges
    - Inline accept/reject with carousel navigation through candidates
    - Source context display showing where items were discovered
    - **Opportunity Candidates**: Extracted from meeting documents via Granola scanner
      - Deduplication: Fuzzy title matching detects existing opportunities
      - Accept creates opportunity, reject discards with reason
      - "Link to existing" option when duplicate detected
    - **Task Candidates**: Discovered from KB documents
    - **Stakeholder Candidates**: Extracted from meeting transcripts
    - Auto-refreshes every 2 minutes
21. **Project Naming Workflow**: Required project name for opportunities in active phases
    - Modal triggered when opportunity status changes to scoping or pilot
    - Project name required, description optional
    - Enables task linking to parent projects
22. **Granola Vault Scanner**: Extracts structured data from synced Granola meeting notes
    - **Dashboard Panel**: Shows scan status on System Health tab (total/scanned/new counts)
    - **What it extracts** (all as candidates for review):
      - AI opportunities with scores (ROI, effort, strategic alignment, readiness)
      - Tasks with assignees and due dates
      - Stakeholders with roles, sentiment, concerns, and interests
    - **Date filtering**: Only scans meetings from Jan 5, 2026 onwards (configurable)
      - Default cutoff: `DEFAULT_SINCE_DATE = date(2026, 1, 5)` (post role-start)
      - Multi-method date detection: `original_date` field > filename parsing > path parsing
      - API parameters: `since_date=YYYY-MM-DD` or `days_back=N`
    - **Background scanning**: Runs in background thread, continues if user navigates away
      - Use `background=true` parameter for async scanning
      - Returns `job_id` for status polling via `GET /api/pipeline/granola/scan/job/{job_id}`
      - Frontend shows confirmation message: "Scan started! You can navigate away..."
    - **Deduplication logic**:
      - Opportunities: Fuzzy title match (>85%) + vector similarity search; matches flagged with "Link to existing" option
      - Tasks: Fuzzy title match (>85%); similar tasks skipped entirely
      - Stakeholders: Name match against existing; duplicates skipped
    - **Scan tracking**: Each document stamped with `granola_scanned_at` after processing
      - Future scans only process documents where `granola_scanned_at IS NULL`
      - `force_rescan=true` parameter available to re-process all documents
    - **Source detection**: Filters documents where `obsidian_file_path` contains 'Granola'
    - **Backend**: `services/granola_scanner.py`, direct queries (avoids Cloudflare 1101 with ilike)
23. **PuRDy (Product Requirements Document)**: Standalone feature for AI-assisted product discovery
    - **Separate entry point**: `/purdy` route with dedicated layout for PuRDy-only users
    - **User access**: Controlled via `app_access` column in users table (values: 'thesis', 'purdy', 'all')
    - **Initiative-based workflow**: Each initiative contains documents, agent runs, and outputs
    - **Per-initiative document repository**: Upload documents that grow over time
    - **Output format selection**: Choose Comprehensive, Executive Summary, or Brief formats before running agents
    - **Mermaid diagram support**: Architecture and flow diagrams render visually in output viewer
    - **Six specialized agents** (v4.0 - consulting quality bar):
      - **Triage (v4.0)**: 5-minute GO/NO-GO with conviction - decision in first sentence, 250 words max
      - **Discovery Planner (v4.0)**: Design discovery humans execute - session plans, agendas, quantification gates, 350 words max
      - **Coverage Tracker (v4.0)**: Run iteratively during discovery - READY/GAPS/CRITICAL verdict, 280 words max
      - **Insight Extractor (v4.0)**: NEW - Distill raw transcripts into structured insights with evidence quotes, 500 words max
      - **Synthesizer (v4.0)**: 500-word decision document - decision in first sentence, leverage point, real names for accountability
      - **Tech Evaluation (v4.0)**: Platform recommendation with architecture diagrams and confidence-tagged estimates
    - **Discovery Loop**: Discovery Planner and Coverage Tracker work iteratively - run Coverage after each session, return to Planner if gaps
    - **Executive Summary Generator**: Extracts decision-forcing elements (leverage point, feedback loop, decision, first action, blocker) from any output
    - **v3.0 Scoring Rubric** (`RUBRIC-v3.0.md`): Outcome-based measurement with 3 tiers - Action Enablement (50%), Insight Quality (30%), Efficiency (20%)
    - **Discovery Templates**: Type-specific templates in system KB (Process Automation, Data Analytics, Tool Selection, Cross-Functional)
    - **Versioned outputs**: Each agent run produces versioned output stored in DB with markdown export
    - **Previous outputs feed forward**: Subsequent runs automatically include earlier agent outputs as context
    - **Global System KB**: 19 markdown files pre-loaded for all initiatives (methodology, frameworks, risk patterns)
    - **Initiative-scoped RAG chat**: Ask questions about initiative documents with source citations
    - **Multi-user sharing**: Invite members as owner/editor/viewer with role-based permissions
    - **Backend**: `/backend/services/purdy/` (6 service files), `/backend/api/routes/purdy.py`
    - **Frontend**: `/frontend/app/purdy/` (page, layout, detail), `/frontend/components/purdy/` (7 components)
    - **Database**: 11 tables with `purdy_` prefix (initiatives, documents, chunks, runs, outputs, etc.)

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
    /tasks       - Kanban task management
    /opportunities - AI opportunity pipeline
    /meeting-prep - Stakeholder briefing pages
    /intelligence - Analytics and engagement trends
    /admin       - Admin dashboard
    /purdy       - PuRDy standalone feature (Product Requirements Document)
  /components    - React components
    /kb          - Knowledge Base components (KBDocumentsContent)
    /tasks       - Kanban board components (TaskKanbanBoard, TaskCard, etc.)
    /purdy       - PuRDy components (DocumentList, AgentRunner, OutputViewer, etc.)
  /contexts      - AuthContext, HelpChatContext, ThemeContext

/backend
  /api/routes    - FastAPI endpoints
  /agents        - Agent implementations (20 agents)
  /services      - Business logic including transcript_analyzer, operator_tools
    /purdy       - PuRDy services (initiative, document, agent, chat, sharing, system_kb)
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
- Facilitator invites ONE agent at a time (never "Capital and Sage, thoughts?")
- After agent responds, Facilitator returns to bridge/synthesize or invite next agent
- Creates natural back-and-forth conversation rhythm

**Reporter Domain Labels (No Agent Names):**
- Reports use domain labels: "Financial analysis shows..." NOT "Capital noted..."
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
agents                       -- Agent registry (21 agents) with capabilities column
agent_instruction_versions   -- Per-agent versioned instructions (single source of truth)
agent_handoffs               -- Agent-to-agent handoff tracking
agent_knowledge_base         -- Document-to-agent links for RAG (with relevance_score)

-- Stakeholder Management
stakeholders                 -- CRM-style tracking with priority_level, pain_points, win_conditions
stakeholder_candidates       -- Auto-extracted stakeholders pending user review (accept/reject/merge)
stakeholder_insights         -- Extracted insights from transcripts
engagement_level_history     -- Historical engagement level tracking for trends

-- Meeting Intelligence
meeting_transcripts          -- Processed transcript metadata
meeting_rooms                -- Multi-agent meeting sessions
meeting_room_participants    -- Agents in each meeting
meeting_room_messages        -- Messages with agent attribution

-- Task Management
project_tasks                -- Kanban tasks with status, priority, assignee, team, linked_opportunity_id
task_comments                -- Comments on tasks
task_history                 -- Status/priority/assignee change history

-- Business Intelligence (Project Triage)
ai_opportunities             -- Tier-scored AI opportunities with department/owner, justifications, and scoring_confidence
opportunity_conversations    -- Q&A history for opportunity detail modal
roi_opportunities            -- Identified ROI opportunities

-- Research Intelligence (Atlas)
research_tasks               -- Research task queue and history
research_schedule            -- Daily/weekly research schedule by focus area
research_sources             -- Credible sources with tier ratings (1-4)
knowledge_gaps               -- Detected knowledge gaps from agent conversations
agent_topic_mapping          -- Maps topics to relevant agents for distribution

-- Glean Platform Evaluation (Glean Evaluator)
glean_connectors             -- Registry of OOB, custom, and requested Glean connectors
glean_connector_requests     -- Gap tracking for connector prioritization
glean_connector_gaps (view)  -- Prioritized view of requested connectors

-- Obsidian Vault Sync
obsidian_vault_configs       -- User vault configuration with sync options
obsidian_sync_state          -- Per-file sync state for incremental sync (file_path, hash, mtime)
obsidian_sync_log            -- Sync operation history and error tracking

-- Career Intelligence (Compass)
compass_status_reports       -- Career status reports with 5-dimension rubric scores and AI justifications

-- PuRDy (Product Requirements Document)
purdy_initiatives            -- Initiative container with status (draft, triaged, in_discovery, synthesized, evaluated, archived)
purdy_initiative_members     -- Multi-user sharing with role (owner, editor, viewer)
purdy_documents              -- Per-initiative document repository
purdy_document_chunks        -- Chunked + embedded for RAG (scoped to initiative)
purdy_runs                   -- Each agent run with status, timing, token usage
purdy_run_documents          -- Tracks which documents were used in each run
purdy_outputs                -- Versioned agent outputs with structured fields (recommendation, tier_routing, confidence_level)
purdy_conversations          -- Initiative chat sessions
purdy_messages               -- Chat messages with source citations
purdy_system_kb              -- Global methodology KB (19 files shared across all initiatives)
purdy_system_kb_chunks       -- Chunked + embedded KB for RAG
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
| 016 | add_glean_evaluator_agent | Glean Evaluator agent + connector registry tables |
| 016 | rename_fortuna_to_capital | Rename finance agent from Fortuna to Capital |
| 017 | engagement_history | Engagement level history tracking for trends |
| 018 | project_triage | AI opportunities, stakeholder triage fields, Operator context |
| 019 | document_auto_classification | Auto-classification columns + RPC with agent filtering |
| 019 | task_management | Kanban tasks, comments, status history |
| 040 | add_compass_agent | Compass (Career Coach) agent for win tracking |
| 021 | obsidian_sync | Obsidian vault configs, sync state, and sync logs |
| 022 | opportunity_conversations | Opportunity conversations table |
| 023 | add_manual_agent | Manual (Documentation Assistant) agent |
| 025 | opportunity_justifications | AI-generated justification columns for opportunities |
| 026 | compass_status_reports | Career status report storage with 5-dimension rubric scores |
| 027 | compass_improvement_actions | Improvement actions column for career status reports |
| 027 | add_taskmaster_agent | Taskmaster agent for task discovery and tracking |
| 028 | document_task_scan_tracking | Track when documents were scanned for tasks (prevents duplicates) |
| 030 | stakeholder_candidates | Auto-extracted stakeholders pending review, document scan tracking |
| 033 | opportunity_candidates | Opportunity candidates table with deduplication support |
| 034 | project_name_and_team | Team field for tasks, project naming for opportunities, linked_opportunity_id |
| 035 | opportunity_scoring_confidence | scoring_confidence (0-100) and confidence_questions array for opportunities |
| 036 | task_candidates_opportunity_link | linked_opportunity_id and source_opportunity_id for task_candidates |
| 038 | purdy_schema | PuRDy tables (initiatives, documents, chunks, runs, outputs, conversations, system KB) |
| 047 | purdy_outcome_tracking | Outcome tracking: decided_at, launched_at, completed_at, stakeholder_rating, decision_velocity_days |

## Environment Variables

See `/frontend/.env.example` and `/backend/.env.example` for complete reference.

Key variables:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` (graph database)
- `ANTHROPIC_API_KEY` (Claude)
- `VOYAGE_API_KEY` (embeddings)
- `MEM0_API_KEY` (agent memory)
- `PURDY_REPO_PATH` (path to purdy-cf repo for agent prompts and KB files)
- `PURDY_AGENT_MODEL` (Claude model for PuRDy agent runs, default: claude-sonnet-4-20250514)

## Planning Documents

- `/docs/CONTEXT.md` - Full discovery context
- `/docs/planning/IMPLEMENTATION_PLAN.md` - Detailed implementation roadmap
- `/docs/planning/2024-12-26-planning-session.md` - Planning session transcript

## Testing & Code Quality

### Testing Plan (Primary Reference)
**`/docs/testing/TESTING_PLAN.md`** - Comprehensive testing guide that should be consulted and updated with each test run. Contains:
- Quick start commands
- Test file overview (272+ tests)
- Isolation patterns for import chain issues
- Code quality checks
- Templates for new tests
- Troubleshooting guide

### Testing Infrastructure
- `/docs/testing/TESTING_PLAN.md` - **Primary testing reference** (update after each test session)
- `/docs/testing/CODE_REVIEW_2026-01-16.md` - Latest comprehensive code review
- `/docs/testing/TESTING_PROMPT.md` - Reusable prompt for code review and auto-fix

### Running Tests
```bash
cd /Users/charlie.fuller/vaults/Contentful/thesis/backend

# Run all isolated tests (recommended - fast, no import issues)
uv run pytest tests/test_document_classifier.py tests/test_tasks.py \
  tests/test_opportunities.py tests/test_engagement.py tests/test_agents_new.py -v

# Run specific test file
uv run pytest tests/test_opportunities.py -v

# Run with verbose output
uv run pytest tests/ -v --tb=short
```

### Test Coverage (January 2026)
| Test File | Tests | Status |
|-----------|-------|--------|
| test_document_classifier.py | 38 | PASS |
| test_tasks.py | 34 | PASS |
| test_opportunities.py | 102 | PASS |
| test_engagement.py | 36 | PASS |
| test_agents_new.py | 55 | PASS |
| test_obsidian_sync.py | 45+ | PASS |
| test_vibe_coding_bugs.py | 34 | PASS |
| test_rigorous.py | 65 | PASS |

### Code Quality Targets
| Metric | Target | Current |
|--------|--------|---------|
| Code Quality Score | 9.0/10 | 9.3/10 |
| Test Pass Rate | 100% | 100% |
| Bare except blocks | 0 | 0 |
| Print statements (prod) | 0 | 2 (docs only) |

## Important Files

### Backend
- `/backend/main.py` - FastAPI app entry point
- `/backend/agents/` - Agent implementations (21 agents)
- `/backend/agents/agent_factory.py` - Agent creation and registration
- `/backend/agents/base_agent.py` - Base class with instruction loading
- `/backend/agents/atlas.py` - Research agent with web search capability
- `/backend/agents/glean_evaluator.py` - Glean platform fit assessment agent
- `/backend/agents/compass.py` - Career coaching agent for win tracking and status reports
- `/backend/agents/taskmaster.py` - Personal accountability agent for task discovery and tracking
- `/backend/agents/manual.py` - Documentation assistant agent for in-app help
- `/backend/services/transcript_analyzer.py` - Meeting transcript analysis
- `/backend/services/meeting_orchestrator.py` - Multi-agent meeting coordination
- `/backend/services/instruction_loader.py` - XML instruction file loading
- `/backend/services/research_scheduler.py` - Daily Atlas research scheduler
- `/backend/services/research_context.py` - Topic prioritization from platform context
- `/backend/services/agent_observer.py` - Cross-agent conversation monitoring
- `/backend/services/web_researcher.py` - Anthropic web search with credibility filtering
- `/backend/services/operator_tools.py` - Project triage context injection for Operator
- `/backend/services/engagement_calculator.py` - Automatic stakeholder engagement level calculation
- `/backend/services/engagement_scheduler.py` - Weekly engagement recalculation scheduler
- `/backend/services/document_classifier.py` - Hybrid keyword + LLM document classification
- `/backend/services/obsidian_sync.py` - Obsidian vault sync: file watching, frontmatter parsing, wikilink conversion
- `/backend/services/career_status_report.py` - Career status report generation with 5-dimension rubric
- `/backend/services/task_auto_extractor.py` - Auto-extract tasks from KB documents on upload (background)
- `/backend/services/task_extractor.py` - LLM task extraction with natural prompt (Claude Sonnet)
- `/backend/services/stakeholder_extractor.py` - LLM extraction of stakeholders from meeting documents
- `/backend/services/stakeholder_scanner.py` - Coordinates manual stakeholder scanning workflow
- `/backend/services/stakeholder_deduplicator.py` - Detects potential matches with existing stakeholders
- `/backend/services/stakeholder_linker.py` - Links stakeholders to related opportunities/tasks
- `/backend/services/graph/query_service.py` - Neo4j graph queries including `get_meeting_context()` for stakeholder/concern retrieval
- `/backend/services/graph/connection.py` - Neo4j connection management
- `/backend/system_instructions/agents/*.xml` - Agent behavior configuration (Gigawatt v4.0)
- `/backend/system_instructions/shared/smart_brevity.xml` - Mandatory response format directive + KB usage rules
- `/backend/system_instructions/shared/conversational_awareness.xml` - Multi-agent coherence directive (included by smart_brevity.xml)
- `/backend/services/chat_agent_service.py` - Agent selection, @mention parsing, instruction loading for chat
- `/backend/api/routes/chat.py` - Chat endpoints including Dig Deeper and agent routing
- `/backend/api/routes/meeting_rooms.py` - Meeting room CRUD and streaming
- `/backend/api/routes/agents.py` - Agent management endpoints (note: static routes like `/documents/available` must be defined before parameterized routes like `/{agent_id}/documents`)
- `/backend/api/routes/documents.py` - Document CRUD, upload, processing, classification, and agent assignment endpoints
- `/backend/api/routes/research.py` - Atlas research API endpoints
- `/backend/api/routes/glean_connectors.py` - Glean connector registry and gap tracking endpoints
- `/backend/api/routes/tasks.py` - Kanban task management CRUD, transcript extraction, and auto-extraction
- `/backend/api/routes/compass.py` - Compass career status report generation and history endpoints
- `/backend/api/routes/opportunities.py` - AI opportunity pipeline management with detail modal, justification, and candidate endpoints
- `/backend/api/routes/discovery.py` - Unified discovery endpoints for pending candidates (tasks, opportunities, stakeholders)
- `/backend/services/opportunity_context.py` - Vector search for opportunity-related KB documents
- `/backend/services/opportunity_chat.py` - Q&A chat service for opportunity detail modal
- `/backend/services/opportunity_justification.py` - AI-generated justifications using Claude Haiku
- `/backend/services/opportunity_confidence.py` - Scoring confidence rubric evaluation (0-100% based on completeness)
- `/backend/services/opportunity_kb_sync.py` - KB change detection and opportunity re-evaluation
- `/backend/services/opportunity_taskmaster.py` - Taskmaster chat for breaking opportunities/projects into tasks
- `/backend/scripts/generate_all_justifications.py` - Batch generation script for existing opportunities
- `/backend/api/routes/meeting_prep.py` - Stakeholder briefing endpoints
- `/backend/api/routes/stakeholder_metrics.py` - KPI tracking with validation status
- `/backend/api/routes/admin.py` - Admin dashboard with real API health checks
- `/backend/api/routes/obsidian_sync.py` - Obsidian vault configuration and sync API endpoints
- `/backend/scripts/obsidian_watcher.py` - CLI script for background vault file watching
- `/backend/scripts/seed_manual_docs.py` - CLI script to seed Manual agent with platform documentation
- `/backend/api/routes/purdy.py` - PuRDy API endpoints (initiatives, documents, runs, outputs, chat, sharing)
- `/backend/services/purdy/__init__.py` - PuRDy services module exports
- `/backend/services/purdy/initiative_service.py` - Initiative CRUD operations
- `/backend/services/purdy/document_service.py` - Document upload, chunking, embedding, RAG search
- `/backend/services/purdy/agent_service.py` - Load agent prompts from filesystem, run agents, parse outputs
- `/backend/services/purdy/chat_service.py` - Initiative-scoped RAG chat with source citations
- `/backend/services/purdy/sharing_service.py` - Multi-user sharing with role-based permissions
- `/backend/services/purdy/system_kb_service.py` - Global KB sync from filesystem, vector search
- `/backend/scripts/sync_purdy_kb.py` - CLI script to sync KB files to database

### Frontend
- `/frontend/app/layout.tsx` - Root layout with providers
- `/frontend/components/ChatInterface.tsx` - Main chat with agent selection and Dig Deeper
- `/frontend/components/AgentSelector.tsx` - Agent dropdown selector component
- `/frontend/components/AgentIcon.tsx` - Agent icons and color mapping
- `/frontend/components/ChatMessage.tsx` - Message display with agent badges
- `/frontend/app/meeting-room/` - Meeting room pages
- `/frontend/app/tasks/` - Kanban task management
- `/frontend/app/opportunities/` - AI opportunity pipeline
- `/frontend/components/opportunities/OpportunityDetailModal.tsx` - Full detail modal with score justification, confidence meter, related docs, Q&A, edit mode, and Taskmaster chat
- `/frontend/components/opportunities/OpportunityScatterPlot.tsx` - ROI vs Effort scatter plot with quadrant analysis
- `/frontend/components/opportunities/DocumentViewerModal.tsx` - Inline document viewer modal with markdown rendering
- `/frontend/components/opportunities/ScoreJustification.tsx` - Visual score breakdown component
- `/frontend/components/opportunities/TaskmasterChatSection.tsx` - Taskmaster chat for breaking projects into tasks
- `/frontend/app/meeting-prep/` - Stakeholder briefing pages
- `/frontend/app/intelligence/` - Analytics and engagement trends
- `/frontend/app/admin/agents/` - Agent admin interface
- `/frontend/components/tasks/` - Kanban board components (TaskKanbanBoard, TaskCard, etc.)
- `/frontend/components/compass/CareerStatusReportModal.tsx` - Career status report display modal with 5-dimension scores
- `/frontend/components/compass/ScoreDimensionCard.tsx` - Individual dimension score card with justification
- `/frontend/components/kb/ClassificationReviewBanner.tsx` - Document classification review UI
- `/frontend/components/EngagementTrendsChart.tsx` - Stakeholder engagement visualization
- `/frontend/components/discovery/UnifiedDiscoveryPanel.tsx` - Dashboard panel with tabs for all pending candidates
- `/frontend/components/opportunities/OpportunityCandidateReviewModal.tsx` - Inline review for opportunity candidates
- `/frontend/components/opportunities/ProjectNameModal.tsx` - Modal for naming projects on status change
- `/frontend/components/stakeholders/StakeholderCandidateCard.tsx` - Candidate card with accept/reject/merge actions
- `/frontend/components/stakeholders/StakeholderCandidatesSection.tsx` - Scan controls and candidate list for Intelligence page
- `/frontend/app/purdy/page.tsx` - PuRDy initiative list page
- `/frontend/app/purdy/layout.tsx` - PuRDy-specific layout with access control
- `/frontend/app/purdy/[id]/page.tsx` - Initiative detail page with tabs (documents, runs, chat)
- `/frontend/components/purdy/DocumentList.tsx` - Initiative document list with upload/delete
- `/frontend/components/purdy/DocumentUpload.tsx` - Document upload with drag-and-drop
- `/frontend/components/purdy/AgentRunner.tsx` - Agent selection and execution with streaming
- `/frontend/components/purdy/OutputViewer.tsx` - Markdown output viewer with version switching
- `/frontend/components/purdy/InitiativeChat.tsx` - RAG chat component for initiative Q&A
- `/frontend/components/purdy/ShareModal.tsx` - Member management modal

### Database
- `/database/thesis_schema.sql` - Complete DB schema
- `/database/migrations/` - All migration scripts (001-034, 040)

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

### Granola Scanner Debugging
The Granola scanner (`/api/pipeline/granola/scan`) extracts opportunities, tasks, and stakeholders from meeting documents. If scans fail:

1. **Debug endpoint**: `GET /api/pipeline/granola/debug` - checks document storage URLs
2. **Check date filtering**: Default cutoff is Jan 5, 2026. Use `since_date` param to adjust:
   ```bash
   POST /api/pipeline/granola/scan?since_date=2025-01-01  # Scan older meetings
   POST /api/pipeline/granola/scan?days_back=90          # Last 90 days
   ```
3. **Background scan status**: Check job progress:
   ```bash
   GET /api/pipeline/granola/scan/job/{job_id}
   ```
4. **Empty content**: Documents may have been synced with 0 bytes. Check with:
   ```sql
   SELECT id, filename, original_date, storage_url FROM documents
   WHERE obsidian_file_path LIKE '%Granola%'
     AND granola_scanned_at IS NULL;
   ```
5. **Verify storage URL is accessible**: `curl -I "<storage_url>"` should return `content-length: > 0`
6. **Fix empty documents**: Delete and re-sync via `POST /api/obsidian/sync/full`

### Required RPC Functions
The Granola scanner uses RPC functions to avoid PostgREST `ilike` issues (Cloudflare Error 1101). Ensure these exist in Supabase:

- `get_granola_documents_to_scan(p_user_id, p_force_rescan)` - Returns unscanned Granola documents
- `get_granola_scan_status(p_user_id)` - Returns scan counts
- `check_duplicate_opportunity_candidate(p_client_id, p_title_prefix)` - Deduplication check
- `check_duplicate_task_candidate(p_client_id, p_title_prefix)` - Deduplication check
- `check_existing_stakeholder_candidate(p_client_id, p_name)` - Deduplication check
- `check_existing_stakeholder(p_client_id, p_name)` - Deduplication check
