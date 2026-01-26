# Thesis Application - Comprehensive Test Plan

> **Version**: 3.0
> **Updated**: January 25, 2026
> **Application**: Multi-agent AI platform (21 agents, Next.js 16 + FastAPI)

---

## Quick Start - Run All Tests

```bash
# Run everything (from repo root)
./scripts/run-all-tests.sh

# Or run individual categories:
./scripts/run-all-tests.sh backend      # Backend tests only
./scripts/run-all-tests.sh frontend     # Frontend tests only
./scripts/run-all-tests.sh security     # Security tests only
./scripts/run-all-tests.sh ai-safety    # AI safety/bias tests
./scripts/run-all-tests.sh it-audit     # IT department audit
```

---

## Test Categories Overview

| Category | Files | Est. Tests | Purpose |
|----------|-------|------------|---------|
| Backend Unit | `tests/test_*.py` | 500+ | Core functionality |
| Backend Integration | `test_integration.py` | 35 | API endpoint tests |
| Contract Tests | `test_contracts.py` | 30 | API contract validation |
| Property-Based | `test_property_based.py` | 40 | Edge case discovery |
| AI Safety | `test_ai_safety_ethics.py` | 35 | Safety guardrails |
| Human-Centered AI | `test_human_centered_ai.py` | 45 | Oversight & consent |
| LLM Bias | `test_llm_bias_mitigation.py` | 50 | Bias detection |
| IT Compliance | `test_it_compliance.py` | 60 | Security controls |
| IT Audit | `test_it_department_audit.py` | 50 | Enterprise concerns |
| Smoke Tests | `test_smoke.py` | 20 | Deployment validation |
| Chaos/Resilience | `test_chaos_resilience.py` | 35 | Failure handling |
| Concurrent Users | `test_concurrent_users.py` | 30 | Race conditions |
| Monitoring | `test_monitoring_alerts.py` | 40 | Observability |
| Database Migrations | `test_database_migrations.py` | 25 | Migration safety |
| Frontend Unit | `__tests__/*.test.tsx` | 30 | React components |
| E2E | `e2e/*.spec.ts` | 50 | User journeys |
| Accessibility | `e2e/accessibility.spec.ts` | 30 | WCAG compliance |
| Visual Regression | `e2e/visual-regression.spec.ts` | 25 | UI consistency |
| **Total** | | **~1,100** | |

---

## Part 1: Backend Tests

### 1.1 Unit Tests
```bash
cd backend
uv run pytest tests/ -v \
  --ignore=tests/test_integration.py \
  --ignore=tests/test_chaos_resilience.py \
  --ignore=tests/test_concurrent_users.py \
  --cov=. --cov-report=html
```

### 1.2 Integration Tests
```bash
cd backend
uv run pytest tests/test_integration.py -v
```

### 1.3 Smoke Tests (Post-Deployment)
```bash
cd backend
uv run pytest tests/test_smoke.py -v -m smoke
```

### 1.4 Contract Tests
```bash
cd backend
uv run pytest tests/test_contracts.py -v
```

### 1.5 Property-Based Tests
```bash
cd backend
uv run pytest tests/test_property_based.py -v
# For CI with more examples:
HYPOTHESIS_PROFILE=ci uv run pytest tests/test_property_based.py -v
```

---

## Part 2: AI Safety & Bias Tests

### 2.1 AI Safety and Ethics
```bash
cd backend
uv run pytest tests/test_ai_safety_ethics.py -v
```

**What it tests:**
- Harmful content refusal
- PII protection
- Prompt injection resistance
- Toxic language prevention
- Professional tone maintenance

### 2.2 Human-Centered AI
```bash
cd backend
uv run pytest tests/test_human_centered_ai.py -v
```

**What it tests:**
- Human oversight capabilities (kill switches)
- Human-in-the-loop workflows
- Informed consent practices
- User control over data
- AI governance accountability

### 2.3 LLM Bias Detection
```bash
cd backend
uv run pytest tests/test_llm_bias_mitigation.py -v
```

**Known Claude biases tested:**
- Sycophancy bias (agreeing too much)
- Recency bias (overweighting recent info)
- Verbosity bias (unnecessarily long responses)
- Positivity bias (sugar-coating negatives)
- Authority bias (inappropriate deference)
- Western-centric bias
- Confidence calibration
- Anchoring bias
- Confirmation bias

---

## Part 3: Security & IT Compliance

### 3.1 Security Tests
```bash
cd backend
uv run pytest tests/test_security.py -v
```

### 3.2 IT Compliance Tests
```bash
cd backend
uv run pytest tests/test_it_compliance.py -v
```

**What it tests:**
- Access control (RBAC)
- Authentication (MFA, session timeout)
- Data protection (encryption, PII masking)
- Audit logging
- Network security (CORS, rate limiting, TLS)
- Disaster recovery

### 3.3 IT Department Audit
```bash
cd backend
uv run pytest tests/test_it_department_audit.py -v

# Generate IT Audit Report:
uv run python -c "from tests.test_it_department_audit import generate_it_audit_report; print(generate_it_audit_report())" > it-audit-report.md
```

**What IT will want to know:**
- Where does data go? (Anthropic, Voyage, Supabase)
- Is SSO supported?
- How are secrets managed?
- What about data residency/GDPR?
- Can we avoid vendor lock-in?
- How do we control costs?
- What's the incident response plan?

---

## Part 4: Resilience & Performance

### 4.1 Chaos/Resilience Tests
```bash
cd backend
uv run pytest tests/test_chaos_resilience.py -v -m chaos
```

