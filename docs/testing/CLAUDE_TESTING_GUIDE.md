# Claude Code Testing Guide

Complete guide for running tests autonomously in the Thesis codebase.

## Quick Start - Run Everything

### 1. Backend Tests (400+ unit tests)

```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend

# With encrypted .env (recommended)
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
./scripts/run_all_tests.sh

# Quick mode - core tests only
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
./scripts/run_all_tests.sh --quick
```

### 2. Individual Test Files

```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend

# Core tests (most reliable)
.venv/bin/python -m pytest tests/test_document_classifier.py -v
.venv/bin/python -m pytest tests/test_tasks.py -v
.venv/bin/python -m pytest tests/test_opportunities.py -v
.venv/bin/python -m pytest tests/test_engagement.py -v
.venv/bin/python -m pytest tests/test_agents_new.py -v

# Obsidian sync tests
.venv/bin/python -m pytest tests/test_obsidian_sync.py -v

# All tests in one command
.venv/bin/python -m pytest tests/test_document_classifier.py \
    tests/test_tasks.py tests/test_opportunities.py \
    tests/test_engagement.py tests/test_agents_new.py \
    tests/test_vibe_coding_bugs.py tests/test_rigorous.py -v
```

---

## E2E Browser Test Execution Guide

### Prerequisites Checklist

Before running E2E tests:

- [ ] Backend running: `localhost:8000`
- [ ] Frontend running: `localhost:3000`
- [ ] Chrome browser open to localhost:3000
- [ ] Test user credentials available

### Starting the Servers

```bash
# Terminal 1: Backend
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
JWK=$(curl -s "https://imdavfgreeddxluslsdl.supabase.co/auth/v1/.well-known/jwks.json" | jq -c '.keys[0]')
SUPABASE_JWT_SECRET="$JWK" \
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/frontend
npm run dev
```

### Chrome DevTools MCP Tool Reference

| Action | MCP Tool | Example |
|--------|----------|---------|
| Navigate | `mcp__chrome-devtools__navigate_page` | `url="http://localhost:3000/chat"` |
| Get elements | `mcp__chrome-devtools__take_snapshot` | Returns element UIDs |
| Fill input | `mcp__chrome-devtools__fill` | `uid="abc123", value="text"` |
| Click | `mcp__chrome-devtools__click` | `uid="abc123"` |
| Wait | `mcp__chrome-devtools__wait_for` | `text="Success"` |
| Check console | `mcp__chrome-devtools__list_console_messages` | Verify no JS errors |
| Check network | `mcp__chrome-devtools__list_network_requests` | Verify API calls |
| Screenshot | `mcp__chrome-devtools__take_screenshot` | Visual verification |
| Drag-drop | `mcp__chrome-devtools__drag` | `from_uid="a", to_uid="b"` |
| Resize | `mcp__chrome-devtools__resize_page` | `width=375, height=667` |

### Test Execution Pattern

For EACH test scenario:

1. **Setup**: Navigate to starting page
2. **Action**: Perform user action (fill, click, drag)
3. **Verify Frontend**: Check UI shows expected state
4. **Verify Backend**: Check network requests succeeded
5. **Verify State**: Confirm data persisted correctly

### Example: Complete Task Creation Test

```
# 1. Navigate to tasks page
mcp__chrome-devtools__navigate_page(url="http://localhost:3000/tasks")

# 2. Take snapshot to get element UIDs
mcp__chrome-devtools__take_snapshot()
# Look for: button with text "New Task" -> uid: "xyz"

# 3. Click new task button
mcp__chrome-devtools__click(uid="xyz")

# 4. Take another snapshot for form fields
mcp__chrome-devtools__take_snapshot()

# 5. Fill title field
mcp__chrome-devtools__fill(uid="title-field-uid", value="Test Task from E2E")

# 6. Click save button
mcp__chrome-devtools__click(uid="save-button-uid")

# 7. Wait for task to appear
mcp__chrome-devtools__wait_for(text="Test Task from E2E")

# 8. Verify no console errors
mcp__chrome-devtools__list_console_messages()

# 9. Verify API call succeeded
mcp__chrome-devtools__list_network_requests()
# Look for: POST /api/tasks with 200/201 status
```

### Validation Test Pattern

For validation tests (empty fields, invalid data):

```
# 1. Navigate to form
mcp__chrome-devtools__navigate_page(url="http://localhost:3000/tasks")

# 2. Click new task
mcp__chrome-devtools__click(uid="new-task-button")

# 3. Try to submit with empty required field
mcp__chrome-devtools__click(uid="submit-button")

# 4. Take snapshot to check for error message
mcp__chrome-devtools__take_snapshot()
# Verify: Error message visible near the field

# 5. Check network - should NOT have made API call
mcp__chrome-devtools__list_network_requests()
# Verify: No POST request made (frontend validation blocked it)
```

### Error Handling Test Pattern

```
# 1. Perform action that triggers API call
mcp__chrome-devtools__click(uid="save-button")

# 2. If API fails, wait for error state
mcp__chrome-devtools__wait_for(text="Error")

# 3. Take snapshot to verify error UI
mcp__chrome-devtools__take_snapshot()
# Verify: Error message visible, retry button available

# 4. Check network for failed request
mcp__chrome-devtools__list_network_requests()
# Look for: 4xx or 5xx status codes
```

---

## Test Scenarios Reference

The full list of 60+ E2E test scenarios is in:
`backend/tests/e2e_browser_tests.py`

