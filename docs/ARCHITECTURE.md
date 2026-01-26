# Thesis Architecture Reference

This document contains detailed architecture documentation. For essential Claude Code instructions, see `/CLAUDE.md`.

## Agent Roster (21 Agents)

### Meta-Agents (Always Present in Meetings)
| Agent | Name | Purpose |
|-------|------|---------|
| Facilitator | Facilitator | Meeting orchestration - welcomes users, clarifies intent, routes to specialists, ensures balanced participation, invokes systems thinking before conclusions. |
| Reporter | Reporter | Meeting synthesis and documentation - creates unified summaries, action items, and executive briefs. Uses domain labels instead of agent names for shareable output. |

### Stakeholder Perspective Agents
| Agent | Name | Persona Alignment | Purpose |
|-------|------|-------------------|---------|
| Atlas | Research | Chris Baumgartner | GenAI research, Lean methodology, benchmarking |
| Capital | Finance | Raul Rivera III | ROI analysis, SOX compliance, business cases |
| Guardian | IT/Governance | Danny Leal | Security, compliance, shadow IT, vendor evaluation |
| Counselor | Legal | Ashley Adams | Contracts, AI risks, liability, data privacy |
| Sage | People | Chad Meek | Change management, human flourishing, adoption |
| Oracle | Meeting Intelligence | CIPHER v2.1 | Transcript analysis, stakeholder dynamics, sentiment extraction |

### Consulting/Implementation Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Strategist | Executive Strategy | C-suite engagement, organizational politics, governance |
| Architect | Technical Architecture | Enterprise AI patterns, RAG, integration, build vs. buy |
| Operator | Business Operations | Process optimization, automation, Project Triage pipeline |
| Pioneer | Innovation/R&D | Emerging technology, hype filtering, maturity assessment |

### Internal Enablement Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Catalyst | Internal Communications | AI messaging, employee engagement, AI anxiety |
| Scholar | Learning & Development | Training programs, champion enablement, adult learning |
| Echo | Brand Voice | Voice analysis, style profiling, AI emulation guidelines |
| Glean Evaluator | Can We Glean This? | Glean platform fit assessment, connector analysis |
| Compass | Career Coach | Win capture, performance tracking, check-in prep |
| Taskmaster | Personal Accountability | Task discovery, progress tracking, slippage alerts |
| Manual | Documentation Assistant | In-app help, feature explanation, troubleshooting |

### Systems/Coordination Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Nexus | Systems Thinking | Interconnections, feedback loops, leverage points |
| Coordinator | Thesis | Central orchestrator for chat, query routing |

## Capabilities Reference

### Core Features
1. **Agent Selection in Chat** - Select specific agents or use Auto mode with @mention syntax
2. **Knowledge Base** - Unified document management with auto-classification and agent-filtered RAG
3. **Meeting Intelligence** - Transcript analysis with stakeholder insights
4. **Stakeholder Tracking** - CRM-style tracking with auto-discovery from meetings
5. **Research Intelligence** - Atlas web research with credibility-tiered sources
6. **Agent Coordination** - Hybrid model for collaboration
7. **Persistent Memory** - Mem0 integration for cross-conversation learning

### Meeting & Collaboration
8. **Meeting Room** - Multi-agent collaboration with selected agents
9. **Autonomous Discussion** - Agents discuss with discourse moves (Question, Connect, Challenge, Extend, Synthesize)
10. **Dig Deeper** - One-click elaboration on responses

### Task & Project Management
11. **Auto-Generated Titles** - Conversation titles from initial message
12. **Task Management** - Kanban board with auto-extraction from documents
13. **Project Triage (Operator)** - AI opportunity pipeline with tier-based scoring
14. **Opportunities Pipeline** - Pipeline and Analysis tabs with scatter plot visualization

### Intelligence & Analytics
15. **Meeting Prep** - Stakeholder briefing pages
16. **Stakeholder Engagement Analytics** - Weekly recalculation with trend visualization
17. **Career Status Reports (Compass)** - 5-dimension rubric assessment

### Integrations
18. **Obsidian Vault Sync** - File watching, frontmatter parsing, wikilink conversion
19. **Enhanced RAG Search** - Original date tracking, document type filtering, recency boost

### Discovery & Pipeline
20. **Unified Discovery Inbox** - Tabs for Tasks, Opportunities, Stakeholders candidates
21. **Project Naming Workflow** - Required names for opportunities in active phases
22. **Granola Vault Scanner** - Extract opportunities, tasks, stakeholders from meeting notes

