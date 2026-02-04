# Thesis - January 2026 Release Notes

This document summarizes all new functionality added to Thesis in the January 2026 development cycle.

## New Agents (3 Added)

### 1. Glean Evaluator - "Can We Glean This?"
**Purpose**: Assesses whether Glean is the appropriate tool for a given PRD, discussion, or application request.

**Key Capabilities**:
- Evaluate PRDs and application requests for Glean platform fit
- Analyze integration requirements and data source compatibility
- Assess scale, cost, and time-to-value considerations
- Recommend alternatives when Glean is not appropriate
- Identify security and compliance requirements

**Backend**: `/backend/agents/glean_evaluator.py`
**Instructions**: `/backend/system_instructions/agents/glean_evaluator.xml`

### 2. Compass - Personal Career Coach
**Purpose**: Helps professionals track performance, capture wins, prepare for manager conversations, and maintain strategic alignment.

**Key Capabilities**:
- Win capture and impact documentation from conversational updates
- Check-in and performance review preparation
- Strategic alignment tracking with company priorities
- Goal progress monitoring and reflection prompting
- Performance Tracker document management

**Backend**: `/backend/agents/compass.py`
**Instructions**: `/backend/system_instructions/agents/compass.xml`

### 3. Facilitator & Reporter (Meta-Agents)
Already existed but documented here for completeness - they are now properly wired up with the meeting room system.

---

## New Features

### 1. Task Management System (`/tasks`)
A Kanban-style task board for tracking work across the platform.

**Features**:
- Drag-and-drop status updates (Backlog, Todo, In Progress, Done)
- Priority levels (P1-P4) with color coding
- Assignee tracking with stakeholder integration
- Due date management
- Task extraction from meeting transcripts
- Status history tracking for audit trails
- Comments on tasks

**Frontend**: `/frontend/app/tasks/page.tsx`
**Components**: `/frontend/components/tasks/`
**Backend**: `/backend/api/routes/tasks.py`
**Migration**: `019_task_management.sql`

### 2. Project Triage System (Operator Enhancement)
Enhanced the Operator agent with AI opportunity pipeline management.

**Features**:
- 4-dimension scoring: ROI Potential, Implementation Effort, Strategic Alignment, Stakeholder Readiness
- Tier-based prioritization (Tier 1-4) based on total score
- Automatic context injection into Operator agent queries
- Status tracking: identified, scoping, pilot, scaling, completed, blocked
- Department and stakeholder ownership tracking

**Backend Service**: `/backend/services/operator_tools.py`
**Operator Enhancement**: Automatic triage context injection when queries mention opportunities, pipeline, stakeholders, etc.

### 3. Opportunities Pipeline (`/opportunities`)
A dedicated page for managing AI implementation opportunities.

**Features**:
- Visual tier-based grouping with expandable sections
- Summary cards showing opportunity counts by tier
- Filters by department and status
- Inline status updates
- Score editing with automatic tier recalculation
- Create new opportunities with full scoring form

**Frontend**: `/frontend/app/opportunities/page.tsx`
**Create Form**: `/frontend/app/opportunities/new/page.tsx`
**Backend**: `/backend/api/routes/opportunities.py`
**Migration**: `018_project_triage.sql`

### 4. Meeting Prep Pages (`/meeting-prep/[stakeholder_id]`)
Stakeholder briefing pages for pre-meeting preparation.

**Features**:
- Stakeholder priority level and relationship status
- Status summary (red/yellow/green) across key areas
- Linked AI opportunities with tier and status
- KPI tracking with validation status (unverified, validated, baseline_set)
- Open questions to ask
- AI-recommended approach based on stakeholder profile
- Days since last contact indicator

**Frontend**: `/frontend/app/meeting-prep/[stakeholder_id]/page.tsx`
**Backend**: `/backend/api/routes/meeting_prep.py`

### 5. Document Auto-Classification
Automatic agent relevance tagging when documents are uploaded.

**How It Works**:
1. When a document is uploaded, keyword scoring analyzes content
2. If confidence is high (>80%), document is auto-tagged to relevant agents
3. If confidence is ambiguous (40-80%), LLM classification (Claude Haiku) is used
4. Ambiguous results are flagged for user review via banner in KB page
5. Users can confirm or adjust agent assignments