### Scenarios by Category

| Category | Count | Key Tests |
|----------|-------|-----------|
| Auth | 8 | Login, logout, session, protected routes |
| Chat | 10 | Send message, @mentions, history, streaming |
| Knowledge Base | 12 | Upload, search, filter, CRUD |
| Tasks | 10 | Kanban, drag-drop, CRUD |
| Opportunities | 12 | Pipeline, scoring, tier calc, CRUD |
| Meeting Rooms | 8 | Create, agents, autonomous mode |
| Performance | 6 | Core Web Vitals, load testing |
| **Total** | **66** | |

### Priority Order for Testing

Run tests in this order for fastest feedback:

1. **Smoke Tests** (auth_login_success, chat_send_message)
2. **Happy Path** (one from each category)
3. **Validation** (form validation tests)
4. **Error Handling** (API error tests)
5. **Edge Cases** (as needed)

---

## Test Result Recording

For each test, record:

| Test ID | Status | Notes |
|---------|--------|-------|
| auth_login_success | PASS/FAIL | Details if failed |
| chat_send_message | PASS/FAIL | Response time noted |
| ... | ... | ... |

### Status Definitions

- **PASS**: All steps completed, all verifications passed
- **FAIL**: Step failed or verification failed (note which)
- **SKIP**: Prerequisites not met (e.g., no test data)
- **BLOCKED**: Infrastructure issue (servers down, etc.)

---

## Test Data Setup

### Required Test Data

- Test user: Create via Supabase or use existing dev account
- Test document: Any PDF file for upload tests
- Clean state: Delete test data between runs if needed

### Cleanup Commands

```sql
-- Delete test tasks
DELETE FROM tasks WHERE title LIKE 'Test%';

-- Delete test opportunities
DELETE FROM opportunities WHERE opportunity_code LIKE 'TEST-%';

-- Delete test documents
DELETE FROM documents WHERE filename LIKE 'test%';

-- Delete test meeting rooms
DELETE FROM meeting_rooms WHERE name LIKE 'Test%';
```

---

## Troubleshooting

### Backend won't start

```bash
# Check if port in use
lsof -i :8000

# Check Python version
python3 --version  # Should be 3.10+

# Check venv
source .venv/bin/activate
pip list | grep fastapi
```

### Frontend won't start

```bash
# Check if port in use
lsof -i :3000

# Check node modules
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Tests fail with import errors

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### Chrome DevTools MCP not connecting

1. Make sure Chrome is running
2. Make sure the page is loaded at localhost:3000
3. Try refreshing the page
4. Check that DevTools is not open (can interfere)

---

## Integration Test Isolation (pytest-forked)

### The Problem: Mock Pollution

When running the full test suite, unit tests that mock modules (like `database`, `auth`, `anthropic`) can pollute the module cache. Integration tests that run later expect real connections but get mocked modules instead, causing failures like:
- 422 errors on authenticated endpoints
- Empty responses from database queries
- Tests pass in isolation but fail in full suite

### The Solution: pytest-forked

The `pytest-forked` plugin runs each test in a separate process, ensuring complete isolation:

```bash
# Install (included in test runner)
uv pip install pytest-forked

# Run integration tests with isolation
.venv/bin/python -m pytest tests/test_integration.py --forked -v
```

### How It Works

1. Each test runs in a fresh Python process
2. All module caches start clean
3. No mock pollution between tests
4. Slightly slower but 100% reliable

### When to Use --forked

| Test Type | Use --forked? | Reason |
|-----------|---------------|--------|
| Integration tests | **Yes** | Need real database/auth connections |
| Unit tests with mocks | No | Isolation not needed, would slow down |
| E2E browser tests | No | Run separately with live servers |

### Automatic Usage

The test runner script (`scripts/run_all_tests.sh`) automatically uses `--forked` for integration tests:

```bash
# This is handled automatically:
pytest tests/test_integration.py tests/test_obsidian_sync.py --forked
```

### Manual Isolation Commands

```bash
# Run integration tests isolated (35 tests, ~2 minutes)
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/test_integration.py --forked -v

# Run specific integration test isolated
.venv/bin/python -m pytest tests/test_integration.py::TestTaskEndpoints -v --forked
```

### Debugging Integration Test Failures

If integration tests fail even with `--forked`:

1. **Check JWT auth**: Tests may skip if using ES256 keys (can't forge tokens)
2. **Check database**: Verify Supabase connection works
3. **Run in isolation**: `pytest tests/test_integration.py -v` (without full suite)
4. **Check environment**: Ensure dotenvx decrypts .env properly

---

## Test Coverage Summary

| Layer | Tests | Coverage |
|-------|-------|----------|
| Backend Unit | 370+ | Business logic, validation |
| Backend Integration | 35+ | Real database operations |
| Backend Obsidian | 55+ | Vault sync functionality |
| E2E Browser | 66 | Full user flows |
| **Total** | **526+** | Full stack |

---

## Commands Cheat Sheet

```bash
# All backend tests
cd backend && ./scripts/run_all_tests.sh

# Quick backend tests
cd backend && ./scripts/run_all_tests.sh --quick

# Specific test file
cd backend && .venv/bin/python -m pytest tests/test_tasks.py -v

# With coverage
cd backend && .venv/bin/python -m pytest tests/ --cov=. --cov-report=html

# E2E test scenarios info
cd backend && .venv/bin/python tests/e2e_browser_tests.py
```
