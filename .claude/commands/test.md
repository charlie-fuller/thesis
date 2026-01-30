# Run Test Suite

Run the Thesis test suite with options for quick unit tests, full pytest regimen, or comprehensive production E2E tests.

## Usage

```
/test          # Run full regimen: pytest stages 1-4 + basic E2E (default)
/test --quick  # Run core unit tests only (fastest)
/test --full   # Run comprehensive E2E on production (28 scenarios)
```

**Note:** Cleanup of E2E test data runs automatically at the end of any E2E test (default or --full modes).

## Prerequisites

### For --quick and default modes (pytest)
1. **dotenvx** - The `.env` file is encrypted. Use `dotenvx run` to decrypt and inject environment variables.
2. **DOTENV_PRIVATE_KEY** - Required for decryption. Found in `backend/.env.keys`.

### For --full mode (production E2E)
1. **Chrome DevTools MCP** - Chrome browser must be open with DevTools MCP connected
2. **Authentication** - You should be logged into thesis-mvp.vercel.app in Chrome

---

# OPTION: --quick (Unit Tests Only)

If `--quick` option is specified, run ONLY Stage 1 (unit tests) and skip everything else.

---

# DEFAULT MODE: Full Pytest Regimen + Basic E2E

Execute ALL test stages below in order. Do NOT stop if one stage fails - continue to the next stage and report all results at the end.

## Stage 1: Unit Tests

Run core unit tests first:

```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest \
  tests/test_document_classifier.py \
  tests/test_tasks.py \
  tests/test_projects.py \
  tests/test_engagement.py \
  tests/test_agents_new.py \
  tests/test_vibe_coding_bugs.py \
  tests/test_rigorous.py \
  -v --tb=short --timeout=60 2>&1 || true
```

Record: passed, failed, skipped counts.

## Stage 2: Integration Tests

Run integration and Obsidian sync tests:

```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest \
  tests/test_integration.py \
  tests/test_obsidian_sync.py \
  -v --tb=short --timeout=120 2>&1 || true
```

Record: passed, failed, skipped counts.

## Stage 3: Extended Tests

Run all remaining tests (excluding E2E):

```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/ \
  --ignore=tests/e2e/ \
  --ignore=tests/e2e_browser_tests.py \
  --ignore=tests/test_document_classifier.py \
  --ignore=tests/test_tasks.py \
  --ignore=tests/test_projects.py \
  --ignore=tests/test_engagement.py \
  --ignore=tests/test_agents_new.py \
  --ignore=tests/test_vibe_coding_bugs.py \
  --ignore=tests/test_rigorous.py \
  --ignore=tests/test_integration.py \
  --ignore=tests/test_obsidian_sync.py \
  -v --tb=short --timeout=120 2>&1 || true
```

Record: passed, failed, skipped counts.

## Stage 4: Basic E2E Browser Tests

E2E tests use Chrome DevTools MCP to automate browser interactions.

### Step 4.1: Check Server Status

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "Frontend not running"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "Backend not running"
```

### Step 4.2: Start Servers (if not running)

If servers are not running, start them in background:

**Backend** (run in background):
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
JWK=$(curl -s "https://imdavfgreeddxluslsdl.supabase.co/auth/v1/.well-known/jwks.json" | jq -c '.keys[0]')
SUPABASE_JWT_SECRET="$JWK" \
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m uvicorn main:app --reload --port 8000
```

**Frontend** (run in background):
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/frontend
npm run dev
```

Wait for both servers to be ready.

### Step 4.3: Verify Chrome DevTools MCP Connection

Use `mcp__chrome-devtools__list_pages` to verify Chrome is connected.

### Step 4.4: Run Basic E2E Test Scenarios

**Test 1: Auth Login Success**
1. Navigate to `http://localhost:3000`
2. Verify user is authenticated (user menu visible) or complete login flow

**Test 2: Chat Send Message**
1. Navigate to `/chat`
2. Send test message: "Hello, this is an E2E test"
3. Verify AI agent responds

**Test 3: KB Search** (optional)
1. Navigate to `/kb`
2. Search for a term
3. Verify results appear