**Components**:
- `/frontend/components/kb/ClassificationReviewBanner.tsx` - Review UI
- `/backend/services/document_classifier.py` - Hybrid classifier

**Agent-Filtered RAG**:
- Retrieval now prioritizes documents tagged for the querying agent
- Hybrid strategy: agent-filtered first, falls back to all docs if <3 results
- Relevance scores stored in `agent_knowledge_base.relevance_score`

**Migration**: `019_document_auto_classification.sql`

### 6. Stakeholder Engagement Analytics
Automatic engagement level calculation with historical trend tracking.

**Features**:
- Weekly scheduler (Sunday 4 AM UTC) recalculates engagement levels
- Sticky level rules (only demote on explicit negative signals)
- Engagement trends visualization with Recharts stacked area chart
- History tracking in `engagement_level_history` table

**Engagement Level Rules**:
- **Champion**: 5+ interactions AND (1+ commitment OR 3+ support)
- **Supporter**: 3+ interactions AND >50% positive ratio
- **Neutral**: Default level
- **Skeptic/Blocker**: Requires unresolved objections

**Backend Services**:
- `/backend/services/engagement_calculator.py`
- `/backend/services/engagement_scheduler.py`

**Frontend**:
- `/frontend/components/EngagementTrendsChart.tsx`
- `/frontend/app/intelligence/page.tsx` (updated)

**Migration**: `017_engagement_history.sql`

### 7. Glean Connector Registry
Database and API for tracking Glean connector availability and gaps.

**Tables**:
- `glean_connectors` - Registry of OOB, custom, and requested connectors
- `glean_connector_requests` - Gap tracking for connector prioritization
- `glean_connector_gaps` (view) - Prioritized view of requested connectors

**API Endpoints**:
- `GET /api/glean-connectors/` - List all connectors
- `GET /api/glean-connectors/categories` - List categories
- `POST /api/glean-connectors/check` - Check connector availability
- `POST /api/glean-connectors/request` - Log a connector request
- `GET /api/glean-connectors/gaps` - Get prioritized gaps
- `GET /api/glean-connectors/search/{query}` - Search connectors

**Backend**: `/backend/api/routes/glean_connectors.py`
**Migration**: `016_add_glean_evaluator_agent.sql`
**Data**: `/docs/glean/CONNECTOR_REGISTRY.csv`

### 8. Stakeholder Metrics API
KPI tracking with validation status for stakeholder performance monitoring.

**Features**:
- Red/yellow/green validation framework
- Baseline tracking and target setting
- Evidence linking for validated metrics
- Bulk operations for stakeholder metrics

**Backend**: `/backend/api/routes/stakeholder_metrics.py`

---

## Enhanced Stakeholder Model

The stakeholder model was extended with Project Triage fields:

| Field | Type | Purpose |
|-------|------|---------|
| `priority_level` | text | tier_1, tier_2, tier_3 prioritization |
| `ai_priorities` | text[] | Array of stated AI priorities |
| `pain_points` | text[] | Array of identified pain points |
| `win_conditions` | text[] | What success looks like |
| `communication_style` | text | How they prefer to communicate |
| `relationship_status` | text | new, warming, established, champion, cooling |
| `open_questions` | text[] | Questions to address in next meeting |
| `last_contact` | timestamp | Last interaction date |
| `reports_to_name` | text | Manager name for org context |
| `team_size` | integer | Team size for impact assessment |

---

## Database Migrations

New migrations added:

| # | File | Description |
|---|------|-------------|
| 016 | add_glean_evaluator_agent | Glean Evaluator agent + connector registry |
| 016 | rename_fortuna_to_capital | Rename finance agent |
| 017 | engagement_history | Engagement level history tracking |
| 018 | project_triage | AI opportunities, stakeholder triage fields |
| 019 | document_auto_classification | Auto-classification + agent filtering |
| 019 | task_management | Kanban tasks, comments, history |
| 040 | add_compass_agent | Compass career coach agent |

---

## Agent Count

**Total Agents**: 20 (up from 18)

New additions:
- Glean Evaluator
- Compass
- (Facilitator and Reporter were already implemented but not fully documented)

---

## Navigation Updates

