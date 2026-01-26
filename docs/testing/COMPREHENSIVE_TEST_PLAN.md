# Thesis Application - Comprehensive Test Plan & Code Review

> **Version**: 2.0
> **Created**: January 25, 2026
> **Permanent Location**: `/docs/testing/COMPREHENSIVE_TEST_PLAN.md`
> **Purpose**: Production-ready validation plan for full-stack developer review
> **Application**: Multi-agent AI platform (21 agents, Next.js 16 + FastAPI)
> **Current State**: 445+ backend tests, 3 frontend tests, no CI/CD, no e2e tests

---

## Executive Summary

This plan transforms Thesis from a functional prototype to production-grade software through:
1. **Code Review Checklist** - Professional engineering standards validation
2. **Test Coverage Expansion** - 483 tests → 940+ tests target
3. **CI/CD Pipeline** - Automated quality gates
4. **E2E Testing** - Critical user journey validation
5. **Performance & Security Testing** - Production hardening

---

## Part 1: Code Review Checklist

### 1.1 Backend Code Quality (Python/FastAPI)

**Files to Review**: `/backend/api/routes/*.py` (36 files), `/backend/agents/*.py` (21 agents)

| Check | Standard | How to Verify |
|-------|----------|---------------|
| Type hints | All functions typed | `mypy backend/ --strict` |
| No bare `except:` | Specific exceptions only | `grep -r "except\s*:" backend/` |
| No `print()` in prod | Use logger | `grep -r "\bprint\s*(" backend/api/` |
| Async consistency | No blocking I/O in async | Manual review of `await` usage |
| Pydantic models | All API requests/responses | Check each route file |
| Docstrings | All public functions | `pydocstyle backend/` |

**Commands**:
```bash
cd backend
uv run ruff check . --select=E,F,W,B,I
uv run black --check .
uv run mypy . --ignore-missing-imports
```

### 1.2 Frontend Code Quality (TypeScript/React)

**Files to Review**: `/frontend/components/*.tsx` (40+ components), `/frontend/app/**/*.tsx`

| Check | Standard | How to Verify |
|-------|----------|---------------|
| No `any` types | Explicit types always | `grep -r ": any" frontend/` |
| useEffect deps | Complete dependency arrays | ESLint react-hooks/exhaustive-deps |
| Error boundaries | All async operations | Manual review |
| Loading states | All fetch operations | Manual review |
| Key props | All list renders | ESLint |

**Commands**:
```bash
cd frontend
npm run lint
npm run build  # TypeScript check
```

### 1.3 Security Review Checklist

| Area | Check | File(s) |
|------|-------|---------|
| JWT validation | Algorithm pinned (HS256/ES256) | `/backend/auth.py` |
| CORS | Explicit origins, no `*` | `/backend/main.py` |
| Rate limiting | Chat: 20/min, Upload: 10/min | `/backend/api/routes/chat.py` |
| Input validation | UUID validation, length limits | `/backend/validation.py` |
| SQL injection | No string interpolation | All routes using Supabase |
| XSS | No `dangerouslySetInnerHTML` | All React components |
| Secrets | No hardcoded keys | `grep -r "sk-" . --include="*.py"` |

### 1.4 API Contract Review

**Verify for each endpoint**:
- [ ] Request model with validation
- [ ] Response model documented
- [ ] Error responses use standard format
- [ ] OpenAPI docs accurate (`/docs` endpoint)

**Standard Error Format**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {}
  }
}
```

---

## Part 2: Unit Test Expansion

### 2.1 Frontend Tests Needed (Current: 3 → Target: 100+)

**Priority 1 - Core Components** (40 tests):

| Component | File | Tests Needed | Test Cases |
|-----------|------|--------------|------------|
| ChatInterface | `components/ChatInterface.tsx` | 15 | Message send, streaming, agent routing, file attach, error states |
| AgentSelector | `components/AgentSelector.tsx` | 10 | @mention parsing, multi-select, keyboard nav |
| ConversationSidebar | `components/ConversationSidebar.tsx` | 8 | Search, select, delete, archive |
| TaskReviewPanel | `components/TaskReviewPanel.tsx` | 7 | Status change, drag-drop, edit |

**Test File Template** (`frontend/__tests__/ChatInterface.test.tsx`):
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatInterface from '@/components/ChatInterface'

// Mock Supabase
jest.mock('@/lib/supabase', () => ({
  supabase: { from: jest.fn() }
}))

describe('ChatInterface', () => {
  describe('Message Sending', () => {
    it('sends message and displays optimistically', async () => {})
    it('handles streaming responses', async () => {})
    it('prevents double-submit during loading', async () => {})
    it('retries failed messages', async () => {})
  })

  describe('Agent Selection', () => {
    it('routes to @mentioned agent', async () => {})
    it('locks to specific agent when lockedAgentId provided', async () => {})
  })

  describe('Error Handling', () => {
    it('displays user-friendly error on API failure', async () => {})
    it('shows retry button on network error', async () => {})
  })
})
```