**Test 4: Tasks Create**
1. Navigate to `/tasks`
2. Click "Add Task"
3. Create task: "E2E Test Task - Automated"
4. Verify task appears in To Do column

**Test 5: Tasks Kanban Drag**
1. Drag test task to In Progress
2. Verify task persists after refresh

### Step 4.5: Cleanup Test Data

After running E2E tests, clean up any test data created:

1. Navigate to `/tasks`
2. Delete any tasks containing "E2E Test" in the title
3. Navigate to `/chat`
4. Delete any conversations created during testing

### Step 4.6: Record E2E Results

Record pass/fail for each scenario.

---

## Default Mode Summary

After ALL stages complete, provide a summary table:

```
============================================
TEST SUMMARY
============================================
Stage 1 - Unit Tests:        XX passed, XX failed, XX skipped
Stage 2 - Integration Tests: XX passed, XX failed, XX skipped
Stage 3 - Extended Tests:    XX passed, XX failed, XX skipped
Stage 4 - E2E Browser Tests: XX passed, XX failed
--------------------------------------------
TOTAL:                       XXX passed, XXX failed, XXX skipped
============================================
```

---

# OPTION: --full (Comprehensive Production E2E)

Run comprehensive end-to-end test of all Thesis functionality using Chrome DevTools MCP on production.

**Test Configuration:**
- **Production URL**: https://thesis-mvp.vercel.app
- **Test Data Prefix**: All test data uses "E2E Test" prefix for easy cleanup

Execute ALL test phases in order. After each test, record PASS/FAIL.

---

## PHASE 1: AUTHENTICATION & NAVIGATION

### Test 1.1: Verify Authentication State

1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify user is logged in (user menu visible) or complete login flow

*Expected:* User is authenticated with access to all app sections

### Test 1.2: Navigation Bar Verification

1. Verify presence of navigation links: Dashboard, Chat, Tasks, Projects, Intelligence, Agents, KB, DISCo
2. Click each link and verify page loads without error

*Expected:* All navigation links present and functional

---

## PHASE 2: DASHBOARD

### Test 2.1: Dashboard Load

1. Navigate to `https://thesis-mvp.vercel.app/`
2. Verify dashboard content loads
3. Check for console errors

*Expected:* Dashboard loads without errors

---

## PHASE 3: CHAT & AI AGENTS

### Test 3.1: New Chat Creation

1. Navigate to `/chat`
2. Click "+ New Chat" button
3. Verify chat interface with message input

### Test 3.2: Send Message and Receive Response

1. Fill message: "E2E Test: Hello, this is an automated test message. Please acknowledge."
2. Click Send
3. Wait for AI response

*Expected:* AI agent responds with acknowledgment

### Test 3.3: KB Context Chat (CRITICAL)

1. Click "+ New Chat"
2. Send: "E2E KB Test: What are the key topics and themes from the documents added to the Knowledge Base in the last week? Please cite specific documents."
3. Wait for response (10-15 seconds)
4. **Verify response contains:**
   - References to specific KB documents
   - Actual content/themes from documents
   - Agent attribution

*Pass Criteria:*
- At least 1 document cited in response
- Response contains substantive KB content

### Test 3.4: Agent Selection

1. Find agent selector and select a specific agent (e.g., "Atlas")
2. Send: "E2E Agent Test: Brief research summary on AI trends"
3. Verify response comes from selected agent

### Test 3.5: Chat Conversation Actions

1. Test Rename button on a conversation
2. Change name to "E2E Renamed Conversation"
3. Test Archive if available

---

## PHASE 4: TASKS (KANBAN)

### Test 4.1: View Tasks Board

1. Navigate to `/tasks`
2. Verify Kanban columns: To Do, In Progress, Done
3. Note current task counts

### Test 4.2: Create New Task

1. Click "Add Task"
2. Fill: "E2E Test Task - Full Suite Verification"
3. Click Create
4. Verify task appears in To Do

### Test 4.3: Drag Task to In Progress

1. Drag test task to In Progress column
2. Refresh page
3. Verify task persisted in new column

### Test 4.4: Task Details Modal

1. Click on test task card
2. Verify details display (title, description, status)

---

## PHASE 5: PROJECTS

### Test 5.1: View Projects List