**What it tests:**
- Service failure handling
- Network condition handling
- Resource exhaustion
- Dependency outages
- Recovery behavior
- Data consistency under failure

### 4.2 Concurrent User Tests
```bash
cd backend
uv run pytest tests/test_concurrent_users.py -v -m concurrent
```

**What it tests:**
- Race conditions
- Deadlock prevention
- Data integrity under concurrent access
- Session isolation

### 4.3 Load Testing (Locust)
```bash
cd backend
# Normal load
locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m

# Stress test
locust -f locustfile.py --users 200 --spawn-rate 20 --run-time 10m

# Headless mode for CI
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --html report.html
```

---

## Part 5: Database Tests

### 5.1 Migration Safety Tests
```bash
cd backend
uv run pytest tests/test_database_migrations.py -v
```

**What it tests:**
- All migrations reversible
- No data loss on schema changes
- Rollback functionality
- Migration performance on large tables
- Dependency resolution

---

## Part 6: Frontend Tests

### 6.1 Unit Tests
```bash
cd frontend
npm test -- --coverage --watchAll=false
```

### 6.2 E2E Tests (Playwright)
```bash
cd frontend
npx playwright test

# Specific browser
npx playwright test --project=chromium

# With UI
npx playwright test --ui
```

### 6.3 Accessibility Tests
```bash
cd frontend
npx playwright test e2e/accessibility.spec.ts
```

**WCAG 2.1 AA compliance:**
- Color contrast
- Keyboard navigation
- Screen reader support
- Focus management
- ARIA attributes

### 6.4 Visual Regression Tests
```bash
cd frontend
npx playwright test e2e/visual-regression.spec.ts

# Update baselines
npx playwright test --update-snapshots
```

---

## Part 7: Monitoring & Alerts

### 7.1 Monitoring Tests
```bash
cd backend
uv run pytest tests/test_monitoring_alerts.py -v
```

**What it tests:**
- Metrics collection
- Log formatting (JSON, required fields)
- Alert thresholds
- Health check endpoints
- SLO compliance
- Distributed tracing

---

## Part 8: Mutation Testing

Mutation testing verifies test quality by introducing code changes and checking if tests catch them.

```bash
cd backend
pip install mutmut

# Run mutation testing
mutmut run

# View results
mutmut results

# Generate HTML report
mutmut html
```

---

## Part 9: Code Quality

### 9.1 Backend Linting
```bash
cd backend
uv run ruff check . --select=E,F,W,B,I
uv run black --check .
uv run mypy . --ignore-missing-imports
```

### 9.2 Frontend Linting
```bash
cd frontend
npm run lint
npm run build  # TypeScript check
```

### 9.3 Security Scanning
```bash
# Python
cd backend
pip install safety bandit pip-audit
safety check -r requirements.txt
bandit -r . -f json
pip-audit -r requirements.txt

# JavaScript
cd frontend
npm audit
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/test.yml`) runs:

| Job | Trigger | Required |
|-----|---------|----------|
| Backend Unit | Push/PR | Yes |
| Backend Integration | Push/PR | Yes |
| Backend Smoke | Push/PR | Yes |
| Contract Tests | Push/PR | No |
| Property-Based | Push/PR | No |
| Frontend Unit | Push/PR | Yes |
| E2E Tests | Push/PR | Yes |
| Accessibility | Push/PR | No |
| Visual Regression | PR only | No |
| Security Scanning | Push/PR | No |
| AI Safety | Push/PR | No |
| IT Audit | Push/PR | No |
| Load Testing | Manual | No |

---

## Test Reports

After running tests, reports are available at:

| Report | Location |
|--------|----------|
| Backend Coverage | `backend/htmlcov/index.html` |
| Frontend Coverage | `frontend/coverage/lcov-report/index.html` |
| Playwright Report | `frontend/playwright-report/index.html` |
| IT Audit Report | `backend/it-audit-report.md` |
| Locust Report | `backend/locust-report.html` |
| Security Reports | `backend/*.json` |

---

## Coverage Targets

| Area | Target | Current |
|------|--------|---------|
| Backend Unit | 80% | ~75% |
| Frontend Unit | 70% | ~40% |
| E2E Critical Paths | 100% | ~80% |
| API Endpoints | 90% | ~85% |

---

## Adding New Tests

### Backend Test Template
```python
"""
Test module for [feature].
"""
import pytest

class TestFeatureName:
    """Tests for [feature]."""

    def test_happy_path(self):
        """Description of what this tests."""
        # Arrange
        # Act
        # Assert
        pass

    @pytest.mark.parametrize("input,expected", [
        ("a", "A"),
        ("b", "B"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple input/output combinations."""
        assert input.upper() == expected
```

### Frontend Test Template
```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ComponentName } from '@/components/ComponentName'

describe('ComponentName', () => {
  it('renders correctly', () => {
    render(<ComponentName />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    render(<ComponentName />)
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByText('Clicked')).toBeInTheDocument()
  })
})
```

---

## Troubleshooting

### Tests Failing Locally but Passing in CI
- Check environment variables
- Ensure database is accessible
- Clear pytest cache: `rm -rf .pytest_cache`

### Flaky Tests
- Add `@pytest.mark.flaky(reruns=3)` for known flaky tests
- Check for race conditions in async tests
- Increase timeouts for slow operations

### Coverage Not Accurate
- Run with `--cov-branch` for branch coverage
- Exclude test files: `--cov-omit="tests/*"`
