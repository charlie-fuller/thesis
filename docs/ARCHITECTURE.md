# Thesis Architecture Reference

This document contains detailed architecture documentation. For essential Claude Code instructions, see `/CLAUDE.md`.

## Agent Roster (22 Agents)

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
| Kraken | Task Automation | Evaluates tasks for AI workability, executes approved tasks, computes agenticity scores |
| Discovery Agent | Initiative Discovery | Initiative framing, context synthesis, discovery methodology (internal key: initiative_agent) |
| Manual | Documentation Assistant | In-app help, feature explanation, troubleshooting |

### Systems/Coordination Agents
| Agent | Name | Purpose |
|-------|------|---------|
| Nexus | Systems Thinking | Interconnections, feedback loops, leverage points |
| Coordinator | Thesis | Central orchestrator for chat, query routing |

## Capabilities Reference

### Core Features
1. **Agent Selection in Chat** - Select specific agents or use Auto mode with @mention syntax
2. **Knowledge Base** - Finder-style document browser with folder tree sidebar, source/search filtering, and agent-filtered RAG
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
12. **Task Management** - Kanban board with auto-extraction from documents, Taskmaster sequenced task plans from chat, notes field, cascade filtering by team/project/assignee
13. **Project Triage (Operator)** - AI project pipeline with tier-based scoring
14. **Projects Pipeline** - Pipeline and Analysis tabs with scatter plot visualization, project-scoped chat with RAG search limited to linked documents

### Intelligence & Analytics
15. **Meeting Prep** - Stakeholder briefing pages
16. **Stakeholder Engagement Analytics** - Weekly recalculation with trend visualization
17. **Career Status Reports (Compass)** - 5-dimension rubric assessment

### Integrations
18. **Obsidian Vault Sync** - File watching, frontmatter parsing, wikilink conversion, binary doc support (PDF/DOCX/XLSX/PPTX with OCR fallback), move/rename detection preserves document IDs, linked documents protected from orphan cleanup, remote upload endpoint with file_mtime for accurate date extraction, future-date guard prevents false date matches
19. **Enhanced RAG Search** - Document type auto-classification (transcript, notes, report, etc.), date filtering for recency queries, 20% recency boost for recent docs

### Discovery & Pipeline
20. **Unified Discovery Inbox** - Tabs for Tasks, Projects, Stakeholders candidates with deduplication
21. **Project Naming Workflow** - Required names for projects in active phases
22. **Meeting Scanner** - Heuristic-based document classification extracts projects, tasks, stakeholders from meeting notes (transcripts, summaries, 1:1s)

### DISCO (Discovery → Insights → Synthesis → Convergence → Operationalize)
23. **DISCO KB Integration** - Uses Knowledge Base as single source of truth for documents. Link existing KB documents to discoveries via browser modal with search/tag filtering. Chat includes linked document list for visibility plus vector search for content queries.
24. **DISCO Pipeline** - AI-assisted product discovery with 4 consolidated stage-aligned agents and human-in-the-loop checkpoints:
    - **Discovery Guide**: Validates problem, plans discovery sessions, tracks coverage (consolidates: Triage, Discovery Planner, Coverage Tracker). v1.4 adds Five Whys, root cause analysis, and framing extraction from documents.
    - **Insight Analyst**: Extracts patterns and creates decision document (consolidates: Insight Extractor, Consolidator)
    - **Initiative Builder**: Clusters insights into scored proposed initiatives (consolidates: Strategist)
    - **Requirements Generator**: Produces PRD with technical recommendations, tool/platform guidance, value alignment confirmation, and AI risk/compliance review (consolidates: PRD Generator, Tech Evaluation). v1.2 adds platform recommendations and eval/QA plans.
25. **Flexible Output Types** - Proposed initiative approval generates one of three document types based on purpose:
    - **PRD** (default): Product Requirements Document for build/development proposed initiatives
    - **Evaluation Framework**: Weighted criteria matrix, platform comparison, recommendation for research/evaluation proposed initiatives
    - **Decision Framework**: Decision criteria, stakeholder input, risk/benefit assessment for governance decisions
    - AI suggests appropriate output type based on proposed initiative content analysis
    - All output types include value alignment confirmation, tool/platform recommendations, and AI risk/compliance review
26. **Create Project from Proposed Initiative** - Two paths to project creation:
    - **Direct**: Approved proposed initiatives can spawn projects directly with score mapping (impact→roi_potential, feasibility→effort, urgency→alignment)
    - **Via PRD**: Approved PRDs can spawn projects with AI-extracted fields (title, description, department, scoring dimensions, confidence indicators)
    - Optional task extraction from PRD requirements section
    - Projects linked to parent discovery with `source_type: disco_prd`
