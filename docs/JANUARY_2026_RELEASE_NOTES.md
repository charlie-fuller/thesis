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
- API: `/backend/api/routes/obsidian_sync.py`
- CLI: `/backend/scripts/obsidian_watcher.py`
- Migration: `021_obsidian_sync.sql`
- Documentation: `/docs/obsidian-sync-readme.md`

**Usage**:
```bash
python -m scripts.obsidian_watcher --user-id <uuid>
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