**Priority 2 - Feature Components** (35 tests):
- Opportunities: `OpportunityCard`, `PipelineView`, `TierBadge` (15 tests)
- Tasks: `KanbanBoard`, `TaskCard`, `TaskForm` (12 tests)
- DISCo: `InitiativeCard`, `CoverageChart` (8 tests)

**Priority 3 - Contexts & Hooks** (25 tests):
- `AuthContext`: Session management, refresh, logout (10 tests)
- `ThemeContext`: Toggle, persistence (5 tests)
- `useDebounce`, `useAsync`: Edge cases (10 tests)

### 2.2 Backend Tests Needed (Current: 445 → Target: 600)

**Uncovered Services**:

| Service | File | Tests Needed |
|---------|------|--------------|
| Meeting Orchestrator | `services/meeting_orchestrator.py` | 25 |
| Google Drive Sync | `services/google_drive_sync.py` | 20 |
| Granola Scanner | `services/granola_scanner.py` | 15 |
| DISCo Services | `services/disco/*.py` | 40 |
| Graph Services | `services/graph/*.py` | 15 |

**Test File**: `backend/tests/test_meeting_orchestrator.py`
```python
"""Tests for multi-agent meeting orchestration."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

class TestMeetingOrchestrator:
    """Meeting orchestration tests."""

    def test_agent_selection_for_topic(self):
        """Correct agents selected based on topic keywords."""

    def test_turn_taking_respects_priority(self):
        """Agents speak in priority order."""

    def test_autonomous_mode_word_limits(self):
        """Enforce 50-100 word limit per turn."""

    def test_facilitator_redirects_off_topic(self):
        """Facilitator intervenes when discussion drifts."""

    def test_reporter_generates_synthesis(self):
        """Reporter produces unified summary."""
```

---

## Part 3: Integration Testing

### 3.1 API Endpoint Coverage (Current: 35 → Target: 100)

**Priority Endpoints**:

| Endpoint Group | Tests Needed | Focus Areas |
|----------------|--------------|-------------|
| `/api/chat` | 15 | Streaming, RAG context, agent routing |
| `/api/meeting-rooms` | 20 | CRUD, autonomous mode, interjection |
| `/api/disco` | 25 | Full pipeline, stage transitions |
| `/api/documents` | 15 | Upload, chunking, embedding, search |
| `/api/stakeholders` | 10 | CRUD, engagement calculation |

**Test Pattern** (`backend/tests/test_integration_chat.py`):
```python
@pytest.mark.integration
class TestChatEndpoints:
    """Integration tests for chat API."""

    def test_send_message_creates_conversation(self, authenticated_client):
        """First message creates new conversation."""
        response = authenticated_client.post("/api/chat", json={
            "message": "Hello",
            "conversation_id": None
        })
        assert response.status_code == 200
        assert "conversation_id" in response.json()

    def test_agent_routing_with_mention(self, authenticated_client):
        """@atlas routes to Atlas agent."""
        response = authenticated_client.post("/api/chat", json={
            "message": "@atlas What are the trends?",
            "conversation_id": "test-conv"
        })
        assert response.json()["agent"] == "atlas"

    def test_rate_limiting_enforced(self, authenticated_client):
        """Rate limiter returns 429 after threshold."""
        for i in range(25):  # Exceed 20/min limit
            authenticated_client.post("/api/chat", json={"message": f"Test {i}"})

        response = authenticated_client.post("/api/chat", json={"message": "Over limit"})
        assert response.status_code == 429
```

