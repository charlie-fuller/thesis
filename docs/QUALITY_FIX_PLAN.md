# Quality Fix Plan

## Overview

This document provides a systematic plan to address all code quality issues identified in the comprehensive test run. Execute each phase in order, committing after each phase.

**IMPORTANT: This plan is designed for autonomous overnight execution without user interaction.**

**Total Issues:**
- Phase 1: 111 complexity violations (C901)
- Phase 2: 1475 line-length violations (E501)
- Phase 3: 6923 type hint gaps (prioritized subset)
- Phase 4: 208 frontend warnings

---

## Autonomous Execution Rules

### Global Decision Rules

1. **Test Verification**: Run tests after EVERY batch of changes (max 5 files per batch)
2. **Rollback Trigger**: If tests fail, revert the batch and skip those files
3. **Commit Frequency**: Commit after each successful batch
4. **No Interaction Required**: Use these rules to make all decisions autonomously

### When to Use `# noqa` vs Refactor

| Scenario | Action |
|----------|--------|
| Complexity > 25 | Always refactor |
| Complexity 16-25 | Refactor if clear extraction points exist |
| Complexity 11-15 | Refactor if simple; noqa if deeply nested async/error handling |
| Test files | Add noqa - don't refactor test complexity |
| Agent system instructions (long strings) | Add noqa: E501 |

### When to Add Dependencies vs Disable Hook Rule

| Scenario | Action |
|----------|--------|
| Function is stable, defined outside component | Add to dependency array |
| Adding dep would cause infinite loop | Disable with eslint-disable-next-line |
| Dep is intentionally omitted (mount-only effect) | Disable with eslint-disable-next-line + comment why |
| Function is defined inside component with useCallback | Add to dependency array |

---

## Rollback Procedure

If tests fail after a batch of changes:

```bash
# 1. Identify failed files
git diff --name-only

# 2. Revert all changes in current batch
git checkout -- <file1> <file2> ...

# 3. Log skipped files for manual review
echo "SKIPPED: <file> - <reason>" >> /tmp/quality_fix_skipped.log

# 4. Continue with next batch
```

---

## Verification Checkpoints

Run after EACH batch of changes:

```bash
# Backend - Quick test (30 seconds)
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/test_integration.py -v --tb=short -x

# Frontend - Type check (20 seconds)
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/frontend
npm run build 2>&1 | tail -10

# If both pass, commit and continue
```

---

## Phase 1: Complexity Refactoring (111 Violations)

### Complete Violation List by Severity

#### Critical Tier (Complexity > 25) - 6 Functions

| # | File | Function | Complexity | Strategy |
|---|------|----------|------------|----------|
| 1 | `api/routes/chat.py:558` | `chat_stream` | 57 | Extract: error handling, context building, streaming logic |
| 2 | `api/routes/chat.py:594` | `generate_stream` | 56 | Extract: message processing, tool handling, final response |
| 3 | `api/routes/chat.py:140` | `chat` | 30 | Extract: validation, context building, response formatting |
| 4 | `agents/taskmaster.py:178` | `_get_task_context` | 26 | Extract: each task type into separate handler |
| 5 | `agents/oracle.py:463` | `_format_analysis` | 23 | Use dictionary dispatch for section formatting |
| 6 | `api/routes/admin/help_docs.py:265` | `update_help_document` | 21 | Extract: validation, update logic, embedding logic |

#### High Tier (Complexity 16-25) - 25 Functions