27. **Discovery Projects View** - Dedicated endpoint for querying projects linked to a discovery with source badges
28. **Discovery Goal Alignment** - Analyzes discoveries against IS FY27 strategic goals (same 4-pillar framework as projects). Uses rich context from agent outputs for scoring. Project roll-up shows linked projects' alignment scores with distribution.
29. **Discovery Throughline** - Structured input framing for discoveries: problem statements, hypotheses (assumption/belief/prediction), known gaps (data/people/process/capability), and desired outcome state. Throughline is threaded through all 4 DISCO agent stages and resolved at convergence with hypothesis resolutions, gap statuses, state changes, and "So What?" analysis.
30. **Framing Extraction** - Two paths: (1) Triage agent automatically suggests throughline elements from linked documents with post-triage review panel, (2) Discovery Agent in chat can discuss framing conversationally and propose structured `<framing_proposal>` blocks that users selectively apply via FramingProposalCard.
31. **Value Alignment** - Flexible alignment tracking per discovery: target department, KPIs, department goals, company priority, strategic pillar, notes. Populated progressively as information emerges during discovery.
32. **Sponsor/Stakeholder Linking** - Discoveries can be linked to an executive sponsor and multiple stakeholders from the stakeholder database.
33. **Resolution Annotations** - Users can override agent-assigned hypothesis/gap resolution statuses with their own assessment and notes. Annotations persist alongside agent output.
34. **Task Source Tracking** - Tasks created from DISCO convergence state changes include `source_initiative_id` and `source_disco_output_id` for full traceability back to the discovery process.
35. **Gap Taxonomy** - Reference taxonomy for gap categorization (data/people/process/capability) with investigation focus guidance. Available as KB reference for Discovery Guide agent.
36. **Initiative Folder Links** - Link vault folders to discoveries. When a folder is linked, all documents in that folder are automatically linked to the initiative. Folder link state tracked in `disco_initiative_folder_links`. Removal sync unlinks documents when folders are removed.
37. **Discovery Agent Context Injection** - The Discovery Agent (chat) receives full initiative context via `build_initiative_context()`: initiative metadata, throughline, agent output summaries, linked document names, and value alignment. Previously the agent claimed context but received none.
38. **Project Creation from Discovery** - Create projects directly from the discovery detail page via ProjectCreateModal, with automatic initiative linking.
39. **Kraken Agent (Task Automation)** - Evaluates project tasks for autonomous AI execution using a 5-dimension confidence framework (information sufficiency, output clarity, execution feasibility, completeness achievable, domain fit). Categorizes tasks as automatable (70-100%), assistable (40-69%), or manual (<40%). Computes agenticity score per project. Executes approved tasks non-destructively: output saved as task comments and KB documents. Uses web search for real-time research. Never modifies task status.
40. **DISCO Process Map** - Standalone HTML visualization of the complete DISCO pipeline at `/disco-process-map.html`. Shows all 5 stages, 4 checkpoint gates, agent details, throughline system, output document types, multi-pass synthesis, and operationalization paths.
41. **AI Platform Governance Maps** - Standalone HTML visualizations for platform governance: Platform Process Map (`/platform-process-map.html`) covers approved platforms (Glean, Gemini/Gems, NotebookLM, Claude, MuleSoft, Custom), comparison matrix, quick decision paths, and hub-and-spoke governance. Platform Decision Tree (`/platform-decision-tree.html`) provides guided platform selection. Both embedded as tabs on the DISCO page.
42. **Thesis Manifesto** - 10 core organizational principles accessible from top navigation. Tabbed layout: Principles (cards with core statement and elaboration) and XML (agent-loadable format). Principles cover state change orientation, problems before solutions, multiple perspectives, trace connections, and more.
43. **Agent Selection Guide (Deductive Discovery)** - Redesigned from tool-picker to situational discovery process at `/agent-selection-tree.html`. Three modes: Discovery Mode (3-step wizard: Situation → Context → Recommendation), Browse All Agents (22-agent catalog), Visual Map (full decision tree visualization). Results recommend primary + supporting agents with reasoning, approach, and manifesto alignment.
44. **Iframe Theme Inheritance** - All 8 embedded HTML visualizations (agent-selection-tree, data-flow-map, meeting-rooms-process-map, throughline-process-map, platform-process-map, platform-decision-tree, kraken-process-map, project-scoring-map) sync with the parent app's theme. Script reads ThemeContext CSS custom properties and computes a full gray ramp via color interpolation. Supports dark/light detection with polling and MutationObserver for runtime changes.

**Consolidated Agent Architecture (v1.2):**
| # | Agent | Color | Consolidates | Checkpoint After |
|---|-------|-------|--------------|------------------|
| 1 | Discovery Guide | Blue | Triage + Discovery Planner + Coverage Tracker | Ready to Execute Discovery? |
| 2 | Insight Analyst | Cyan | Insight Extractor + Consolidator | Ready for Initiative Building? |
| 3 | Initiative Builder | Green | Strategist | Ready for Requirements? |
| 4 | Requirements Generator | Rose | PRD Generator + Tech Evaluation | Ready for Engineering Handoff? |

