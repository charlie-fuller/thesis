# Thesis Testing Plan

> **Last Updated**: January 18, 2026
> **Test Coverage**: 445+ tests across 9 test files
> **Quality Score**: 9.3/10

## Quick Start

```bash
cd /Users/charlie.fuller/vaults/Contentful/thesis/backend

# Run all unit tests (fast, ~1 second, mocked dependencies)
uv run pytest tests/test_document_classifier.py tests/test_tasks.py \
  tests/test_opportunities.py tests/test_engagement.py tests/test_agents_new.py \
  tests/test_vibe_coding_bugs.py tests/test_rigorous.py -v

# Run integration tests (hits real database, ~70 seconds)
uv run pytest tests/test_integration.py -v

# Run Obsidian sync tests (requires backend context)
uv run pytest tests/test_obsidian_sync.py -v

# Run specific test file
uv run pytest tests/test_opportunities.py -v

# Run with coverage report
uv run pytest tests/ --cov=. --cov-report=html
```

## Test Files Overview

| File | Tests | Coverage Area | Runtime | Status |
|------|-------|---------------|---------|--------|
| test_document_classifier.py | 38 | Document auto-classification | <1s | PASS |
| test_tasks.py | 34 | Kanban task management | <1s | PASS |
| test_opportunities.py | 102 | AI opportunity pipeline + detail modal | <1s | PASS |
| test_engagement.py | 36 | Stakeholder engagement analytics | <1s | PASS |
| test_agents_new.py | 55 | Glean Evaluator + Compass + Manual agents | <1s | PASS |
| test_obsidian_sync.py | 45+ | Obsidian vault sync | <1s | PASS (3 known issues) |
| test_vibe_coding_bugs.py | 34 | Common vibe-coding bug patterns | <1s | PASS |
| test_rigorous.py | 65 | Contract, boundary, recovery, load tests | <1s | PASS |
| **test_integration.py** | **35** | **Real database + API tests** | **~70s** | **PASS** |

## Test Types

### Unit Tests (409+ tests, <1 second)
All tests except `test_integration.py` are **unit tests** with mocked dependencies:
- Use `MagicMock` for Supabase, Anthropic, Voyage AI
- Test business logic in isolation
- Fast feedback during development
- No real API calls or database connections

### Integration Tests (35 tests, ~70 seconds)
`test_integration.py` hits the **real backend**:
- Uses FastAPI TestClient with actual routes
- Connects to real Supabase database
- Creates/updates/deletes real data (with cleanup)
- Tests authentication, API contracts, concurrent access
- Requires `.env` file with real credentials

## Test Architecture

### Isolation Pattern

For tests that need to avoid the import chain (llama_index dependency), use this pattern:

```python
import sys
from unittest.mock import MagicMock

# Mock problematic modules BEFORE importing
sys.modules['services'] = MagicMock()
sys.modules['services.sync_scheduler'] = MagicMock()

# Now import the specific module you need
from services.document_classifier import classify_document
```

### Test Categories

Each test file follows this structure:

1. **Unit Tests** - Test individual functions in isolation
2. **Integration Tests** - Test function interactions
3. **Edge Cases** - Boundary conditions and error handling
4. **Validation Tests** - Pydantic model validation

## Feature Test Coverage

### Document Auto-Classification (38 tests)
- Keyword scoring for each agent domain
- Score normalization and thresholds
- LLM fallback for ambiguous cases
- Review flag determination
- Database storage operations

### Task Management (34 tests)
- Task CRUD operations
- Kanban status transitions
- Position management (drag-and-drop)
- Comment system
- Transcript extraction
- Filtering and search

### Opportunities Pipeline (102 tests)
- Tier-based scoring (4 dimensions)
- Status progression workflow
- Stakeholder linkage
- Operator context injection
- API response formats
- **Detail Modal - Related Documents** (7 tests)
  - Document structure validation
  - Relevance score sorting
  - Limit and min_similarity filtering
  - Empty opportunity handling
- **Detail Modal - Q&A Chat** (4 tests)
  - Response with sources
  - Question validation (length, empty)
  - Source document linking