| # | File | Function | Complexity | Strategy |
|---|------|----------|------------|----------|
| 7 | `api/routes/admin/analytics.py:20` | `get_usage_trends` | 20 | Extract: query building, data aggregation |
| 8 | `api/routes/admin/help_docs.py:100` | `reindex_help_document` | 19 | Extract: embedding logic |
| 9 | `services/stakeholder_extractor.py:142` | `_parse_response` | 17 | Dictionary dispatch for field parsing |
| 10 | `tests/test_engagement.py:238` | `calculate_level` | 17 | Add noqa (test file) |
| 11 | `api/routes/documents.py:134` | `upload_document` | 16 | Extract: validation, processing, storage |
| 12 | `services/obsidian_sync.py:224` | `_convert_text` | 16 | Extract: each format handler |
| 13 | `services/obsidian_sync.py:299` | `_extract_enhanced_metadata` | 16 | Extract: each metadata type |
| 14 | `services/graph/neo4j_service.py:316` | `get_graph_context` | 16 | Extract: query building helpers |
| 15 | `api/routes/disco/chat.py:125` | `api_extract_project_from_chat` | 15 | Extract: extraction logic |
| 16 | `api/routes/disco/outputs.py:21` | `get_output` | 15 | Extract: format handling |
| 17 | `services/project_context.py:39` | `get_scoring_related_documents` | 15 | Extract: similarity logic |
| 18 | `services/task_auto_extractor.py:19` | `extract_tasks_from_document` | 15 | Extract: parsing logic |
| 19 | `services/task_auto_extractor.py:220` | `accept_task_candidate` | 15 | Extract: validation |
| 20 | `services/task_digest.py:181` | `_build_markdown` | 15 | Extract: section builders |
| 21 | `services/task_extractor.py:469` | `_extract_due_date` | 15 | Extract: date pattern handlers |
| 22 | `api/routes/disco/prd.py:26` | `generate_prd` | 15 | Extract: generation logic |
| 23 | `api/routes/admin/analytics.py:692` | `get_keyword_trends` | 14 | Extract: aggregation logic |
| 24 | `api/routes/admin/health.py:19` | `get_system_health` | 14 | Extract: each health check |
| 25 | `api/routes/admin/users_and_clients.py:108` | `export_conversations` | 14 | Extract: export formatting |
| 26 | `services/disco/discovery_service.py:177` | `_process_discovery_with_graph` | 14 | Extract: graph processing |
| 27 | `services/graph/neo4j_service.py:248` | `get_agent_context` | 14 | Extract: context builders |
| 28 | `services/stakeholder_deduplicator.py:104` | `_calculate_match_score` | 14 | Extract: scoring components |
| 29 | `services/stakeholder_linker.py:39` | `_find_related_opportunities` | 14 | Extract: query logic |
| 30 | `services/task_extractor.py:238` | `extract_with_llm` | 14 | Extract: prompt building |
| 31 | `api/routes/knowledge_base.py:81` | `search_knowledge_base` | 14 | Extract: filtering logic |

#### Medium Tier (Complexity 11-15) - 80 Functions

