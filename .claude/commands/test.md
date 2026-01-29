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

E2E tests use Chrome DevTools MCP. Check if servers are running:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "Frontend not running"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "Backend not running"
```

If BOTH servers respond (status 200), run E2E tests using Chrome DevTools MCP tools:

1. Use `mcp__chrome-devtools__list_pages` to verify Chrome is connected
2. Navigate to `http://localhost:3000` using `mcp__chrome-devtools__navigate_page`
3. Execute key E2E scenarios from `tests/e2e_browser_tests.py`:
   - `auth_login_success` - Login flow
   - `chat_send_message` - Chat functionality
   - `kb_search` - Knowledge base search
   - `tasks_create` - Task creation
   - `tasks_kanban_drag` - Kanban drag/drop

If servers are NOT running, skip E2E and note it in the summary.

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
| E2E | e2e_browser_tests.py scenarios | 66 scenarios |

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