The PageHeader navigation now includes:
- Dashboard
- Chat
- Meeting Room
- Tasks (new)
- Opportunities (new)
- Intelligence
- KB

---

## Bug Fixes

1. **Import Fix**: `glean_connectors.py` - Changed incorrect `from ..dependencies import get_supabase` to `from database import get_supabase`

2. **Styling Consistency**: Updated opportunities pages and meeting-prep pages to use:
   - `PageHeader` component
   - `bg-page` theme class
   - `text-primary` and `text-muted` theme classes

---

## File Summary

### New Backend Files
```
backend/agents/glean_evaluator.py
backend/agents/compass.py
backend/api/routes/glean_connectors.py
backend/api/routes/meeting_prep.py
backend/api/routes/opportunities.py
backend/api/routes/stakeholder_metrics.py
backend/api/routes/tasks.py
backend/services/operator_tools.py
backend/services/engagement_calculator.py
backend/services/engagement_scheduler.py
backend/services/document_classifier.py
backend/system_instructions/agents/glean_evaluator.xml
backend/system_instructions/agents/compass.xml
```

### New Frontend Files
```
frontend/app/tasks/page.tsx
frontend/app/opportunities/page.tsx
frontend/app/opportunities/new/page.tsx
frontend/app/meeting-prep/[stakeholder_id]/page.tsx
frontend/components/tasks/TaskKanbanBoard.tsx
frontend/components/tasks/TaskCard.tsx
frontend/components/tasks/TaskColumn.tsx
frontend/components/tasks/TaskCreateModal.tsx
frontend/components/tasks/TaskFilters.tsx
frontend/components/kb/ClassificationReviewBanner.tsx
frontend/components/EngagementTrendsChart.tsx
```

### New Documentation
```
docs/glean/CONNECTOR_REGISTRY.csv
docs/stakeholders/CONTENTFUL_EXECUTIVES.sql
docs/stakeholders/CONTENTFUL_STAKEHOLDERS.sql
docs/stakeholders/STAKEHOLDER_PROFILE_METHOD.md
```

---

## Coming Soon

- Research dashboard UI for Atlas insights
- Stakeholder network visualization

---

## Post-Release Update: Obsidian Vault Sync (Completed January 2026)

The Obsidian Vault Sync feature was completed after the initial release notes were written.

**Features**:
- Sync markdown files from local Obsidian vaults to Knowledge Base
- File watcher monitors vault for changes (create/modify/delete)
- Parses YAML frontmatter (including `thesis-agents` for auto-tagging)
- Converts `[[wikilinks]]` to standard markdown links
- Incremental sync via content hash change detection

**Files**:
- Backend: `/backend/services/obsidian_sync.py`
- Scheduler: `/backend/services/vault_watcher_scheduler.py`
- API: `/backend/api/routes/obsidian_sync.py`
- CLI: `/backend/scripts/vault_watcher.py`
- Migration: `021_obsidian_sync.sql`
- Documentation: `/docs/obsidian-sync-readme.md`

**Usage** (automatic with backend):
```bash
# Add to .env
VAULT_WATCHER_USER_ID=<uuid>
# Watcher starts automatically with backend server
```

---

## Late January Updates (January 27-29, 2026)

### Document Type Classification for Smart RAG

Documents synced from Obsidian are now automatically classified by type, enabling smarter search filtering.

**Document Types**:
- `transcript` - Meeting transcripts, call recordings (including Granola format `Person1 __ Person2.md`)
- `notes` - Meeting notes, personal notes
- `instructions` - Guides, playbooks, how-to docs
- `report` - Research reports, analysis, whitepapers
- `presentation` - Slides, decks (.pptx)
- `spreadsheet` - Data files (.csv, .xlsx)

**Smart Search Behavior**:
- Queries about "recent meetings" or "this week" filter to transcript/notes types
- Recency boost (20%) applied to documents from last 14 days
- Path-based classification fallback (documents in `meetings/` folder → transcript)

**Files**: `backend/services/obsidian_sync.py`, `backend/migrations/049_backfill_obsidian_document_types.sql`

### Binary Document Support in Obsidian Sync

Obsidian sync now processes binary documents (PDF, DOCX, XLSX, PPTX) in addition to markdown.

