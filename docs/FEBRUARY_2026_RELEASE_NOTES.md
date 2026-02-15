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

### Remote Upload Endpoint Fix

Fixed three broken imports in the remote vault sync upload endpoint (`POST /api/obsidian/upload`) that caused every upload to fail with HTTP 500.

**Problem Solved**:
- The endpoint referenced renamed functions (`auto_classify_document`, `extract_date_from_content`, `parse_obsidian_frontmatter`) that no longer existed
- This silently broke the entire local-to-Railway sync pipeline, preventing any new or modified files from syncing

**Fix**:
- Updated imports to use correct function names: `classify_document_by_filename`, `extract_original_date`, `parse_frontmatter`
- Updated all call sites with correct argument signatures

**Files**: `backend/api/routes/obsidian_sync.py`

### File Modification Time in Remote Sync

The remote vault sync agent now sends file modification timestamps to the backend for more accurate date extraction.

**Changes**:
- Added `file_mtime` field to `RemoteFileUploadRequest` model
- `remote_vault_sync.py` now sends `stat.st_mtime` with each upload
- Backend converts to datetime and passes to `extract_original_date()` as fallback
- Prevents documents from getting incorrect dates when content-based extraction fails

**Files**: `backend/api/routes/obsidian_sync.py`, `backend/scripts/remote_vault_sync.py`

### Future Date Guard

Added validation to prevent date extraction from matching dates in the future.

**Problem Solved**:
- Document content containing future dates (e.g., "May 20, 2026" in a planning document) could be incorrectly extracted as the document's original date
- This caused documents to appear with wrong dates in the KB

**Fix**:
- `_extract_date_from_text()` now skips any extracted date that is after today
- Falls back to the next matching pattern or returns None

**Files**: `backend/services/obsidian_sync.py`

### DISCO Initiative Description Modal

Replaced inline description editing with a modal dialog for editing initiative name and description.

**Changes**:
- Click initiative name or description to open edit modal
- Modal provides more space for multi-line description editing
- Cleaner UX than inline text editing with save/cancel buttons

**Files**: `frontend/app/disco/[id]/page.tsx`

### Project-Scoped Chat

Chat conversations started from a project context now have RAG search scoped to that project's linked documents.

**Features**:
- Project agent automatically selected when chatting from a project
- Taskmaster agent auto-selected alongside project agent for task-related queries
- Project context (name, description, status, scores) injected into chat system prompt
- RAG document search filtered to only documents linked to the project via `project_documents`
- Database-level document ID filtering for efficient scoped search
- Project dropdown in chat sidebar now loads correctly

**Files**: `backend/api/routes/chat.py`, `backend/services/project_chat.py`, `frontend/components/ConversationSidebar.tsx`

---

## February 7-12, 2026

### Taskmaster Sequenced Task Plans

Taskmaster can now create multi-step task plans directly from chat with sequenced execution order.

**Features**:
- Users describe a goal in chat; Taskmaster generates a sequenced plan of tasks
- Task proposals displayed as interactive cards in the chat stream
- Each task has a sequence number for execution order
- Accept/reject individual tasks or approve entire plan
- Accepted tasks created on the Kanban board ordered by sequence number

**Files**: `backend/api/routes/chat.py`, `backend/api/routes/tasks.py`, `backend/system_instructions/agents/taskmaster.xml`, `frontend/components/chat/TaskProposalCard.tsx`

### Task Board Improvements

Multiple enhancements to the task Kanban board for better usability.

**Changes**:
- **Notes field**: Tasks now have a free-text notes field for additional context
- **Condensed ticket layout**: Tighter card design with more visible information density
- **Sequence sort**: Column headers include option to sort by sequence number (for Taskmaster plans)
- **Cascade filtering**: Selecting a team or project cascades to filter the assignee dropdown accordingly
- **Project info on cards**: Task cards display associated project name
- **Stakeholder dropdown fix**: Properly loads stakeholder list in task create modal

**Files**: `frontend/components/tasks/TaskCreateModal.tsx`, `frontend/components/tasks/TaskKanbanBoard.tsx`, `frontend/components/tasks/TaskColumn.tsx`, `frontend/components/tasks/TaskFilters.tsx`, `database/migrations/070_task_notes.sql`