### DISCo (Discovery → Insights → Synthesis → Capabilities)
23. **DISCo Pipeline** - AI-assisted product discovery with 8 specialized agents across 4 stages:
    - **Discovery Stage**: Triage (GO/NO-GO with Problem Worth Solving gate), Discovery Planner
    - **Insights Stage**: Coverage Tracker, Insight Extractor (pattern library), Consolidator (decision doc)
    - **Synthesis Stage**: Strategist (cluster insights into initiative bundles)
    - **Capabilities Stage**: PRD Generator (engineering-ready PRDs from bundles), Tech Evaluation

**UI Sidebar Order (workflow sequence):**
| # | Agent | Color | v4.2 Persona Feature |
|---|-------|-------|---------------------|
| 1 | Triage | Blue | Problem Worth Solving gate (Mikki) |
| 2 | Discovery Planner | Amber | Session templates with agendas |
| 3 | Coverage Tracker | Purple | Gap analysis with session routing |
| 4 | Insight Extractor | Cyan | Pattern Library - 5 enterprise loops (Tyler) |
| 5 | Consolidator | Green | Metrics Dashboard + diagram reasoning (Chris) |
| 6 | Strategist | Emerald | Cluster insights into initiative bundles |
| 7 | PRD Generator | Rose | Engineering-ready PRDs from bundles |
| 8 | Tech Evaluation | Indigo | Build vs. buy with architecture diagrams |

**Note:** Synthesizer was merged into Consolidator (v4.2). Legacy outputs created by Synthesizer display under Consolidator.

**Prompt Version:** v4.2 (2026-01-25) - See `/backend/disco_agents/` (formerly `purdy_agents`, path alias still supported)
**Evaluation:** `/backend/disco_agents/EVALUATION-v4.2-RESULTS.md`
- Triage: 85/100 ADOPT - Problem gate working well
- Synthesizer: 78/100 REVIEW - Blocked term enforcement needed
- Insight Extractor: 82/100 ADOPT - Pattern Library adds value

## Database Schema

### Agent System
- `agents` - Agent registry (21 agents) with capabilities
- `agent_instruction_versions` - Per-agent versioned instructions
- `agent_handoffs` - Agent-to-agent handoff tracking
- `agent_knowledge_base` - Document-to-agent links for RAG

### Stakeholder Management
- `stakeholders` - CRM-style tracking
- `stakeholder_candidates` - Auto-extracted pending review
- `stakeholder_insights` - Extracted from transcripts
- `engagement_level_history` - Trend tracking

### Meeting Intelligence
- `meeting_transcripts` - Processed transcript metadata
- `meeting_rooms` - Multi-agent sessions
- `meeting_room_participants` - Agents per meeting
- `meeting_room_messages` - Messages with agent attribution

### Task Management
- `project_tasks` - Kanban tasks with status, priority, team
- `task_comments` - Comments on tasks
- `task_history` - Status/priority change history

### Business Intelligence
- `ai_opportunities` - Tier-scored opportunities with justifications
- `opportunity_conversations` - Q&A history
- `roi_opportunities` - Identified ROI opportunities

### Research Intelligence
- `research_tasks` - Research queue and history
- `research_schedule` - Daily/weekly schedule
- `research_sources` - Credible sources with tier ratings
- `knowledge_gaps` - Detected gaps from conversations
- `agent_topic_mapping` - Topics to agents mapping

### Glean Platform
- `glean_connectors` - Connector registry
- `glean_connector_requests` - Gap tracking
- `glean_connector_gaps` (view) - Prioritized view

### Obsidian Sync
- `obsidian_vault_configs` - User vault configuration
- `obsidian_sync_state` - Per-file sync state
- `obsidian_sync_log` - Sync operation history

### Career Intelligence
- `compass_status_reports` - Career status reports with rubric scores