**Features**:
- PDF text extraction with OCR fallback for image-based PDFs
- DOCX/XLSX/PPTX processing via document_processor
- View original document button in KB interface
- Progress bar shows current file during sync

**Files**: `backend/services/obsidian_sync.py`, `backend/document_processor.py`

### Real-Time Sync Progress

Obsidian sync now shows real-time progress with:
- Progress bar with percentage complete
- Current file being processed
- Total file count

### Date-Aware Agents

Agents now receive current date context and respect KB date filters in search results.

**Behavior**:
- Agents know today's date for time-relative queries
- "This week" queries filter to last 7 days
- Search results respect date filters rather than silently dropping them

### DISCo Enhancements

- **Glean Connector Scoring Matrix**: Added DISCo-style scoring for Glean connector fit assessment
- **Data Freshness Notes**: Scoring output now includes data freshness indicators

### KB UI Improvements

- **Full Folder Hierarchy**: Obsidian view now preserves complete folder structure instead of flattening
- **Document View Button**: Direct link to view original document in storage

---

## Late January Updates (January 29, 2026)

### DISCo KB Integration

DISCo initiatives now use the Knowledge Base as the single source of truth for documents, eliminating document duplication.

**Features**:
- Link documents from KB to DISCo initiatives (modal: "Link Documents from Knowledge Base")
- KB document browser with 60/40 search/tag filter split and preview panel
- Warning when deleting KB documents that are linked to DISCo initiatives
- Multi-select and bulk delete for uploaded files
- Highlighted preview selection in document list

**Files**: `frontend/components/disco/KBDocumentBrowser.tsx`, `backend/api/routes/disco.py`

### Vault Terminology

Renamed "Obsidian" and "Granola" references to generic "Vault" terminology throughout the platform for cleaner UX.

- Vault panel in dashboard shows sync status
- Vault folders display as nested tree structure
- Removed direct references to third-party product names in UI

### Help Chat Temporal Awareness

Date filtering and temporal awareness added to the help chat system.

**Features**:
- Queries like "this week" filter to last 7 days
- Date-based filtering respects KB date metadata
- Reindexing now always part of documentation updates

### Dashboard Simplification

- Removed Vault panel from main dashboard
- Streamlined Discovery Inbox focus

---

## Late January / Early February Updates (January 30 - February 2, 2026)

### DISCo Chat Document Visibility Fix

The DISCo initiative chat now properly shows linked KB documents in all contexts.

**Problem Solved**:
- Previously, chat only included KB document chunks via vector search
- Meta-questions like "what documents do you have?" returned nothing because they didn't semantically match content
- Users couldn't verify if linked documents were visible to the assistant

**Solution**:
- Added document list to chat context showing all linked KB documents by name
- Chat now starts context with "Available Linked KB Documents" section
- Vector search results still included for content-specific queries
- System prompt updated to mention KB document access

**Files**: `backend/services/disco/chat_service.py`, `backend/services/disco/document_service.py`

### Code Quality Gates & Test Command

Enhanced `/test` command with code quality gates and flexible options.

**Features**:
- `--quick` flag for core tests only (faster feedback)
- `--full` flag for comprehensive test suite including integration
- Pre-test quality gates: Black formatting, Ruff linting
- Automatic fix suggestions when quality checks fail

**Files**: `backend/scripts/run_all_tests.sh`

### Database Connection Resilience

Added automatic retry logic for database connections to handle transient failures.

**Features**:
- Retry with exponential backoff for broken pipe errors
- Handles connection pool exhaustion gracefully
- Automatic reconnection on `BrokenPipeError`

**Files**: `backend/database.py`

### File Storage Improvements

- **Special Characters**: Filenames with special characters (brackets, parentheses) now handled correctly in storage paths
- **RTF Support**: Added RTF file type support for document uploads
- **Pending Details**: Clicking pending count in sync status now shows list of pending files

### KB Vault Section Enhancements

- Recent files section shows recently synced documents
- Files sorted by `last_synced_at` timestamp
- Meeting documents prioritized by `document_date` for accurate recency
- Date-only strings parsed as local dates (not UTC midnight)

### Global Help Sidebar

The help assistant is now available on all pages throughout the application.