- **Detail Modal - Conversations** (4 tests)
  - Conversation structure
  - Date ordering (newest first)
  - Pagination (limit/offset)
- **Score Justification** (4 tests)
  - Level descriptions for all dimensions
  - Tier explanations
  - Color coding logic
- **API Endpoints** (6 tests)
  - Path patterns for /related-documents, /conversations, /ask
  - Default parameter validation

### Engagement Analytics (36 tests)
- Signal aggregation
- Level hierarchy (champion -> blocker)
- Promotion/demotion rules
- Sticky level behavior
- Batch calculations

### Agent Tests (55 tests)
- Glean Evaluator: connector queries, platform fit assessment
- Compass: win capture, stakeholder context, handoff routing
- Memory save decisions
- Process integration

### Obsidian Vault Sync (45+ tests)
- Frontmatter parsing
- Wikilink conversion
- File hash computation
- Pattern matching
- Vault scanning
- Sync state management
- Watcher configuration

### Vibe-Coding Bug Patterns (34 tests)
These tests target common failure modes in AI-assisted codebases:

**Array/List Edge Cases** (6 tests)
- Empty tier handling (returns `[]` not `null`)
- Single-item pagination
- Empty array serialization
- Pagination beyond data bounds
- Negative offset handling
- Nullable array fields (`tags: null` vs `tags: []`)

**Type Coercion Bugs** (7 tests)
- UUID string vs object equality
- String-to-int score conversion
- Boolean query param variations (`true`, `1`, `True`)
- Tier number vs string handling
- Null vs empty string in optional fields
- ISO date string parsing variants
- Float score rounding

**Async Race Conditions** (3 tests)
- Double-submit protection
- Concurrent status updates (last-writer-wins)
- Read-during-write consistency

**Error Message Propagation** (4 tests)
- Validation errors include field name
- Not-found errors specify resource type
- Duplicate errors are user-friendly
- Permission errors don't leak existence

**Default Value Consistency** (5 tests)
- Opportunity default status (`identified`)
- Tier calculation from null scores (tier 4)
- Task default status (`backlog`)
- Document default visibility (`private`)
- Stakeholder default engagement (`unknown`)

**Permission/Isolation** (3 tests)
- User can only see own opportunities
- Document visibility in search results
- Agent assignment ownership check

**UI State Sync Expectations** (4 tests)
- Create returns complete object with generated fields
- Update returns updated object (not just success)
- Delete returns deleted ID for state removal
- List endpoints return consistent shape when empty

**Full Flow Integration** (2 tests)
- Opportunity create-to-display flow
- Filter-then-detail data consistency

### Rigorous Testing Suite (65 tests)
Production reliability tests for edge cases:

**Contract Tests - Frontend/Backend** (7 tests)
- OpportunityResponse has all frontend fields
- Nullable fields correctly nullable
- RelatedDocument, Conversation, TierResponse shapes

**Boundary Tests** (16 tests)
- Tier calculation at exact boundaries (10→11, 13→14, 16→17)
- Score dimension min/max (1-5)
- Null score handling
- Pagination boundaries (page 0, negative)

**Error Recovery** (8 tests)
- Missing optional field defaults
- Invalid status/tier fallbacks
- Empty array on query failure
- JSON parse failure handling
- Partial update preservation

**Time-Based Tests** (7 tests)
- UTC timestamp verification
- ISO format parsing variants (Z, offset, milliseconds)
- Conversation ordering by created_at
- Stable ordering for same timestamps

**Load Pattern Tests** (6 tests)
- Large list pagination (1000 items)
- Large text fields (10KB)
- Deep nested objects
- Concurrent read/write

**Database Constraint Tests** (5 tests)
- Opportunity code format validation
- Status enum enforcement
- Tier range (1-4)
- Score range (1-5 or null)
- UUID format validation

**Snapshot/Golden Tests** (4 tests)
- Response key stability
- Error response structure
- Success message structure

**Pydantic Validation** (5 tests)
- Required field enforcement
- Optional field handling
- Custom validator rejection
- Type coercion behavior

**Combined Scenarios** (3 tests)
- Full create flow with calculations
- Filter then paginate
- Score update tier recalculation