| # | File | Function | Complexity |
|---|------|----------|------------|
| 32 | `agents/coordinator.py:851` | `stream` | 12 |
| 33 | `agents/coordinator.py:1003` | `_get_graph_context` | 11 |
| 34 | `api/routes/admin/help_docs.py:446` | `get_help_analytics` | 12 |
| 35 | `api/routes/chat.py:1764` | `dig_deeper` | 11 |
| 36 | `api/routes/disco/agents.py:39` | `run_agent` | 13 |
| 37 | `api/routes/disco/agents.py:218` | `run_agent_stream` | 13 |
| 38 | `api/routes/disco/insights.py:25` | `get_insights` | 12 |
| 39 | `api/routes/disco/synthesis.py:53` | `create_synthesis_bundle` | 11 |
| 40 | `api/routes/documents.py:266` | `resync_document` | 12 |
| 41 | `api/routes/documents.py:371` | `update_document` | 13 |
| 42 | `api/routes/documents.py:454` | `update_document_classification` | 11 |
| 43 | `api/routes/granola.py:174` | `create_granola_document` | 12 |
| 44 | `api/routes/granola.py:399` | `process_transcript_sync` | 11 |
| 45 | `api/routes/knowledge_base.py:311` | `kb_search_internal` | 11 |
| 46 | `api/routes/meetings.py:60` | `send_meeting_message` | 12 |
| 47 | `api/routes/meetings.py:304` | `create_meeting` | 11 |
| 48 | `api/routes/meetings.py:461` | `start_autonomous_discussion` | 13 |
| 49 | `api/routes/meetings.py:636` | `autonomous_turn` | 12 |
| 50 | `api/routes/obsidian.py:40` | `sync_vault` | 12 |
| 51 | `api/routes/obsidian.py:100` | `full_vault_sync` | 11 |
| 52 | `api/routes/projects.py:88` | `create_project` | 11 |
| 53 | `api/routes/projects.py:157` | `update_project` | 12 |
| 54 | `api/routes/projects.py:340` | `score_projects` | 12 |
| 55 | `api/routes/projects.py:496` | `get_project_scores_history` | 11 |
| 56 | `api/routes/stakeholders.py:180` | `generate_profile_summary` | 11 |
| 57 | `api/routes/stakeholders.py:291` | `dedupe_stakeholders` | 13 |
| 58 | `api/routes/stakeholders.py:375` | `get_or_create_stakeholder` | 12 |
| 59 | `api/routes/tasks.py:124` | `create_task` | 11 |
| 60 | `api/routes/tasks.py:276` | `update_task` | 11 |
| 61 | `api/routes/tasks.py:403` | `batch_update_tasks` | 12 |
| 62 | `api/routes/transcripts.py:124` | `process_transcript` | 11 |
| 63 | `api/routes/usage.py:36` | `get_user_usage` | 11 |
| 64 | `api/utils/error_handler.py:51` | `handle_supabase_error` | 11 |
| 65 | `pipeline/document_processor.py:84` | `process_document` | 11 |
| 66 | `pipeline/granola_scanner.py:90` | `scan_and_process` | 14 |
| 67 | `pipeline/granola_scanner.py:249` | `_process_note` | 11 |
| 68 | `pipeline/granola_scanner.py:369` | `_should_skip_transcript` | 11 |
| 69 | `services/autonomous_discussion.py:74` | `run_turn` | 12 |
| 70 | `services/disco/agent_runner.py:156` | `_run_discovery_agent` | 11 |
| 71 | `services/disco/discovery_service.py:40` | `create_discovery_thread` | 11 |
| 72 | `services/disco/discovery_service.py:127` | `send_discovery_message` | 12 |
| 73 | `services/disco/prd_generator.py:64` | `generate_prd` | 12 |
| 74 | `services/disco/prd_generator.py:182` | `_create_prd_sections` | 11 |
| 75 | `services/disco/prd_generator.py:246` | `_format_prd_markdown` | 11 |
| 76 | `services/document_classifier.py:209` | `classify_batch` | 12 |
| 77 | `services/embedding_service.py:40` | `embed_and_store` | 12 |
| 78 | `services/engagement_calculator.py:94` | `calculate_level` | 13 |
| 79 | `services/graph/neo4j_service.py:57` | `sync_to_neo4j` | 14 |
| 80 | `services/graph/neo4j_service.py:125` | `sync_stakeholder_to_neo4j` | 11 |
| 81 | `services/graph/neo4j_service.py:180` | `sync_document_to_neo4j` | 12 |
| 82 | `services/help_chat_service.py:88` | `chat` | 13 |
| 83 | `services/help_indexer.py:88` | `_index_file` | 13 |
| 84 | `services/help_indexer.py:181` | `_chunk_content` | 11 |
| 85 | `services/meeting_service.py:40` | `send_message` | 12 |
| 86 | `services/meeting_service.py:130` | `process_message` | 11 |
| 87 | `services/memo_generator.py:25` | `generate_memo` | 11 |
| 88 | `services/obsidian_sync.py:45` | `sync_vault` | 13 |
| 89 | `services/obsidian_sync.py:119` | `_process_file` | 14 |
| 90 | `services/opportunity_extractor.py:24` | `extract_opportunities` | 13 |
| 91 | `services/opportunity_extractor.py:110` | `_parse_opportunities` | 12 |
| 92 | `services/profile_summarizer.py:34` | `generate_summary` | 11 |
| 93 | `services/project_confidence.py:142` | `evaluate_project_confidence` | 12 |
| 94 | `services/project_taskmaster.py:22` | `chat_with_taskmaster` | 13 |
| 95 | `services/research_scheduler.py:422` | `run_daily_research` | 11 |
| 96 | `services/stakeholder_linker.py:102` | `_find_related_tasks` | 12 |
| 97 | `services/web_researcher.py:308` | `_extract_sources_from_response` | 11 |
| 98 | `system_instructions_loader.py:72` | `load_user_system_instructions` | 11 |
| 99 | `tests/test_engagement.py:152` | `collect_signals` | 12 |
| 100-111 | (Additional medium-complexity functions) | Various | 11-13 |