**Features**:
- Help toggle button in header (right side) on every page
- Panel state persists across navigation and browser sessions via localStorage
- 400px sidebar slides in from right when opened
- Available on: Dashboard, Tasks, KB, Projects, Intelligence, Agents, Pipeline, Transcripts, DISCo, Admin

**Files**:
- `frontend/components/PageLayout.tsx` (new wrapper component)
- `frontend/components/PageHeader.tsx` (added `showHelpToggle` prop)
- `frontend/contexts/HelpChatContext.tsx` (added localStorage persistence)

---

## Early February Updates (February 2-3, 2026)

### Project-Initiative Linking

Projects can now be created directly from chat and linked to DISCo initiatives.

**Features**:
- "Create Project from Chat" action extracts project details from conversation context
- Projects linked to initiatives appear in initiative detail view with direct navigation
- Initiative filter on Projects page shows only projects for selected initiative
- Bi-directional navigation between initiatives and their related projects

**Files**: `frontend/components/chat/CreateProjectFromChat.tsx`, `frontend/app/projects/page.tsx`

### Projects Page Overhaul

Simplified project management with cleaner UI and better filtering.

**Changes**:
- Simplified to 4 statuses: Backlog, Active, Completed, Archived
- Added list/tier view toggle (tier view groups by priority tier)
- Active-only filter defaults to true (shows active projects by default)
- Removed star toggle and Total/Active count boxes for cleaner UI
- Save/Cancel buttons moved to modal footer

**Files**: `frontend/app/projects/page.tsx`, `frontend/components/projects/ProjectModal.tsx`

### Task-Project Integration

Tasks can now be associated with projects for better work tracking.

**Features**:
- Tasks tab in project modal shows all tasks linked to that project
- Project filter on Tasks page filters tasks by associated project
- Task extraction when creating projects from chat

**Files**: `frontend/app/tasks/page.tsx`, `frontend/components/projects/ProjectModal.tsx`

### DISCo Link Documents Enhancements

Added sorting and filtering options to the KB document browser when linking documents to initiatives.

**Features**:
- Sort by: Most Recent, Oldest First, Name (A-Z), Name (Z-A)
- Filter by source: All Sources, Vault, Google Drive, Notion, Uploaded
- "Reset filters" link when non-default filters are active
- Filters reset when closing the modal

**Files**: `frontend/components/disco/KBDocumentBrowser.tsx`, `backend/api/routes/documents/search.py`

---

## February 2026 Updates (February 3, 2026)

### KB Tag Manager Overhaul

Replaced the existing Tag Manager with a new unified document browser that matches the DISCO document linking UX.

**Features**:
- Same layout as DISCO browser: Search (60%) + Tag filter (40%) header row
- Sort/source filter row with "Reset filters" link
- Split view: Document list (40%) + Preview/Tags panel (60%)
- Right panel toggles between "Preview" and "Manage Tags" modes
- Multi-select documents for bulk tag operations
- Create new tags inline, add/remove tags with color indicators (green/red)
- Apply changes with single button click

**Files**: `frontend/components/kb/KBDocumentBrowserTab.tsx`, `frontend/components/kb/KBDocumentsContent.tsx`

### Agents Tab in Intelligence

The standalone Agents page has been consolidated into the Intelligence page as a new tab.

**Changes**:
- Agents tab appears after Engagement in the Intelligence page
- Standalone `/agents` route now redirects to `/intelligence?tab=agents`
- Agent grid displays version, KB docs, chats, and meetings count
- Removed Agents from main navigation

### Navigation Reorder

Simplified navigation with KB in a more prominent position.

**New Order**: Dashboard → KB → Chat → Tasks → Projects → Intelligence → DISCO

**Rationale**: Knowledge Base is foundational to all agents' context, so it's positioned early in the workflow.

### Knowledge Graph Removed from KB Data Map

Simplified the KB data flow visualization by removing the Knowledge Graph section.

**Changes**:
- Removed Knowledge Graph node and arrows from data map
- Reduced visual complexity for clearer understanding
- Focus on document → agent → response flow

### Vault Sync Improvements

- **Check for Updates button**: Manually scan for files modified since last sync
- **Inline status messages**: Vault status now displays inline with title (reduced panel height)
- **CSV and RTF support**: Added to default remote vault sync patterns