### 3.2 Database Transaction Tests

```python
class TestDatabaseTransactions:
    """Database integrity tests."""

    def test_opportunity_create_rollback_on_failure(self):
        """Failed stakeholder link rolls back opportunity creation."""

    def test_kanban_position_atomic_update(self):
        """Position updates are atomic (no gaps)."""

    def test_document_cascade_delete(self):
        """Deleting document removes chunks and embeddings."""
```

---

## Part 4: End-to-End Testing

### 4.1 Setup: Playwright

**Install**:
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

**Config** (`playwright.config.ts`):
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### 4.2 Critical User Journeys (50 tests)

**Journey 1: Authentication Flow** (8 tests)
```typescript
// e2e/auth.spec.ts
test.describe('Authentication', () => {
  test('login with valid credentials redirects to chat', async ({ page }) => {
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/chat')
  })

  test('invalid credentials shows error', async ({ page }) => {})
  test('password reset flow completes', async ({ page }) => {})
  test('logout clears session', async ({ page }) => {})
})
```

**Journey 2: Chat with Agent** (12 tests)
```typescript
// e2e/chat.spec.ts
test.describe('Agent Chat', () => {
  test('send message and receive streaming response', async ({ page }) => {
    await page.goto('/chat')
    await page.fill('[data-testid="message-input"]', 'What are AI trends?')
    await page.click('[data-testid="send-button"]')

    // Wait for streaming to start
    await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible()

    // Wait for completion
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeHidden({ timeout: 30000 })
  })

  test('@mention routes to specific agent', async ({ page }) => {})
  test('conversation persists on refresh', async ({ page }) => {})
  test('dig deeper expands response', async ({ page }) => {})
})
```

**Journey 3: Meeting Room** (10 tests)
- Create room with agents
- Start autonomous discussion
- User interjection pauses discussion
- Generate synthesis report

**Journey 4: Knowledge Base** (10 tests)
- Upload document
- Document appears in list
- Search returns uploaded document
- Agent cites KB content

**Journey 5: Opportunities Pipeline** (10 tests)
- Create opportunity with scores
- Tier calculated correctly
- Status progression works
- Link stakeholders

### 4.3 Test Data Management

**Seed Script** (`e2e/fixtures/seed.ts`):
```typescript
export async function seedTestData(supabase: SupabaseClient) {
  await supabase.from('clients').insert({
    id: 'e2e-test-client',
    name: 'E2E Test Client'
  })

  await supabase.from('kb_documents').insert([
    { title: 'Test Doc 1', client_id: 'e2e-test-client' },
    { title: 'Test Doc 2', client_id: 'e2e-test-client' }
  ])
}

export async function cleanupTestData(supabase: SupabaseClient) {
  await supabase.from('kb_documents').delete().eq('client_id', 'e2e-test-client')
  await supabase.from('clients').delete().eq('id', 'e2e-test-client')
}
```

---

## Part 5: Agent Testing

### 5.1 Response Quality Validation

**Test File**: `backend/tests/test_agent_quality.py`

```python
"""Agent response quality tests."""
import pytest

class TestAgentResponseQuality:
    """Validate agent outputs meet quality standards."""

    @pytest.mark.parametrize("agent,query,expected_traits", [
        ("atlas", "Gartner AI trends", ["research", "citations"]),
        ("capital", "Calculate ROI", ["numbers", "financial"]),
        ("guardian", "Security risks", ["compliance", "risks"]),
        ("counselor", "IP concerns", ["legal", "liability"]),
        ("sage", "Employee anxiety", ["empathy", "change"]),
    ])
    async def test_agent_domain_relevance(self, agent, query, expected_traits):
        """Agent produces domain-appropriate response."""

    def test_smart_brevity_word_limit(self, agent_response):
        """Response <= 150 words in chat mode."""
        word_count = len(agent_response.split())
        assert word_count <= 200

    def test_no_banned_phrases(self, agent_response):
        """Response avoids phrases like 'Great question!'."""
        banned = ["Great question", "Absolutely", "I'd be happy to"]
        for phrase in banned:
            assert phrase.lower() not in agent_response.lower()
```

### 5.2 Routing Accuracy Tests

