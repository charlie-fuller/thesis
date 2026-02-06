# Thesis - February 2026 Release Notes

This document summarizes all new functionality added to Thesis in the February 2026 development cycle.

---

## Late January / Early February (January 30 - February 2, 2026)

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

## February 2-3, 2026

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

## February 3, 2026

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

## February 4, 2026

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

---

## February 5, 2026

### KB Finder-Style Redesign

Replaced the integration-centric KB layout (3,044-line monolith with nested accordions) with a Finder-style filesystem browser where the folder tree is immediately visible.

**New Layout**:
- Toolbar: search, source filter, sync status badge, gear icon for settings
- Two-pane flex layout: folder tree sidebar (w-64) + document content pane
- Folder tree loads from `/api/documents/folders` API (complete folder tree with recursive counts)
- Documents lazy-loaded per folder via `/api/documents/search?folder=X`

**Architecture Change** (3,044 lines decomposed into 5 focused files):
- `KBDocumentsContent.tsx` (~300 lines) - Orchestrator: state management, toolbar, layout composition, OAuth handlers
- `KBFinderSidebar.tsx` (~210 lines) - Recursive folder tree with expand/collapse, document counts, folder selection
- `KBFinderContent.tsx` (~400 lines) - Document list with breadcrumbs, source badges, processing status, infinite scroll, bulk actions
- `KBSyncSettingsModal.tsx` (~930 lines) - Tabbed modal (Vault | Drive | Notion | Uploads) containing all sync controls
- `KBDocumentInfoModal.tsx` (~545 lines) - Document detail modal with tags, agent assignments, sync cadence

**Files**: `frontend/components/kb/KBDocumentsContent.tsx`, `frontend/components/kb/KBFinderSidebar.tsx`, `frontend/components/kb/KBFinderContent.tsx`, `frontend/components/kb/KBSyncSettingsModal.tsx`, `frontend/components/kb/KBDocumentInfoModal.tsx`

### Obsidian Sync: File Move/Rename Detection

The vault sync now detects when files are moved or renamed in Obsidian and preserves their document IDs instead of creating duplicates.

**How It Works**:
- During sync, compares content hashes of new files against recently deleted files
- If a hash match is found, updates the existing document's path instead of creating a new one
- Preserves all document metadata (tags, agent assignments, embeddings) across moves
- Works for both incremental sync and "Check for Updates"

**Files**: `backend/services/obsidian_sync.py`

### Full Resync: 5-Phase Filesystem Mirroring

Full resync no longer clears sync states before processing. It efficiently mirrors the vault by computing hashes upfront, processing changes first for fast feedback, and showing phase-aware progress.

**Phases**:
1. **Scan & Categorize**: Compute hashes for all files, categorize into changed vs unchanged
2. **Sync Changes**: Process new/modified files first for fast feedback
3. **Detect Moves**: Match content hashes of new files against missing files to preserve document IDs
4. **Clean Up Deletions**: Remove documents for files no longer on disk (Full Resync only)
5. **Verify Unchanged**: Walk unchanged files through sync (skipped if no changes found)

**Key Improvements**:
- Vault folder tree stays visible throughout sync (sync states not cleared)
- Phase-aware progress UI: "Scanning...", "Syncing changes... 3 of 5", "Detecting moved files...", etc.
- Progress bar resets per phase with phase-specific counts
- No changes = quick finish (skips verification entirely)
- Precomputed hashes avoid double-hashing files

**Files**: `backend/services/obsidian_sync.py`, `backend/api/routes/obsidian_sync.py`, `frontend/components/kb/KBSyncSettingsModal.tsx`

### KB Bulk Delete

Added multi-select and bulk delete capability to the KB document browser.

**Features**:
- Checkbox selection for individual documents
- "Select all" toggle in header
- Bulk delete button with confirmation count
- Warning when deleting documents linked to DISCO initiatives

**Files**: `frontend/components/kb/KBFinderContent.tsx`

### Initiative Goal Alignment

DISCO initiatives can now be analyzed against the same IS FY27 strategic pillars used for projects, with richer context from agent outputs.

**Features**:
- New "Alignment" tab on initiative detail page (between Outputs and Projects)
- Scores 0-100 across 4 IS FY27 pillars (25 points each): Customer Journey, Maximize Value, Digital Workforce, High-Trust Culture
- Rich analysis context: gathers latest agent outputs (triage, strategist, insight analyst, etc.) and bundle scores for more accurate scoring
- Stale indicator when new agent outputs exist since last analysis
- Empty state hint suggesting running agents first for better accuracy
- Project roll-up section showing linked projects' alignment scores, average, and distribution (high/moderate/low/minimal)
- Manual trigger only (click Analyze button); editors/owners can analyze, viewers can view results

**Files**: `backend/services/disco/initiative_alignment_analyzer.py`, `backend/api/routes/disco/initiatives.py`, `frontend/components/disco/InitiativeAlignmentTab.tsx`, `frontend/components/projects/GoalAlignmentSection.tsx`, `frontend/app/disco/[id]/page.tsx`, `database/migrations/067_initiative_goal_alignment.sql`

---

## February 6, 2026

### KB Document Sorting & Column Headers

Improved document list display with proper date sorting and dual date columns.

**Changes**:
- Documents now sort by `original_date` (document creation date) instead of `uploaded_at` (sync timestamp)
- Column headers added: Name, Source, Created (document date), Added (sync date)
- "All Documents" item now shows correctly in folder tree with total count
- Empty folder state handled gracefully

**Files**: `backend/api/routes/documents/search.py`, `frontend/components/kb/KBFinderContent.tsx`, `frontend/components/kb/KBFinderSidebar.tsx`

### Unified Filter/Sort UI

Consistent styling applied across KB, Tasks, and Projects filter controls.

**Changes**:
- All dropdowns use same styling: `px-3 py-2 border border-default rounded-lg text-sm bg-card`
- Priority and source filter buttons use `rounded-lg` (previously `rounded-full` on Tasks)
- Improved visual consistency across the application

**Files**: `frontend/app/projects/page.tsx`, `frontend/components/tasks/TaskFilters.tsx`

### Linked Document Protection

The vault sync orphan cleanup now protects documents that are linked to initiatives or projects.

**Problem Solved**:
- Previously, orphan cleanup could delete documents whose source files were moved/renamed in Obsidian
- This triggered `ON DELETE CASCADE` on foreign keys, deleting all initiative and project document links
- Users lost carefully curated document associations

**Solution**:
- New `_get_linked_document_ids()` helper checks `disco_initiative_documents` and `project_documents` tables
- Orphan cleanup skips any document with existing links
- Skipped documents logged with "SKIPPED orphan (has initiative/project links)" warning
- Documents can still be manually deleted if needed

**Files**: `backend/services/obsidian_sync.py`

### Sync Date Parsing Fix

Fixed a bug where date patterns could incorrectly match partial years as days.

**Example**: "2026-02-05" was being parsed with "26" as the day in some edge cases.

**Files**: `backend/services/obsidian_sync.py`

### Folder Cleanup with Pagination

Added pagination to orphan document cleanup and improved stale folder handling.

**Changes**:
- Orphan cleanup now processes documents in batches to avoid memory issues with large vaults
- Stale KB folders (with 0 documents) properly removed from folder tree
- Improved sync reliability for vaults with thousands of files

**Files**: `backend/services/obsidian_sync.py`