1. Navigate to `/projects`
2. Verify projects list or pipeline view

### Test 5.2: Create New Project

1. Click "Add Project"
2. Fill: "E2E Test Project - Automated Verification"
3. Click Create
4. Verify project appears

### Test 5.3: Project Pipeline View

1. Verify status columns (Discovery, Evaluation, etc.)
2. Verify test project in correct column

---

## PHASE 6: KNOWLEDGE BASE

### Test 6.1: KB Page Load

1. Navigate to `/kb`
2. Verify document list/navigator and search

### Test 6.2: KB Navigator Search

1. Search for "AI"
2. Verify results appear

### Test 6.3: Document Preview

1. Click on a document
2. Verify preview displays title and content

### Test 6.4: Tag Filtering

1. Select a tag filter
2. Verify documents filter correctly

---

## PHASE 7: AGENTS

### Test 7.1: Agents Directory

1. Navigate to `/agents`
2. Verify agent cards display
3. Look for: Atlas, Compass, Capital, Guardian

### Test 7.2: Agent Details

1. Click an agent card
2. Verify details and capabilities display

---

## PHASE 8: INTELLIGENCE

### Test 8.1: Intelligence Dashboard

1. Navigate to `/intelligence`
2. Verify charts/insights display

---

## PHASE 9: DISCo

### Test 9.1: DISCo Page Load

1. Navigate to `/disco`
2. Verify interface displays

---

## PHASE 10: MEETING ROOMS

### Test 10.1: Meeting Rooms Interface

1. Navigate to `/chat`
2. Find "Meeting Rooms" tab
3. Verify interface accessible

---

## PHASE 11: ADMIN HELP

### Test 11.1: Help Panel

1. Find Admin Help panel (right side)
2. Verify help options display

### Test 11.2: Help Question

1. Ask: "How do I create a new task?"
2. Verify helpful response

---

## PHASE 12: CLEANUP

### Cleanup 12.1: Delete Test Conversations

1. Navigate to `/chat`
2. Delete all conversations containing "E2E" in title

### Cleanup 12.2: Delete Test Tasks

1. Navigate to `/tasks`
2. Delete all tasks containing "E2E Test"

### Cleanup 12.3: Delete Test Projects

1. Navigate to `/projects`
2. Delete all projects containing "E2E Test"

---

## --full Mode Summary

```
============================================
COMPREHENSIVE E2E TEST SUMMARY
============================================
Date: [CURRENT_DATE]
Environment: Production (thesis-mvp.vercel.app)
============================================

PHASE 1: Authentication & Navigation
- Test 1.1 Verify Auth:           [PASS/FAIL]
- Test 1.2 Navigation:            [PASS/FAIL]

PHASE 2: Dashboard
- Test 2.1 Dashboard Load:        [PASS/FAIL]

PHASE 3: Chat & AI Agents
- Test 3.1 New Chat:              [PASS/FAIL]
- Test 3.2 Send/Receive Message:  [PASS/FAIL]
- Test 3.3 KB Context Chat:       [PASS/FAIL] [CRITICAL]
- Test 3.4 Agent Selection:       [PASS/FAIL]
- Test 3.5 Chat Actions:          [PASS/FAIL]

PHASE 4: Tasks (Kanban)
- Test 4.1 View Tasks Board:      [PASS/FAIL]
- Test 4.2 Create New Task:       [PASS/FAIL]
- Test 4.3 Drag Task:             [PASS/FAIL]
- Test 4.4 Task Details Modal:    [PASS/FAIL]

PHASE 5: Projects
- Test 5.1 View Projects:         [PASS/FAIL]
- Test 5.2 Create New Project:    [PASS/FAIL]
- Test 5.3 Pipeline View:         [PASS/FAIL]

PHASE 6: Knowledge Base
- Test 6.1 KB Page Load:          [PASS/FAIL]
- Test 6.2 KB Search:             [PASS/FAIL]
- Test 6.3 Document Preview:      [PASS/FAIL]
- Test 6.4 Tag Filtering:         [PASS/FAIL]

PHASE 7: Agents
- Test 7.1 Agents Directory:      [PASS/FAIL]
- Test 7.2 Agent Details:         [PASS/FAIL]

PHASE 8: Intelligence
- Test 8.1 Intelligence Dashboard: [PASS/FAIL]

PHASE 9: DISCo
- Test 9.1 DISCo Page:            [PASS/FAIL]

PHASE 10: Meeting Rooms
- Test 10.1 Meeting Rooms:        [PASS/FAIL]

PHASE 11: Admin Help
- Test 11.1 Help Panel:           [PASS/FAIL]
- Test 11.2 Help Question:        [PASS/FAIL]

PHASE 12: Cleanup
- Cleanup 12.1 Conversations:     [DONE/PARTIAL]
- Cleanup 12.2 Tasks:             [DONE/PARTIAL]
- Cleanup 12.3 Projects:          [DONE/PARTIAL]

--------------------------------------------
TOTALS:  XX/28 tests passed
         XX/28 tests failed
         X items cleaned up
============================================

KB Context Chat Details:
- Documents found: [COUNT]
- Documents cited in response: [LIST]
- Response quality: [GOOD/NEEDS_IMPROVEMENT]
============================================
```

