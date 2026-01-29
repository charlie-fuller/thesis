# Run Full Test Regimen

Run the complete Thesis test suite unattended, including unit tests, integration tests, and E2E browser tests.

## Usage

```
/test          # Run full regimen (all stages)
/test --quick  # Run core unit tests only
```

## Prerequisites

Tests require proper environment configuration:

1. **dotenvx** - The `.env` file is encrypted. Use `dotenvx run` to decrypt and inject environment variables.
2. **DOTENV_PRIVATE_KEY** - Required for decryption. Found in `backend/.env.keys`.

## Instructions

Execute ALL test stages below in order. Do NOT stop if one stage fails - continue to the next stage and report all results at the end.

### Stage 1: Unit Tests

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

### Stage 2: Integration Tests

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

### Stage 3: Extended Tests

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

### Stage 4: E2E Browser Tests

E2E tests use Chrome DevTools MCP to automate browser interactions. You MUST start the servers and run these tests - do not skip them.

#### Step 4.1: Check Server Status

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "Frontend not running"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "Backend not running"
```

#### Step 4.2: Start Servers (if not running)

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

Wait for both servers to be ready (frontend compiles, backend shows "Uvicorn running").

#### Step 4.3: Verify Chrome DevTools MCP Connection

Use `mcp__chrome-devtools__list_pages` to verify Chrome is connected:
- If pages are listed: Chrome is connected, proceed to tests
- If error or no connection: The user must have Chrome open with DevTools MCP enabled

#### Step 4.4: Run E2E Test Scenarios

Navigate to the app and execute each test scenario using Chrome DevTools MCP tools.

---

**Test 1: Auth Login Success**

*Purpose:* Verify authentication flow works

Steps:
1. `mcp__chrome-devtools__navigate_page` to `http://localhost:3000`
2. `mcp__chrome-devtools__take_snapshot` to check page state
3. If login form visible:
   - `mcp__chrome-devtools__fill` email field
   - `mcp__chrome-devtools__fill` password field
   - `mcp__chrome-devtools__click` login button
   - `mcp__chrome-devtools__wait_for` dashboard or authenticated content
4. If already logged in (user menu visible): PASS

*Expected:* User is authenticated and can access protected routes

---

**Test 2: Chat Send Message**

*Purpose:* Verify chat functionality with AI agents

Steps:
1. `mcp__chrome-devtools__navigate_page` to `http://localhost:3000/chat`
2. `mcp__chrome-devtools__take_snapshot` to get element IDs
3. Find the message input textbox (look for "Type your message" or similar)
4. `mcp__chrome-devtools__fill` with test message: "Hello, this is an E2E test"
5. `mcp__chrome-devtools__click` send button (or `mcp__chrome-devtools__press_key` Enter)
6. `mcp__chrome-devtools__wait_for` response from agent (look for new message bubble)

*Expected:* Message appears in chat, AI agent responds

---

**Test 3: KB Search** (optional - depends on UI)

*Purpose:* Verify knowledge base search

Steps:
1. `mcp__chrome-devtools__navigate_page` to `http://localhost:3000/kb`
2. `mcp__chrome-devtools__take_snapshot` to find search input
3. If search input exists:
   - `mcp__chrome-devtools__fill` search field with test query
   - `mcp__chrome-devtools__press_key` Enter or click search
   - Verify results appear
4. If no search UI: Skip this test

*Expected:* Search returns relevant KB documents

---

**Test 4: Tasks Create**

*Purpose:* Verify task creation in Kanban board

Steps:
1. `mcp__chrome-devtools__navigate_page` to `http://localhost:3000/tasks`
2. `mcp__chrome-devtools__take_snapshot` to get element IDs
3. Note the current "To Do" count
4. `mcp__chrome-devtools__click` "Add Task" button
5. `mcp__chrome-devtools__take_snapshot` to get modal element IDs
6. `mcp__chrome-devtools__fill` title field with "E2E Test Task - Automated"
7. `mcp__chrome-devtools__click` "Create" button
8. `mcp__chrome-devtools__wait_for` "E2E Test Task - Automated" to appear on page
9. Verify To Do count increased by 1

*Expected:* New task appears in To Do column

---

**Test 5: Tasks Kanban Drag**

*Purpose:* Verify drag-and-drop status changes

Steps:
1. Ensure on `/tasks` page with the test task visible
2. `mcp__chrome-devtools__take_snapshot` to get task card and column element IDs
3. Find the "E2E Test Task - Automated" heading element (from Test 4)
4. Find the "In Progress" column heading element
5. `mcp__chrome-devtools__drag` from task element to In Progress column
6. `mcp__chrome-devtools__click` Refresh button
7. `mcp__chrome-devtools__take_snapshot` to verify:
   - Task appears in In Progress column
   - To Do count decreased
   - In Progress count increased