```python
class TestAgentRouting:
    """Agent routing decision tests."""

    @pytest.mark.parametrize("query,expected_agent", [
        ("What does McKinsey say?", "atlas"),
        ("Calculate NPV", "capital"),
        ("SOC2 compliance?", "guardian"),
        ("Contract terms?", "counselor"),
        ("Reduce employee fear", "sage"),
        ("Analyze transcript", "oracle"),
        ("RAG architecture?", "architect"),
    ])
    async def test_query_routes_correctly(self, query, expected_agent):
        """Coordinator routes to correct specialist."""
```

### 5.3 Prompt Regression Tests

```python
class TestPromptRegression:
    """Golden response tests to catch prompt regressions."""

    def test_atlas_research_format(self):
        """Atlas response follows expected structure."""

    def test_coordinator_multi_agent_synthesis(self):
        """Coordinator properly synthesizes multi-agent responses."""
```

---

## Part 6: Performance & Load Testing

### 6.1 Setup: Locust

**Install**: `pip install locust`

**Config** (`locustfile.py`):
```python
from locust import HttpUser, task, between

class ThesisUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post("/api/auth/login", json={
            "email": "loadtest@thesis.ai",
            "password": "loadtest-password"
        })
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def list_conversations(self):
        self.client.get("/api/conversations", headers=self.headers)

    @task(5)
    def send_chat(self):
        self.client.post("/api/chat",
            json={"message": "Test", "stream": False},
            headers=self.headers
        )

    @task(3)
    def search_kb(self):
        self.client.get("/api/documents/search?q=test", headers=self.headers)
```

### 6.2 Performance Targets

| Endpoint | P50 | P95 | P99 | Max RPS |
|----------|-----|-----|-----|---------|
| GET /api/conversations | 100ms | 300ms | 500ms | 500 |
| POST /api/chat (non-stream) | 2s | 5s | 10s | 50 |
| GET /api/documents/search | 200ms | 500ms | 1s | 100 |
| POST /api/documents/upload | 3s | 8s | 15s | 20 |

### 6.3 Test Scenarios

```bash
# Normal load (50 users)
locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 10m

# Stress test (200 users)
locust -f locustfile.py --users 200 --spawn-rate 20 --run-time 10m

# Soak test (1 hour)
locust -f locustfile.py --users 30 --spawn-rate 5 --run-time 1h
```

---

## Part 7: Security Testing

### 7.1 Authentication Tests

```python
class TestAuthSecurity:
    """Authentication security tests."""

    def test_missing_auth_returns_401(self, client):
        """Unauthenticated requests rejected."""
        response = client.get("/api/tasks")
        assert response.status_code in [401, 403]

    def test_invalid_jwt_rejected(self, client):
        """Invalid tokens rejected."""
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = client.get("/api/tasks", headers=headers)
        assert response.status_code == 401

    def test_expired_jwt_rejected(self, client, expired_token):
        """Expired tokens rejected."""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/tasks", headers=headers)
        assert response.status_code == 401
```

### 7.2 Authorization Boundary Tests

```python
class TestAuthorizationBoundaries:
    """Authorization isolation tests."""

    def test_user_cannot_access_other_user_data(self, user_a_client, user_b_task):
        """User A cannot access User B's tasks."""
        response = user_a_client.get(f"/api/tasks/{user_b_task['id']}")
        assert response.status_code in [403, 404]

    def test_non_admin_blocked_from_admin_routes(self, regular_client):
        """Regular users cannot access admin endpoints."""
        response = regular_client.get("/api/admin/users")
        assert response.status_code in [401, 403]
```

### 7.3 Input Fuzzing

```python
@pytest.mark.parametrize("malicious", [
    "'; DROP TABLE users; --",
    "<script>alert('xss')</script>",
    "../../../etc/passwd",
    "{{7*7}}",
    "A" * 100000,
])
def test_malicious_input_handled(self, client, auth_headers, malicious):
    """Malicious input doesn't cause 500 errors."""
    response = client.post("/api/chat",
        json={"message": malicious},
        headers=auth_headers
    )
    assert response.status_code in [200, 400, 422]  # Not 500
```

### 7.4 Dependency Scanning

```bash
# Python
pip install safety bandit pip-audit
safety check -r requirements.txt
bandit -r backend/ -f json
pip-audit -r requirements.txt

# JavaScript
cd frontend
npm audit
```