### HR to People Rename

Renamed "HR" to "People" across all team/department dropdowns and labels for consistency with modern organizational terminology.

**Files**: 16 files across backend and frontend

### Chat Agent Routing Improvements

Multiple fixes to ensure agents maintain identity and routing works correctly.

**Fixes**:
- Agent sticks with current selection instead of re-routing every message
- Agent identity no longer confused when switching agents mid-conversation
- @mention routing now supports taskmaster, project_agent, and initiative_agent
- @mentions take priority over default UI agent selection
- Project, initiative, and agent selections restored when returning to a conversation
- Dig-deeper links now work correctly on streamed messages

**Files**: `backend/services/chat_agent_service.py`, `backend/api/routes/chat.py`, `frontend/components/ChatInterface.tsx`

### DISCO Throughline Enhancement

Initiatives can now include structured input framing that threads through all 4 DISCO pipeline stages.

**Structured Inputs** (at initiative creation/edit):
- Problem statements with auto-generated IDs (ps-1, ps-2, ...)
- Hypotheses with type classification (assumption, belief, prediction)
- Known gaps with category (data, people, process, capability)
- Desired outcome state

**Agent Threading**:
- All 4 agents receive throughline context in their prompts (v1.1 prompts)
- Discovery Guide evaluates problem statements, targets gaps, reports per-hypothesis evidence
- Insight Analyst maps findings to hypothesis IDs, tracks gap coverage
- Initiative Builder traces bundles to throughline items
- Requirements Generator produces structured resolution

**Convergence Resolution** (structured output from requirements_generator):
- Hypothesis resolution table (confirmed/refuted/inconclusive with evidence)
- Gap status table (addressed/unaddressed/partially_addressed with findings)
- Recommended state changes with owners and deadlines
- "So What?" section: proposed state change, next human action, kill test

**Frontend**:
- Collapsible "Structured Framing" section in create/edit modals
- ThroughlineSummary component in initiative header with compact pills and expandable detail
- Color-coded resolution display in OutputViewer (green/red/amber status badges)

**Files**: `database/migrations/071_initiative_throughline.sql`, `backend/api/routes/disco/_shared.py`, `backend/services/disco/initiative_service.py`, `backend/services/disco/agent_service.py`, `backend/disco_agents/*-v1.1.md` (4 files), `frontend/components/disco/ThroughlineEditor.tsx`, `frontend/components/disco/ThroughlineSummary.tsx`, `frontend/app/disco/page.tsx`, `frontend/app/disco/[id]/page.tsx`, `frontend/components/disco/OutputViewer.tsx`

### DISCO Pipeline Restructuring

Comprehensive restructuring of the DISCO process based on UNHYPED methodology alignment. Renames user-facing terminology, deepens discovery analysis, strengthens convergence output, and completes the initiative-to-task spine.

**Terminology Changes** (UI text only, no database renames):
- "Initiative" renamed to "Discovery" in all user-facing text
- "Bundle" renamed to "Proposed Initiative" throughout UI
- Help documentation updated to match new terminology

**Value Alignment**:
- New flexible alignment model per discovery: target department, KPIs, department goals, company priority, strategic pillar, notes
- All fields optional - populated progressively as information emerges during discovery
- KPI tags and department goal badges displayed in discovery header
- Triage agent suggests KPIs and department context from linked documents

**Sponsor and Stakeholder Linking**:
- Executive sponsor field linked to stakeholders database
- Multiple stakeholder selection for involved parties
- Displayed in discovery header and create/edit modal

**Framing Extraction (Agent-Suggested Throughline)**:
- Triage agent analyzes linked documents and suggests problem statements, hypotheses, gaps, KPIs, and stakeholders
- Post-triage "Review Suggested Framing" panel for accepting or dismissing suggestions
- Framing hints in UI guide users to run triage before manually defining throughline
- Preferred workflow: link documents, run triage, review extracted framing

**Discovery Depth (Discovery Guide v1.2)**:
- Five Whys root cause analysis added to triage mode
- Framing extraction from documents during triage
- Gap taxonomy KB reference (data/people/process/capability) with investigation focus guidance
- Coverage tracker includes "Why This Matters" and absence reports