### DISCo Tables (formerly PuRDy - `purdy_*` table names still accepted for backwards compatibility)
- `disco_initiatives` - Initiative container
- `disco_initiative_members` - Multi-user sharing
- `disco_documents` - Per-initiative documents
- `disco_document_chunks` - Chunked + embedded for RAG
- `disco_runs` - Agent run metadata
- `disco_run_documents` - Documents used per run
- `disco_outputs` - Versioned agent outputs (all agents)
- `disco_conversations` - Chat sessions
- `disco_messages` - Chat messages
- `disco_system_kb` - Global methodology KB
- `disco_system_kb_chunks` - KB chunks for RAG
- `disco_bundles` - Initiative bundles from Strategist (scores, rationale, dependencies)
- `disco_prds` - PRD documents from PRD Generator (structured + markdown)

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
| 008 | add_nexus_systems_thinking_agent | Nexus agent |
| 009-010 | add_bard_agent, rename_bard_to_echo | Echo (Brand Voice) agent |
| 011 | research_system | Atlas research tables |
| 012 | autonomous_discussion | Autonomous discussion mode |
| 013 | document_title | Title column for documents |
| 014-015 | add_facilitator_agent, add_reporter_agent | Meta-agents |
| 016 | add_glean_evaluator_agent | Glean Evaluator + connectors |
| 017 | engagement_history | Engagement level tracking |
| 018 | project_triage | AI opportunities, triage fields |
| 019 | document_auto_classification, task_management | Classification + Kanban |
| 021-023 | obsidian_sync, opportunity_conversations, add_manual_agent | Obsidian, Opportunities, Manual |
| 025-028 | opportunity_justifications through document_task_scan_tracking | Opportunity features |
| 030-036 | stakeholder_candidates through task_candidates_opportunity_link | Discovery pipeline |
| 038 | disco_schema | DISCo tables (formerly purdy_schema) |
| 040 | add_compass_agent | Compass agent |
| 047 | disco_outcome_tracking | Outcome tracking (formerly purdy_outcome_tracking) |
| 048 | disco_synthesis | DISCo bundles + PRDs tables |

## Important Files Reference

### Backend Core
- `/backend/main.py` - FastAPI entry point
- `/backend/agents/` - Agent implementations (21 agents)
- `/backend/agents/agent_factory.py` - Agent creation
- `/backend/agents/base_agent.py` - Base class with instruction loading

### Backend Services
- `/backend/services/transcript_analyzer.py` - Meeting analysis
- `/backend/services/meeting_orchestrator.py` - Multi-agent coordination
- `/backend/services/instruction_loader.py` - XML instruction loading
- `/backend/services/document_classifier.py` - Hybrid classification
- `/backend/services/obsidian_sync.py` - Vault sync
- `/backend/services/engagement_calculator.py` - Engagement levels
- `/backend/services/opportunity_*.py` - Opportunity services (context, chat, justification, confidence)
- `/backend/services/stakeholder_*.py` - Stakeholder services (extractor, scanner, deduplicator, linker)
- `/backend/services/task_*.py` - Task services (auto_extractor, extractor)
- `/backend/services/disco/` - DISCo services (8 agents) (formerly `purdy/`, path alias still supported)
- `/backend/services/graph/` - Neo4j services

### Backend API Routes
- `/backend/api/routes/chat.py` - Chat endpoints
- `/backend/api/routes/meeting_rooms.py` - Meeting room CRUD
- `/backend/api/routes/agents.py` - Agent management
- `/backend/api/routes/documents.py` - Document CRUD
- `/backend/api/routes/tasks.py` - Task management
- `/backend/api/routes/opportunities.py` - Opportunity pipeline
- `/backend/api/routes/disco.py` - DISCo endpoints (formerly `purdy.py`, route `/api/purdy/*` still accepted)

### Frontend Core
- `/frontend/app/layout.tsx` - Root layout
- `/frontend/components/ChatInterface.tsx` - Main chat
- `/frontend/components/AgentIcon.tsx` - Agent icons and colors (single source of truth)

### Frontend Features
- `/frontend/app/meeting-room/` - Meeting rooms
- `/frontend/app/tasks/` - Kanban board
- `/frontend/app/opportunities/` - Opportunity pipeline
- `/frontend/app/disco/` - DISCo feature (formerly `purdy/`, route `/purdy` still redirects)
- `/frontend/components/disco/` - DISCo components (7 files) (formerly `purdy/`)

### DISCo Agent Prompts
- `/backend/disco_agents/` - Agent prompt definitions (versioned markdown) (formerly `purdy_agents/`, path alias still supported)
  - `triage-v4.2.md`, `discovery-planner-v4.1.md`, `coverage-tracker-v4.1.md`
  - `insight-extractor-v4.2.md`, `consolidator-v4.2.md`, `tech-evaluation-v4.0.md`
  - `strategist-v1.0.md`, `prd-generator-v1.0.md`
  - `RUBRIC-v3.0.md` - Scoring rubric for evaluation
  - `EVALUATION-v4.2-RESULTS.md` - Latest evaluation results