**Human-in-the-Loop Checkpoints:**
- Each checkpoint is a gate between agents requiring human approval
- Checkpoints have 4 states: `locked`, `needs_review`, `approved`, `stale`
- Checklist items must be completed before approval
- Staleness detected when new documents added after approval
- Re-running an agent resets the checkpoint to `needs_review`

**Legacy Agent Support:** Original 8 agents available via `include_legacy=true` query param on `/api/disco/agents`. Legacy outputs display correctly in UI.

**Prompt Version:** v1.4 Consolidated (2026-02-13) - Discovery Guide v1.4 adds Five Whys/root cause analysis and framing extraction. Requirements Generator v1.4 adds tool/platform recommendations, eval/QA plans, value alignment confirmation, AI risk/compliance review. See `/backend/disco_agents/`
**Previous Version:** v1.1 (2026-02-12) - Throughline awareness, v1.0 (2026-02-02), v4.2 (2026-01-25) - Legacy agents still available for backwards compatibility

## Database Schema

### Agent System
- `agents` - Agent registry (22 agents) with capabilities
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
- `project_tasks` - Kanban tasks with status, priority, team, embeddings, notes, `source_initiative_id` and `source_disco_output_id` for DISCO traceability
- `task_candidates` - Auto-extracted pending review with dedup tracking
- `task_comments` - Comments on tasks
- `task_history` - Status/priority change history

### Project Management
- `ai_projects` - Tier-scored AI projects with justifications, `agenticity_score`/`agenticity_evaluation` JSONB for Kraken results
- `project_candidates` - Auto-extracted pending review with dedup tracking
- `project_conversations` - Q&A history
- `project_stakeholder_link` - Links stakeholders to projects with roles
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

### DISCO Tables (formerly PuRDy - `purdy_*` table names still accepted for backwards compatibility)
- `disco_initiatives` - Discovery container (includes `goal_alignment_score`, `goal_alignment_details` for strategic alignment, `throughline` JSONB for structured input framing, `value_alignment` JSONB for KPIs/goals/pillar, `target_department`, `sponsor_stakeholder_id`, `stakeholder_ids UUID[]`, `resolution_annotations` JSONB for user overrides)
- `disco_initiative_members` - Multi-user sharing
- `disco_documents` - Per-discovery documents
- `disco_document_chunks` - Chunked + embedded for RAG
- `disco_runs` - Agent run metadata
- `disco_run_documents` - Documents used per run
- `disco_outputs` - Versioned agent outputs (all agents), `last_run_at` for staleness tracking, `throughline_resolution` JSONB for convergence resolution, `triage_suggestions` JSONB for framing extraction
- `disco_conversations` - Chat sessions
- `disco_messages` - Chat messages
- `disco_system_kb` - Global methodology KB
- `disco_system_kb_chunks` - KB chunks for RAG
- `disco_bundles` - Proposed initiatives from Strategist (scores, rationale, dependencies)
- `disco_prds` - PRD documents from Requirements Generator (structured + markdown)
- `disco_checkpoints` - Human-in-the-loop approval gates between consolidated agents (status, checklist_items, approved_at/by)
- `disco_initiative_folder_links` - Vault folder-to-initiative links for auto-document association (initiative_id, folder_path, linked_by)

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
| 038 | disco_schema | DISCO tables (formerly purdy_schema) |
| 040 | add_compass_agent | Compass agent |
| 047 | disco_outcome_tracking | Outcome tracking (formerly purdy_outcome_tracking) |
| 048 | disco_synthesis | DISCO bundles + PRDs tables |
| 056 | rename_opportunities_to_projects | Rename opportunities → projects throughout |
| 061 | disco_checkpoints | Human-in-the-loop checkpoints for consolidated agents |
| 062 | project_initiatives | Initiative linking for projects (`initiative_ids UUID[]`) |
| 065 | project_documents | Project-document linking |
| 066 | conversation_context_columns | Context linking for conversations |
| 067 | initiative_goal_alignment | Goal alignment columns on `disco_initiatives` |
| 069 | task_view_with_project | Task view with project info join |
| 070 | task_notes | Notes field on tasks |
| 071 | initiative_throughline | Throughline + throughline_resolution JSONB columns |
| 072 | disco_restructure | Value alignment, sponsor/stakeholder, resolution annotations on `disco_initiatives`; triage_suggestions on `disco_outputs`; source tracking on `project_tasks` |
| 074 | initiative_folder_links | `disco_initiative_folder_links` table for vault folder-to-initiative associations |
| 075 | task_kraken | Agenticity columns on `ai_projects` (score, evaluation JSONB, task hash) |

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
- `/backend/services/project_*.py` - Project services (context, chat, justification, confidence, taskmaster, kb_sync)
- `/backend/scripts/remote_vault_sync.py` - Local-to-Railway vault sync agent (runs locally, uploads via HTTP)
- `/backend/services/stakeholder_*.py` - Stakeholder services (extractor, scanner, deduplicator, linker)
- `/backend/services/task_*.py` - Task services (auto_extractor, extractor, kraken)
- `/backend/services/disco/` - DISCO services (4 consolidated agents + 8 legacy) (formerly `purdy/`, path alias still supported)
- `/backend/services/disco/initiative_context.py` - Builds XML context for Discovery Agent (throughline, agent outputs, linked docs)
- `/backend/services/goal_alignment_analyzer.py` - Project goal alignment (IS FY27 pillars)
- `/backend/services/disco/initiative_alignment_analyzer.py` - Initiative goal alignment with agent output context
- `/backend/services/graph/` - Neo4j services