### Execution Order for Phase 1

1. **Critical tier first** - highest impact
2. **High tier second** - moderate refactoring
3. **Medium tier last** - simple fixes or noqa

### Refactoring Patterns

**Pattern A: Extract Helper Functions**
```python
# Before (complexity 15)
def complex_function(data):
    if condition1:
        # 20 lines of logic A
    elif condition2:
        # 20 lines of logic B
    else:
        # 20 lines of logic C

# After (complexity 5 each)
def _handle_case_a(data): ...
def _handle_case_b(data): ...
def _handle_case_c(data): ...

def complex_function(data):
    if condition1:
        return _handle_case_a(data)
    elif condition2:
        return _handle_case_b(data)
    return _handle_case_c(data)
```

**Pattern B: Dictionary Dispatch**
```python
# Before
if status == "pending":
    do_pending()
elif status == "active":
    do_active()
elif status == "complete":
    do_complete()

# After
handlers = {
    "pending": do_pending,
    "active": do_active,
    "complete": do_complete,
}
handlers.get(status, do_default)()
```

**Pattern C: Early Returns**
```python
# Before
def process(data):
    if data:
        if data.valid:
            if data.ready:
                # actual logic

# After
def process(data):
    if not data:
        return None
    if not data.valid:
        return None
    if not data.ready:
        return None
    # actual logic
```

### Commit Message Template
```
refactor: reduce cyclomatic complexity in [file]

- Extract [function_name] into smaller helper functions
- Complexity reduced from X to Y

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## Phase 2: Line Length Fixes (1475 Violations)

### Strategy

Most E501 violations can be auto-fixed:

```bash
# Preview what will change
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
.venv/bin/ruff check . --select=E501 --fix --diff

# Apply fixes
.venv/bin/ruff check . --select=E501 --fix
```

### Manual Categories

| Category | Action |
|----------|--------|
| Agent system instructions | Add `# noqa: E501` - breaking harms readability |
| XML prompt strings | Add `# noqa: E501` |
| URLs in comments | Add `# noqa: E501` |
| Everything else | Auto-fix or manual wrap |

---

## Phase 3: Type Hints (Prioritized Subset)

**Do incrementally - not in overnight run**

Priority files:
1. `api/routes/projects.py`
2. `api/routes/tasks.py`
3. `api/routes/conversations.py`
4. `services/disco/initiative_service.py`

---

## Phase 4: Frontend Warnings (208 Total)

### Complete Breakdown by Category

| Category | Count | Strategy |
|----------|-------|----------|
| Unused imports/variables | 132 | Remove or prefix with `_` |
| React Hook dependencies | 52 | See decision rules above |
| Console statements | 18 | Replace with logger or add eslint-disable |
| `<img>` vs `<Image />` | 4 | Keep as-is for external URLs; use Image for local |
| Custom font warning | 1 | Add noqa - intentional |
| Other | 1 | Case by case |

### Unused Imports - Complete List

**Files with 5+ unused imports (high priority):**
- `app/documents/page.tsx` - 15 unused
- `components/kb/KBDocumentsContent.tsx` - 21 unused
- `app/disco/[id]/page.tsx` - 6 unused
- `components/disco/OutputViewer.tsx` - 7 unused
- `components/disco/PRDViewer.tsx` - 4 unused
- `components/disco/SynthesisView.tsx` - 4 unused

### React Hook Dependency Warnings - Complete List