**Convergence Output (Requirements Generator v1.2)**:
- Tool and platform recommendations (simplest effective tool principle)
- Evaluation and QA plans
- Value alignment confirmation (verifies recommendation ties to KPIs)
- AI risk and compliance review (data classification, EU AI Act, platform governance)

**Direct Project Creation from Proposed Initiatives**:
- "Create Project" button on approved proposed initiatives (bypasses PRD generation)
- Score mapping: impact → roi_potential, feasibility → effort, urgency → alignment
- Projects linked to parent discovery for traceability

**Task Creation from State Changes**:
- "Create Tasks from State Changes" button on convergence output
- Select which state changes to create as tasks
- Tasks include `source_initiative_id` and `source_disco_output_id` for traceability
- "Next Human Action" from "So What?" section included as high-priority task option
- Tasks tagged with "disco" for filtering

**Resolution Annotations**:
- Users can override agent-assigned hypothesis/gap resolution statuses
- Status overrides with optional notes (e.g., "You: refuted" with explanation)
- Annotations persist alongside agent output for correction tracking

**Files**: `database/migrations/072_disco_restructure.sql`, `backend/api/routes/disco/_shared.py`, `backend/api/routes/disco/initiatives.py`, `backend/api/routes/disco/synthesis.py`, `backend/disco_agents/discovery-guide-v1.2.md`, `backend/disco_agents/requirements-generator-v1.2.md`, `backend/disco_agents/KB/gap-taxonomy-reference.md`, `backend/services/disco/agent_service.py`, `backend/services/disco/initiative_service.py`, `backend/services/disco/project_service.py`, `frontend/app/disco/page.tsx`, `frontend/app/disco/[id]/page.tsx`, `frontend/components/disco/OutputViewer.tsx`, `frontend/components/disco/SynthesisView.tsx`, `frontend/components/disco/ThroughlineSummary.tsx`, `frontend/components/disco/CheckpointPanel.tsx`, `frontend/components/disco/DiscoProcessMap.tsx`, `frontend/components/disco/DiscoOperationalizeMap.tsx` (28 files total)

---

## February 12-13, 2026

### Initiative Folder Links

Vault folders can now be linked to DISCO discoveries for automatic document association.

**Features**:
- Link vault folders directly to discoveries from the discovery detail page
- All documents in a linked folder are automatically associated with the initiative
- LinkedFoldersSection component shows linked folders with document counts
- Folder removal unlinks documents when a folder is disconnected
- Migration creates `disco_initiative_folder_links` table

**Files**: `database/migrations/074_initiative_folder_links.sql`, `backend/api/routes/disco/documents.py`, `backend/services/obsidian_sync.py`, `frontend/components/disco/LinkedFoldersSection.tsx`, `frontend/components/disco/KBDocumentBrowser.tsx`, `frontend/app/disco/[id]/page.tsx`

### Discovery Agent (Renamed from Initiative Agent)

The Initiative Agent has been renamed to "Discovery Agent" and now receives real initiative context and can propose structured framing.

**Rename**:
- User-facing name changed from "Initiative Agent" to "Discovery Agent" across all UI and help docs
- Internal key remains `initiative_agent` to avoid database migration
- Updated in: agent selector, chat agent service, system instruction XML, help documentation

**Context Injection** (fixes critical gap):
- Previously the agent claimed "full initiative context automatically injected" but received nothing
- New `build_initiative_context()` function fetches and formats as XML: initiative metadata, throughline (problem statements, hypotheses, gaps, desired outcome), agent output summaries, linked document names, and value alignment
- Context injected when `initiative_agent` selected and conversation has `initiative_id`
- Max tokens increased to 4096 for richer responses