### Backend API Routes
- `/backend/api/routes/chat.py` - Chat endpoints
- `/backend/api/routes/meeting_rooms.py` - Meeting room CRUD
- `/backend/api/routes/agents.py` - Agent management
- `/backend/api/routes/documents.py` - Document CRUD
- `/backend/api/routes/tasks.py` - Task management
- `/backend/api/routes/projects.py` - Project pipeline (also `/api/opportunities/*` for backward compatibility)
- `/backend/api/routes/disco.py` - DISCO endpoints (formerly `purdy.py`, route `/api/purdy/*` still accepted)

### Frontend Core
- `/frontend/app/layout.tsx` - Root layout
- `/frontend/components/ChatInterface.tsx` - Main chat
- `/frontend/components/AgentIcon.tsx` - Agent icons and colors (single source of truth)

### Frontend Features
- `/frontend/app/meeting-room/` - Meeting rooms
- `/frontend/app/tasks/` - Kanban board
- `/frontend/app/projects/` - Project pipeline
- `/frontend/app/disco/` - DISCO feature (formerly `purdy/`, route `/purdy` still redirects)
- `/frontend/components/disco/` - DISCO components (10 files, including ThroughlineEditor, ThroughlineSummary, LinkedFoldersSection) (formerly `purdy/`)
- `/frontend/components/chat/FramingProposalCard.tsx` - Selective framing proposal card for Discovery Agent chat responses
- `/frontend/components/chat/TaskProposalCard.tsx` - Selective task proposal card for Taskmaster chat responses

### KB Components (Finder-Style Layout)
- `/frontend/components/kb/KBDocumentsContent.tsx` - Orchestrator (~300 lines): manages folder/search/filter state, toolbar, sidebar+content flex layout, modals
- `/frontend/components/kb/KBFinderSidebar.tsx` - Folder tree from `/api/documents/folders`, expand/collapse, "All Documents" root item
- `/frontend/components/kb/KBFinderContent.tsx` - Document list for selected folder, breadcrumbs, source badges, infinite scroll, bulk actions
- `/frontend/components/kb/KBSyncSettingsModal.tsx` - Tabbed modal (Vault/Drive/Notion/Uploads) for all sync controls
- `/frontend/components/kb/KBDocumentInfoModal.tsx` - Document detail modal with tags, agent assignments, sync cadence
- `/frontend/components/kb/KBDocumentBrowserTab.tsx` - Tag Manager tab with bulk tag operations
- `/frontend/components/kb/ClassificationReviewBanner.tsx` - Review banner for ambiguous auto-classifications

### DISCO Agent Prompts
- `/backend/disco_agents/` - Agent prompt definitions (versioned markdown) (formerly `purdy_agents/`, path alias still supported)
  - **Consolidated (v1.2):** `discovery-guide-v1.2.md`, `insight-analyst-v1.1.md`, `initiative-builder-v1.1.md`, `requirements-generator-v1.2.md`
  - **KB References:** `KB/gap-taxonomy-reference.md` - Gap categorization taxonomy for Discovery Guide
  - **Output Templates:** `evaluation-framework-v1.0.md`, `decision-framework-v1.0.md`, `prd-generator-v1.0.md`, `strategist-v1.0.md`
  - **Legacy:** `triage-v4.2.md`, `discovery-planner-v4.1.md`, `coverage-tracker-v4.1.md`, `insight-extractor-v4.2.md`, `consolidator-v4.2.md`, `tech-evaluation-v4.0.md`
  - `RUBRIC-v3.0.md` - Scoring rubric for evaluation
  - `EVALUATION-v4.2-RESULTS.md` - Latest evaluation results
- `/frontend/components/projects/` - Project components
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
| test_disco_initiative_service.py | 20+ | PASS |
| test_disco_throughline.py | 20+ | PASS |
| test_disco_restructure.py | 46 | PASS |

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