---

# Failure Remediation Plan

When tests fail, create a detailed improvement plan.

## Step 1: Document Each Failure

| Field | Description |
|-------|-------------|
| **Test Name** | Full test path |
| **Stage** | Which stage/phase |
| **Error Type** | Exception or failure type |
| **Error Message** | Full error/traceback |
| **Root Cause** | Analysis of why it failed |
| **Proposed Fix** | Specific changes needed |
| **Files Affected** | Which files need modification |

## Step 2: Create Improvement Plan

```
============================================
FAILURE REMEDIATION PLAN
============================================

FAILURE 1: [Test Name]
-----------------------
Stage: [Stage/Phase]
Error: [Brief description]

Root Cause Analysis:
[Why the test failed]

Proposed Fix:
[Specific changes needed]

Files to Modify:
- [file1]: [what to change]

============================================
```

## Step 3: Generate Follow-Up Prompt

Create a ready-to-use prompt for a new Claude Code session:

````markdown
## Fix Test Failures from /test Run

### Context
The `/test` command was run on [DATE] and the following tests failed.
Working directory: `/Users/charlie.fuller/vaults/Contentful/GitHub/thesis`

### Failed Tests

#### Failure 1: `[FULL_TEST_PATH]`

**Error:**
```
[PASTE FULL ERROR/TRACEBACK]
```

**Root Cause:** [EXPLANATION]
**Proposed Fix:** [SPECIFIC CHANGES]

### Instructions
1. Read failing test file
2. Read source files being tested
3. Implement fixes
4. Re-run specific tests to verify
5. Run full suite with `/test`
6. Commit fixes
````

---

# Troubleshooting

## Pytest Issues

### "Invalid URL" Supabase Errors
**Cause:** `.env` is encrypted. Always run with `dotenvx run`.

### Lazy Supabase Initialization
Some modules need lazy `_get_db()` pattern instead of import-time initialization.

### Test Isolation Issues
Tests pass individually but fail together - module state pollution. Use `pytest-forked` or reset fixtures.

## E2E Issues

### Chrome Not Connected
- Ensure Chrome is open
- Run `mcp__chrome-devtools__list_pages` to verify

### Element Not Found
- Always take fresh snapshot before interacting
- UIDs change between page loads

### Authentication Issues
- Complete login flow if redirected
- Session may expire - re-login if needed

### Slow Responses
- KB context chat may take 10-15 seconds
- Use `mcp__chrome-devtools__wait_for` for expected content

---

# Test Coverage Reference

| Mode | Tests | Expected |
|------|-------|----------|
| --quick | Unit tests only | ~370 tests |
| default | All pytest + 5 E2E | ~800 tests |
| --full | Production E2E | 28 scenarios |

### E2E Scenario Summary

| Mode | Scenarios | Validates |
|------|-----------|-----------|
| default (basic) | 5 | Auth, Chat, KB Search, Tasks CRUD, Kanban drag |
| --full | 28 | Full app: Auth, Nav, Dashboard, Chat (with KB context), Tasks, Projects, KB, Agents, Intelligence, DISCo, Meeting Rooms, Help |