| File | Line | Missing Deps | Action |
|------|------|--------------|--------|
| `app/admin/agents/[id]/page.tsx` | 212 | `fetchAgent` | Add to deps |
| `app/admin/agents/[id]/page.tsx` | 219 | `fetchScanStats` | Add to deps |
| `app/admin/conversations/[id]/page.tsx` | 54 | `fetchConversation` | Add to deps |
| `app/admin/conversations/page.tsx` | 58 | `fetchConversations` | Add to deps |
| `app/admin/core-documents/[clientId]/page.tsx` | 83 | `loadData` | Add to deps |
| `app/admin/documents/page.tsx` | 81,86 | `loadDocuments` | Add to deps |
| `app/admin/help-system/page.tsx` | 156 | `checkIndexingStatus` | Disable - mount only |
| `app/admin/help-system/page.tsx` | 165 | `fetchAnalytics` | Disable - mount only |
| `app/admin/users/[userId]/page.tsx` | 53 | `fetchUserData` | Add to deps |
| `app/disco/page.tsx` | 285 | `loadInitiatives` | Add to deps |
| `app/documents/page.tsx` | 186,234,277,370 | Various | Add to deps |
| `app/intelligence/page.tsx` | 147,153 | `loadStakeholderData` | Add to deps |
| `app/meeting-prep/[stakeholder_id]/page.tsx` | 241 | `loadData` | Add to deps |
| `app/meeting-room/[id]/page.tsx` | 122 | `loadMeeting`, `loadMessages` | Add to deps |
| `components/AgentChatTab.tsx` | 52 | `loadConversations` | Add to deps |
| `components/ChatInterface.tsx` | 150 | `loadConversation` | Add to deps |
| `components/ConversationSidebar.tsx` | 71 | `loadConversations` | Add to deps |
| `components/DocumentUpload.tsx` | 256 | `addFilesToQueue`, `getFilesFromDataTransfer` | Disable - stable refs |
| `components/EngagementTrendsChart.tsx` | 56 | `fetchData` | Add to deps |
| `components/HelpSystemPanel.tsx` | 50 | `checkIndexingStatus` | Disable - mount only |
| `components/RecentActivityFeed.tsx` | 37 | `fetchActivity` | Add to deps |
| `components/StorageIndicator.tsx` | 43 | `fetchStorageData` | Add to deps |
| `components/UsageAnalytics.tsx` | 112 | `fetchAnalytics` | Disable - mount only |
| `components/admin/DocumentsContent.tsx` | 69,75 | `loadDocuments` | Add to deps |
| `components/disco/KBDocumentBrowser.tsx` | 83,90 | Various | Add to deps |
| `components/disco/PRDViewer.tsx` | 243 | `loadPRDs` | Add to deps |
| `components/disco/SynthesisView.tsx` | 244 | `loadBundles` | Add to deps |
| `components/kb/KBDocumentsContent.tsx` | 744,762,833,876,885,969 | Various | Add to deps |
| `components/kb/TagManagerTab.tsx` | 97,119,127 | Various | Add to deps |
| `components/projects/DocumentViewerModal.tsx` | 64 | `document`, `fetchDocumentContent` | Add to deps |
| `components/projects/ProjectCandidateReviewModal.tsx` | 87 | `loadCandidate` | Add to deps |
| `components/projects/ProjectDetailModal.tsx` | 361 | Many | Add to deps |
| `components/projects/TaskmasterChatSection.tsx` | 66 | `handleAutoGenerate` | Disable - intentional |

### Auto-Fix Command

```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/frontend
npm run lint -- --fix
```

This will auto-remove unused imports. Manual fixes needed for hook dependencies.

---

## Execution Summary

### Overnight Autonomous Run Order

1. **Phase 2**: Auto-fix line length (`ruff check --fix`) - 5 min
2. **Phase 4 (partial)**: Auto-fix unused imports (`eslint --fix`) - 2 min
3. **Phase 1**: Critical tier complexity (6 functions) - 2 hours
4. **Phase 1**: High tier complexity (25 functions) - 3 hours
5. **Phase 4**: React hook dependencies (52 manual fixes) - 1 hour

### Verification Between Phases

```bash
# Backend tests
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/test_integration.py -v -x

# Frontend build
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/frontend
npm run build

# Lint check
npm run lint 2>&1 | grep -c warning
```

---

## Prompt to Execute This Plan

```
Execute the Quality Fix Plan from /docs/QUALITY_FIX_PLAN.md autonomously.

Rules:
- Work through phases in order
- Commit after each batch of 5 files
- If tests fail, revert batch and log to /tmp/quality_fix_skipped.log
- Use decision rules in the document - no questions
- Stop if more than 3 consecutive batches fail
```