---

## Part 8: CI/CD Pipeline

### 8.1 GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
  SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  SUPABASE_JWT_SECRET: ${{ secrets.SUPABASE_JWT_SECRET }}

jobs:
  backend-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install deps
        working-directory: backend
        run: pip install uv && uv pip install -r requirements.txt -r requirements-dev.txt
      - name: Lint
        working-directory: backend
        run: uv run ruff check . && uv run black --check .
      - name: Unit tests
        working-directory: backend
        run: uv run pytest tests/ -v --ignore=tests/test_integration.py --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v4

  backend-integration:
    runs-on: ubuntu-latest
    needs: backend-unit
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install deps
        working-directory: backend
        run: pip install uv && uv pip install -r requirements.txt
      - name: Integration tests
        working-directory: backend
        run: uv run pytest tests/test_integration.py -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - name: Install deps
        working-directory: frontend
        run: npm ci
      - name: Lint
        working-directory: frontend
        run: npm run lint
      - name: Type check
        working-directory: frontend
        run: npm run build
      - name: Unit tests
        working-directory: frontend
        run: npm test -- --coverage

  e2e:
    runs-on: ubuntu-latest
    needs: [backend-unit, frontend]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run E2E
        run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python security
        run: |
          pip install safety bandit
          safety check -r backend/requirements.txt || true
          bandit -r backend/ -f json || true
      - name: JS security
        working-directory: frontend
        run: npm audit || true
```

---

## Part 9: Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up CI/CD pipeline with existing tests
- [ ] Add 20 frontend component tests (ChatInterface, AgentSelector)
- [ ] Add 25 backend service tests (meeting_orchestrator, chat routes)
- [ ] Configure code coverage reporting

### Phase 2: Critical Paths (Week 3-4)
- [ ] Implement 30 E2E tests for top 5 journeys
- [ ] Add 15 agent routing accuracy tests
- [ ] Add 20 authentication/authorization security tests
- [ ] Document all API contracts

### Phase 3: Quality & Performance (Week 5-6)
- [ ] Add 20 agent response quality tests
- [ ] Implement Locust load testing
- [ ] Add visual regression tests (optional)
- [ ] Run stress tests and document limits

### Phase 4: Hardening (Week 7-8)
- [ ] Add prompt regression (golden) tests
- [ ] Implement input fuzzing
- [ ] Add dependency vulnerability scanning to CI
- [ ] Complete code review checklist

---

## Part 10: Verification Commands

### Run All Tests

```bash
# Backend unit tests
cd backend && uv run pytest tests/ -v --ignore=tests/test_integration.py

# Backend integration tests
cd backend && uv run pytest tests/test_integration.py -v

# Frontend tests
cd frontend && npm test

# E2E tests
cd frontend && npx playwright test

# Load tests
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m
```

### Coverage Report

```bash
# Backend
cd backend && uv run pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend && npm test -- --coverage
```

### Quality Gates

| Gate | Threshold | Command |
|------|-----------|---------|
| Backend unit tests | 100% pass | `pytest tests/ --ignore=test_integration.py` |
| Backend coverage | 80%+ | `pytest --cov --cov-fail-under=80` |
| Frontend lint | 0 errors | `npm run lint` |
| Frontend build | Success | `npm run build` |
| E2E tests | 95%+ pass | `npx playwright test` |

---

## Summary: Test Count Targets

| Category | Current | Target | Gap |
|----------|---------|--------|-----|
| Backend Unit | 445 | 600 | +155 |
| Backend Integration | 35 | 100 | +65 |
| Frontend Unit | 3 | 100 | +97 |
| E2E Tests | 0 | 50 | +50 |
| Agent Quality | 0 | 30 | +30 |
| Performance | 0 | 20 | +20 |
| Security | 0 | 40 | +40 |
| **Total** | **483** | **940** | **+457** |

---

## Critical Files for Implementation

1. `/backend/tests/conftest.py` - Extend fixtures for new test types
2. `/frontend/jest.config.js` - Configure coverage thresholds
3. `/frontend/__tests__/` - Add component test files
4. `/e2e/` - Create Playwright test directory
5. `.github/workflows/test.yml` - CI/CD pipeline
6. `/locustfile.py` - Load testing configuration