## Known Issues

### Import Chain Problem

**Issue**: `services/__init__.py` imports `sync_scheduler` which imports `google_drive_sync` which requires `llama_index` (Python 3.10+ only).

**Fix Applied**: Modified `services/__init__.py` to use lazy imports:

```python
def start_scheduler():
    from .sync_scheduler import start_scheduler as _start
    return _start()
```

**Workaround for tests**: Use isolation pattern above or run from backend directory.

### Python Version

Local dev runs Python 3.9.6 (past EOL). Some features require Python 3.10+:
- llama_index
- Some google-auth features

**Recommendation**: Upgrade to Python 3.11 or 3.12

## Code Quality Checks

Run these checks before committing:

```bash
# Ruff linting (if available)
uv run ruff check . --select=E,F,W,B

# Custom quality scan
uv run python -c "
import re
from pathlib import Path

# Check core production code only
for py_file in Path('api').rglob('*.py'):
    content = py_file.read_text()
    # Check for bare except
    if re.search(r'except\s*:', content):
        print(f'BARE_EXCEPT: {py_file}')
    # Check for print statements
    if re.search(r'\bprint\s*\(', content):
        print(f'PRINT: {py_file}')
"
```

### Quality Targets

| Metric | Target | Current |
|--------|--------|---------|
| Code Quality Score | 9.0/10 | 9.3/10 |
| Test Pass Rate | 100% | 100% |
| Bare except blocks | 0 | 0 |
| Print statements (prod) | 0 | 2 (docs only) |

## Adding New Tests

### Template for New Feature Tests

```python
"""
Tests for [Feature Name]

Tests cover:
- [Area 1]
- [Area 2]
- [Area 3]
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Use isolation pattern if needed
import sys
sys.modules['problematic_module'] = MagicMock()


class TestFeatureUnit:
    """Unit tests for [feature]."""

    def test_basic_functionality(self):
        """Test basic operation."""
        pass

    def test_edge_case(self):
        """Test boundary condition."""
        pass


class TestFeatureValidation:
    """Validation tests for [feature]."""

    def test_valid_input_passes(self):
        """Test valid input is accepted."""
        pass

    def test_invalid_input_fails(self):
        """Test invalid input is rejected."""
        pass


class TestFeatureIntegration:
    """Integration tests for [feature]."""

    def test_end_to_end_flow(self):
        """Test complete workflow."""
        pass
```

### Naming Conventions

- Test files: `test_<feature>.py`
- Test classes: `Test<Component><Type>` (e.g., `TestTaskValidation`)
- Test methods: `test_<what>_<condition>` (e.g., `test_create_task_with_null_tags`)

## Testing Workflow

### Before Each PR

1. Run full test suite
2. Check code quality
3. Verify no new print statements
4. Ensure all new code has tests

### Weekly Review

1. Run coverage report
2. Identify untested code paths
3. Update this document with new tests
4. Review and fix flaky tests

## Test Data Patterns

### Mock Supabase Client

```python
mock_supabase = MagicMock()
mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
    data=[{"id": "test-id", "field": "value"}]
)

with patch("module.supabase", mock_supabase):
    result = function_under_test()
```

### Mock Anthropic Client

```python
mock_response = MagicMock()
mock_response.content = [MagicMock(text='{"agents": ["atlas"], "confidence": 0.9}')]

mock_client = MagicMock()
mock_client.messages.create.return_value = mock_response

with patch("module.anthropic_client", mock_client):
    result = function_under_test()
```

## Integration Tests (test_integration.py)

These tests hit the real backend with actual database connections. They require:
- Real Supabase credentials in `.env`
- At least one user in the `users` table

### Coverage Areas (35 tests)

**Health & Connectivity (3 tests)**
- Root endpoint status
- Health endpoint with DB connection verification
- CORS preflight handling

**Agent API (3 tests)**
- List agents (authenticated and unauthenticated)
- Get agent by ID

**Task API (10 tests)**
- List tasks (authenticated and unauthenticated)
- Create task with validation
- Get task by ID and not-found handling
- Update task and status
- Delete task
- Kanban board view