- `/frontend/components/opportunities/` - Opportunity components
- `/frontend/components/tasks/` - Task components

### Configuration
- `/backend/system_instructions/agents/*.xml` - Agent behavior (Gigawatt v4.0)
- `/backend/system_instructions/shared/smart_brevity.xml` - Response format
- `/backend/system_instructions/shared/conversational_awareness.xml` - Multi-agent coherence

## Agent Instruction Methodology

Agent system instructions use the **Gigawatt v4.0 RCCI Framework**:

- **XML Structure**: `<version>`, `<role>`, `<context>`, `<capabilities>`, `<instructions>`, `<criteria>`, `<few_shot_examples>`, `<wisdom>`, `<anti_patterns>`
- **Smart Brevity**: 100-150 words max, ask-first for unclear intent
- **Conversational Awareness**: Build on each other's points in meetings
- **Evidence-Based**: All insights backed by quotes/data
- **No Emojis**: Professional formatting throughout

### Smart Brevity Format
1. **The Big Thing** (1-2 sentences) - Key insight with metric
2. **Why It Matters** (1-2 sentences) - Business impact
3. **Key Details** (3-5 bullets or table) - Scannable facts
4. **Dig-Deeper Links** (2-4 links) - Expandable via `[text](dig-deeper:section_id)`

### Meeting Room Behavior
- **50-100 words MAX** per agent turn
- **75 words MAX** in autonomous discussions
- ONE key insight per turn
- Facilitator invites ONE agent at a time
- Reporter uses domain labels, not agent names

See `/docs/AGENT_GUARDRAILS.md` for complete rules.

## Testing Reference

### Test Files
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

### Running Tests
```bash
# From the repo root:
cd backend

# Run all isolated tests
uv run pytest tests/test_document_classifier.py tests/test_tasks.py \
  tests/test_opportunities.py tests/test_engagement.py tests/test_agents_new.py -v

# Run specific test file
uv run pytest tests/test_opportunities.py -v
```

See `/docs/testing/TESTING_PLAN.md` for comprehensive testing guide.

## Security & Credentials Management

### Credential Storage

Credentials are managed through a layered approach with multiple fallback options:

| Priority | Method | Description |
|----------|--------|-------------|
| 1 | 1Password CLI | Secure vault storage with Touch ID authentication |
| 2 | Environment Variables | Standard env vars (for CI/CD) |
| 3 | dotenvx | Encrypted `.env.vault` with key-based decryption |

### 1Password Integration

All Thesis credentials are stored in 1Password:
- **Vault**: Employee
- **Item**: Thesis Backend
- **Item ID**: `bqvwidzwtlswzndi5wjq33gon4`

**Retrieve a credential:**
```bash
op item get bqvwidzwtlswzndi5wjq33gon4 --field SUPABASE_URL --reveal
```

**Run scripts with 1Password:**
```bash
USE_1PASSWORD=1 python scripts/your_script.py
```

### Credentials Module

All scripts use the centralized credentials module (`/backend/scripts/lib/credentials.py`):

```python
from scripts.lib.credentials import get_credentials, get_supabase_client

# Get all credentials
creds = get_credentials()

# Get a configured Supabase client
supabase = get_supabase_client()
```

### Available Credentials

| Key | Description |
|-----|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase admin service key |
| `SUPABASE_JWT_SECRET` | JWT signing secret for auth |
| `ANTHROPIC_API_KEY` | Claude API key |
| `VOYAGE_API_KEY` | Voyage AI embeddings API |
| `NEO4J_URI` | Neo4j Aura connection string |
| `NEO4J_USERNAME` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |
| `MEM0_API_KEY` | Mem0 memory API key |

### Security Documentation

- **Security Assessment**: `/docs/security/SECURITY_ASSESSMENT_REPORT.md`
- **1Password Command**: `/backend/.claude/commands/1password.md`

## Removed Features (December 2025)

- **Quick Prompts** - Removed in favor of agent commands
- **Projects** - Replaced by vector DB + Neo4j graph
- **Templates** - Moved to agent instructions
- **Core Documents** - All documents now equally deletable
- **Standalone Documents Page** - Integrated into `/kb`

Related cleanup: `user_quick_prompts` table, `documents.is_core_document` column