**Framing Capability**:
- Discovery Agent can discuss initiative framing conversationally
- When ready, outputs structured `<framing_proposal>` JSON block with problem statements, hypotheses, gaps, and desired outcome state
- Backend extracts proposal from response (same pattern as Taskmaster's `<task_proposals>`)
- Frontend renders FramingProposalCard with checkboxes for selective application
- "Apply to Discovery" merges selected items into existing throughline via PATCH endpoint
- Applied badge shown after successful application

**Files**: `backend/agents/initiative_agent.py`, `backend/services/chat_agent_service.py`, `backend/services/disco/initiative_context.py` (new), `backend/api/routes/chat.py`, `backend/system_instructions/agents/initiative_agent.xml`, `backend/docs_help/user/02-chat.md`, `frontend/components/AgentSelector.tsx`, `frontend/components/ChatInterface.tsx`, `frontend/components/ChatMessage.tsx`, `frontend/components/chat/FramingProposalCard.tsx` (new)

### Project Creation from Discovery View

Added the ability to create projects directly from the discovery detail page.

**Features**:
- "Create Project" button in discovery header
- Uses existing ProjectCreateModal with auto-linking to the current initiative
- Projects created this way appear in the discovery's Projects tab

**Files**: `frontend/app/disco/[id]/page.tsx`, `frontend/components/projects/ProjectCreateModal.tsx`

### UI Polish

- Added text labels to folder select-all buttons in KB document browsers for improved intuitiveness
- Updated DISCO UI references from "triage agent" to "Discovery Guide"

**Files**: `frontend/components/disco/KBDocumentBrowser.tsx`, `frontend/components/projects/ProjectDocumentBrowser.tsx`

### Kraken Agent (Task Automation)

New agent that evaluates project tasks for autonomous AI execution and runs approved tasks non-destructively.

**Phase 1: Task Evaluation**
- "Release the Kraken" button in project Tasks tab
- 5-dimension confidence framework: information sufficiency, output clarity, execution feasibility, completeness achievable, domain fit (0-20 each)
- Tasks categorized as: Automatable (70-100%), Assistable (40-69%), Manual (<40%)
- Computes agenticity score per project (displayed in Scores tab)

**Phase 2: Task Execution**
- User selects which tasks to execute (automatable pre-selected)
- Uses project context, KB documents, initiative documents, and web search
- Output saved as task comments (non-destructive, never modifies task status)
- Substantial outputs (>200 words) also saved as KB documents tagged `["kraken", "auto-generated"]`
- KB documents auto-linked to the project

**Design Decisions**:
- Intentionally separate from Taskmaster (creation/tracking vs evaluation/execution)
- Staleness detection via MD5 hash of task states
- Web search enabled (up to 5 searches per task) for real-time research

**Files**: `backend/agents/kraken.py`, `backend/services/task_kraken.py`, `backend/system_instructions/agents/kraken.xml`, `backend/api/routes/projects.py`, `frontend/components/projects/KrakenPanel.tsx`, `frontend/components/projects/ProjectDetailModal.tsx`, `frontend/components/AgentIcon.tsx`, `database/migrations/075_task_kraken.sql`

### DISCO Process Map

Added a standalone HTML process map visualizing the complete DISCO pipeline.

**Coverage**:
- 5-stage pipeline overview (D-I-S-C-O) with 4 checkpoint gates
- Stage details with agent names, versions, inputs, and outputs
- Discovery Agent three operating modes (Triage, Planning, Coverage)
- Investigation framing (throughline) system with three definition methods
- Checkpoint gate checklists
- Convergence output document types (PRD, Evaluation, Decision Framework)
- Multi-pass synthesis architecture
- Operationalization paths (direct project, AI-extracted project, tasks from state changes)
- Initiative lifecycle and full traceability spine
- Key principles

**Files**: `frontend/public/disco-process-map.html`

### AI Platform Governance Maps

Added two HTML visualizations for AI platform governance, embedded as tabs on the DISCO page.

**Platform Process Map** (`/platform-process-map.html`):
- Approved platform set: Glean, Gemini/Gems, NotebookLM, Claude, MuleSoft, Custom
- Platform comparison matrix across 6 dimensions (Reliability, Governance, Traceability, Auditability, Fault Tolerance, German Approved)
- Quick decision paths for common scenarios (JD generator, cash app automation, codebase analysis, etc.)
- Hub-and-spoke governance model

**Platform Decision Tree** (`/platform-decision-tree.html`):
- Guided decision flow for selecting the right AI platform
- Considers data sensitivity, user scope, integration needs, and governance requirements

**Files**: `frontend/public/platform-process-map.html`, `frontend/public/platform-decision-tree.html`, `frontend/app/disco/page.tsx`

---

## February 13-14, 2026

### Thesis Manifesto

New page defining 10 core organizational principles for AI strategy work.

**Features**:
- Tabbed layout: Principles tab (card format with core statement and elaboration) and XML tab (agent-loadable format)
- 10 principles covering: state change orientation, problems before solutions, outcomes not activities, multiple perspectives, simplest effective tool, trace connections, and more
- Accessible from top navigation bar
- Designed to guide both human decision-making and agent behavior

**Files**: `frontend/app/manifesto/page.tsx`, `frontend/components/Header.tsx`

### Agent Selection Guide Redesign

Redesigned the agent selection tree from a tool-picker into a deductive discovery process.

**Old Flow**: Category → Tool subcategory → Single agent (2 clicks)
**New Flow**: Situation → Context → Recommendation (3 steps, tool-agnostic)

**Three Modes**:
- **Discovery Mode**: 3-step wizard asks situational questions before recommending agents. Results include primary agents with "why" explanations, supporting agents, suggested approach, and manifesto principle alignment
- **Browse All Agents**: Catalog of all 22 agents organized by category
- **Visual Map**: Full decision tree visualization showing all paths and outcomes

**Multi-Agent Results**: Recommendations can suggest 2-3 agents with roles (primary + supporting) and Meeting Room sessions when multi-perspective analysis is needed.

**Files**: `frontend/public/agent-selection-tree.html`

### Iframe Theme Inheritance

All 8 embedded HTML visualizations now inherit the parent app's theme settings.

**How It Works**:
- Sync script reads ThemeContext CSS custom properties from the parent frame (bg-page, bg-card, bg-hover, text-primary, text-secondary, text-muted, border-default, primary, primary-hover)
- Computes full gray ramp (--gray-50 through --gray-900) via color interpolation between anchor points
- Polls every 200ms until ThemeContext applies inline styles (handles async auth + API delay)
- MutationObserver detects runtime theme changes
- Falls back to prefers-color-scheme media query for standalone viewing
- Supports bidirectional dark/light switching

**Files affected** (8 HTML files in `frontend/public/`): `agent-selection-tree.html`, `data-flow-map.html`, `meeting-rooms-process-map.html`, `throughline-process-map.html`, `platform-process-map.html`, `platform-decision-tree.html`, `kraken-process-map.html`, `project-scoring-map.html`

### N8N Removal

Removed all N8N references from platform process map. N8N is no longer part of the approved platform set.

**Files**: `frontend/public/platform-process-map.html`

---

## February 15, 2026

### Agent Context Token Budget

DISCO agents now enforce a character budget when loading initiative documents, preventing prompt overflow errors.

**Problem Solved**:
- Initiatives with many linked documents (83+) could exceed the 200k token model context limit
- This caused a 400 error ("prompt is too long") when running agents like Discovery Guide

**Solution**:
- `get_all_initiative_content()` now accepts a `max_chars` parameter (default 500k chars, ~150k tokens)
- Documents loaded in order of link recency (most recently linked first)
- When budget exceeded, remaining documents skipped with a context budget notice
- Leaves room for system prompt, agent instructions, previous outputs, and KB folder documents

**Files**: `backend/services/disco/document_service.py`

### KB Duplicate Document Cleanup

Cleaned up duplicate document records caused by multiple copies of the same files in different Obsidian vault folders.

**Root Cause**:
- Three mirrored folder trees in the vault (`GitHub/archived/purdy-cf/`, `projects/strategic-account-planning/purdy/`, `agents/BuRDy/`) contained copies of the same files
- Obsidian sync correctly created separate records per path, but the content was identical
- 83 documents linked to a single initiative included 18 duplicate filename entries

**Cleanup**:
- Removed 209 duplicate files from the Obsidian vault (kept most recent of each)
- Removed 452 duplicate document records from the database (kept newest by `uploaded_at`)
- Cleaned up orphaned initiative and project document links
- KB reduced from 1,851 to ~1,399 documents with 0 remaining filename duplicates