### DISCO Terminology

Renamed "DISCo" to "DISCO" (capital O) throughout the application for consistency with the acronym (Discovery, Intelligence, Synthesis, Convergence, Operationalize).

### Conversation Context Linking

Conversations and meeting rooms can now be associated with projects or initiatives for better organization.

**Features**:
- Context filter dropdowns in conversation sidebar (filter by project or initiative)
- New **Initiative Agent** and **Project Agent** for context-aware conversations
- Conversations linked to a project/initiative automatically include relevant context
- Filter sidebar to show only conversations for a specific project or initiative

**Files**: `backend/agents/initiative_agent.py`, `backend/agents/project_agent.py`, `frontend/components/ConversationSidebar.tsx`

### Dashboard Tab Reorder

Reorganized dashboard tabs for better workflow:

**New Order**: System Health → Analytics → Process Map → Knowledge Graph (last)

Interface Health panel moved from System Health to Analytics tab for consolidated metrics viewing.

### Discovery Inbox Redesign

The Discovery Inbox now displays all three candidate types simultaneously in a vertical panel layout.

**Changes**:
- Tasks, Projects, and Stakeholders panels displayed vertically (not as tabs)
- Each panel shows one candidate at a time with navigation arrows
- Removed expand/collapse - always visible
- Accept (checkmark) and Skip (X) buttons for each candidate

### KB Data Map Improvements

- Changed subtitle to "Click any box for details"
- Enlarged column title fonts for better readability
- Routed Chat→Agents arrow around outside bottom to avoid overlapping other elements
- Removed "Meeting Transcripts" node (documents now generalized)
- "Local Vault" subtitle changed to "Filesystem Sync"

---

## February 2026 Updates (February 4, 2026)

### DISCO Flexible Output Types

Bundle approval now supports three document types based on bundle purpose, with AI-suggested recommendations.

**Output Types**:
- **PRD** (default): Product Requirements Document for build/development bundles
- **Evaluation Framework**: Weighted criteria matrix, platform comparison table, and recommendation for research/evaluation bundles (e.g., vendor selection, tool evaluation)
- **Decision Framework**: Decision criteria, stakeholder analysis, options comparison, and risk/benefit assessment for governance decisions

**Features**:
- AI analyzes bundle name, description, and included items to suggest appropriate output type
- Suggestion displayed with rationale before user confirms
- Output type selector in bundle approval modal with descriptions
- Section parsers extract structured content for each document type

**Files**: `backend/disco_agents/evaluation-framework-v1.0.md`, `backend/disco_agents/decision-framework-v1.0.md`, `backend/services/disco/prd_service.py`, `frontend/components/disco/SynthesisView.tsx`

### Create Project from PRD

Approved PRDs can now spawn projects directly with AI-extracted fields and confidence indicators.

**Features**:
- "Create Project" button appears on approved PRDs
- AI extracts: title, description, department, current state, desired state, and 4-dimension scores
- Confidence indicators (high/medium/low) highlight fields needing user review
- Low-confidence fields highlighted in amber for attention
- Task extraction from PRD requirements section with priority assignment
- Projects linked to parent initiative with `source_type: disco_prd`
- Source notes include PRD reference for traceability

**Files**: `frontend/components/disco/CreateProjectFromPRDModal.tsx`, `frontend/components/disco/PRDViewer.tsx`, `backend/api/routes/disco/synthesis.py`

### Initiative Projects Endpoint

New dedicated API endpoint for querying projects linked to DISCO initiatives.

**Features**:
- `GET /api/disco/initiatives/{id}/projects` returns all linked projects
- Supports filtering by project status
- "From PRD" badge displayed on projects created via PRD extraction
- Cleaner than using general projects API with initiative filter

**Files**: `backend/api/routes/disco/initiatives.py`, `backend/services/disco/project_service.py`, `frontend/app/disco/[id]/page.tsx`

### Direct Project Creation from Projects Page

Added ability to create projects directly from the Projects page without going through discovery flows.

**Features**:
- "New Project" button on Projects page header
- Full project form with all scoring dimensions
- Auto-generates project code based on department
- Supports initiative linking at creation time

**Files**: `frontend/app/projects/page.tsx`