*Expected:* Task moves to In Progress, counts update correctly

---

#### Step 4.5: Record E2E Results

Record pass/fail for each scenario:
- Auth Login Success: PASS/FAIL
- Chat Send Message: PASS/FAIL
- KB Search: PASS/FAIL/SKIPPED
- Tasks Create: PASS/FAIL
- Tasks Kanban Drag: PASS/FAIL

#### Troubleshooting E2E Tests

**Chrome not connected:**
- Ensure Chrome browser is open
- Chrome DevTools MCP server must be running and configured in Claude Code settings
- Try `mcp__chrome-devtools__list_pages` to diagnose

**Server startup issues:**
- Check port conflicts: `lsof -i :3000` and `lsof -i :8000`
- Kill existing processes if needed: `kill -9 <PID>`
- Frontend may use alternate port (3001) if 3000 is occupied

**Element not found:**
- Always use `mcp__chrome-devtools__take_snapshot` before interacting
- Element UIDs change between page loads - get fresh snapshot
- Wait for page to fully load before taking snapshot

**Authentication issues:**
- If redirected to login, complete auth flow first
- Session persists in browser - may already be logged in

## Final Summary

After ALL stages complete, provide a summary table:

```
============================================
TEST SUMMARY
============================================
Stage 1 - Unit Tests:        XX passed, XX failed, XX skipped
Stage 2 - Integration Tests: XX passed, XX failed, XX skipped
Stage 3 - Extended Tests:    XX passed, XX failed, XX skipped
Stage 4 - E2E Browser Tests: XX passed, XX failed (or SKIPPED - servers not running)
--------------------------------------------
TOTAL:                       XXX passed, XXX failed, XXX skipped
============================================
```

If any tests failed, list the failed test names and suggest fixes.

## Test Coverage Reference

| Stage | Test Files | Expected Count |
|-------|------------|----------------|
| Unit | 7 core test files | ~370 tests |
| Integration | test_integration.py, test_obsidian_sync.py | ~90 tests |
| Extended | Remaining test_*.py files | ~345 tests |
| E2E | Chrome DevTools MCP scenarios | 5 core scenarios |

### E2E Test Scenarios

| Scenario | Page | Validates |
|----------|------|-----------|
| Auth Login Success | / | Authentication, session management |
| Chat Send Message | /chat | AI agent communication, real-time updates |
| KB Search | /kb | Document search (optional) |
| Tasks Create | /tasks | CRUD operations, form submission |
| Tasks Kanban Drag | /tasks | Drag-drop, status persistence |

## Known Issues & Fixes

### 1. "Invalid URL" Supabase Errors

**Symptom:** Tests fail with `SupabaseException: Invalid URL`

**Cause:** The `.env` file is encrypted with dotenvx. Running pytest directly loads encrypted values.

**Fix:** Always run tests with `dotenvx run`:
```bash
DOTENV_PRIVATE_KEY=... dotenvx run -f .env -- .venv/bin/python -m pytest ...
```

### 2. Lazy Supabase Initialization

**Symptom:** Import-time errors when modules call `get_supabase()` at module level.

**Fixed Files:**
- `services/useable_output_detector.py` - Changed to lazy `_get_db()` initialization
- `services/obsidian_sync.py` - Changed to lazy `_get_db()` initialization

**Pattern for fixing:**
```python
# BAD - initialized at import time
supabase = get_supabase()

# GOOD - lazy initialization
_supabase = None
def _get_db():
    global _supabase
    if _supabase is None:
        _supabase = get_supabase()
    return _supabase
```

### 3. Test Isolation Issues

**Symptom:** Tests pass individually but fail when run together.

**Cause:** Module-level state pollution between tests.

**Fix:** Use `pytest-forked` marker or run problematic tests in isolation.

### 4. Terminology Rename (opportunity -> project)

The codebase was renamed from "opportunity" to "project" terminology. All test files have been updated:
- `test_opportunities.py` -> `test_projects.py`
- `test_opportunity_modal.py` -> `test_project_modal.py`
- All internal references updated to use `project` terminology

### 5. Topic Detection Keyword Conflicts

**Fixed:** The `detect_help_topic` function had "project" in both `tasks` and `projects` keyword lists. Fixed by removing "project" from `tasks` keywords since "project" is now the primary entity name.

## Quick Test Commands

```bash
# Quick unit test (recommended for development)
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/test_projects.py -v --tb=short

# Run specific test class
dotenvx run -f .env -- .venv/bin/python -m pytest tests/test_agents_new.py::TestManualHelpTopicDetection -v

# Run with keyword filter
dotenvx run -f .env -- .venv/bin/python -m pytest tests/ -k "project" -v
```