**Opportunity API (5 tests)**
- List opportunities
- Create with required fields (opportunity_code, title)
- Get/update by ID
- Tier calculation verification

**Other Endpoints (4 tests)**
- Stakeholders list
- Documents list
- User documents
- Conversations list

**Database Integrity (4 tests)**
- Task status enum constraint
- Task priority range (1-5)
- Opportunity score range (1-5)
- UUID validation

**Concurrent Access (1 test)**
- Concurrent task creation without collision

**Performance (2 tests)**
- List tasks < 5 seconds
- List opportunities < 5 seconds

**Error Handling (3 tests)**
- 404/500 response format
- 401 without authentication
- 422 validation error format

### Running Integration Tests

```bash
# Run integration tests only
uv run pytest tests/test_integration.py -v

# Skip slow tests
uv run pytest tests/test_integration.py -v -m "not slow"

# Run specific test class
uv run pytest tests/test_integration.py::TestTaskEndpoints -v
```

## Continuous Improvement

### Areas to Expand

1. **Meeting Room Tests** - Multi-agent orchestration
2. **Graph Service Tests** - Neo4j query validation
3. **Streaming Tests** - SSE event testing
4. **Chat API Tests** - Agent routing, Dig Deeper

### Recent Additions (January 2026)

- **Integration tests (35)** - Real database + API tests with ~70s runtime
- Document classifier tests (38)
- Task management tests (34)
- Opportunities pipeline tests (64 -> 102)
  - Added detail modal tests (38 new tests)
  - Related documents retrieval
  - Q&A chat functionality
  - Conversation history
  - Score justification display
- Engagement calculator tests (36)
- Glean Evaluator agent tests (27)
- Compass agent tests (28)
- Obsidian sync expansion (18)
- Vibe-coding bug tests (34)
- Rigorous testing suite (65)

### Next Priority

1. Meeting room orchestration tests
2. Research scheduler tests
3. Graph sync tests
4. Webhook/callback tests

## Troubleshooting

### "No module named 'services'"

Run tests from the backend directory:
```bash
cd /Users/charlie.fuller/vaults/Contentful/thesis/backend
uv run pytest tests/test_file.py -v
```

### "No module named 'llama_index'"

Use isolation pattern or skip tests that require llama_index on Python 3.9.

### Slow Tests

Use pytest markers to skip slow tests:
```bash
uv run pytest tests/ -v -m "not slow"
```

### Flaky Tests

If a test fails intermittently:
1. Check for async timing issues
2. Verify mock setup is complete
3. Look for shared state between tests

---

## Change Log

| Date | Changes |
|------|---------|
| 2026-01-18 | **Added integration tests (35 tests, ~70s runtime)** |
| | - Real database tests with FastAPI TestClient |
| | - Health, Agent, Task, Opportunity, Stakeholder, Document APIs |
| | - Database integrity and constraint validation |
| | - Concurrent access testing |
| | - Performance benchmarks (<5s for list operations) |
| | - Error handling format verification |
| 2026-01-18 | Added rigorous testing suite (65 new tests) |
| | - Contract tests for frontend/backend alignment |
| | - Boundary tests for tier calculations |
| | - Error recovery and graceful degradation |
| | - Time-based edge cases |
| | - Load pattern tests |
| | - Database constraint validation |
| | - Pydantic validation behavior |
| 2026-01-18 | Added vibe-coding bug tests (34 new tests) |
| | - Array/list edge cases (6 tests) |
| | - Type coercion bugs (7 tests) |
| | - Async race conditions (3 tests) |
| | - Error message propagation (4 tests) |
| | - Default value consistency (5 tests) |
| | - Permission/isolation bugs (3 tests) |
| | - UI state sync expectations (4 tests) |
| | - Full flow integration (2 tests) |
| 2026-01-18 | Added opportunity detail modal tests (38 new tests) |
| | - Related documents retrieval and validation |
| | - Q&A chat functionality |
| | - Conversation history with pagination |
| | - Score justification display logic |
| | - API endpoint path validation |
| 2026-01-16 | Initial plan created with 272+ tests |
| | Added isolation pattern documentation |
| | Documented import chain fix |
| | Created test templates |
