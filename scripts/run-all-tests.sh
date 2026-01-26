#!/bin/bash
#
# Thesis Test Runner
# Run all tests or specific categories
#
# Usage:
#   ./scripts/run-all-tests.sh              # Run all tests
#   ./scripts/run-all-tests.sh backend      # Backend tests only
#   ./scripts/run-all-tests.sh frontend     # Frontend tests only
#   ./scripts/run-all-tests.sh security     # Security tests
#   ./scripts/run-all-tests.sh ai-safety    # AI safety/bias tests
#   ./scripts/run-all-tests.sh it-audit     # IT department audit
#   ./scripts/run-all-tests.sh quick        # Quick smoke tests only
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

# Print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print failure
print_failure() {
    echo -e "${RED}✗ $1${NC}"
}

# Print info
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Run backend unit tests
run_backend_unit() {
    print_header "Backend Unit Tests"
    cd "$REPO_ROOT/backend"
    uv run pytest tests/ -v \
        --ignore=tests/test_integration.py \
        --ignore=tests/test_chaos_resilience.py \
        --ignore=tests/test_concurrent_users.py \
        -m "not slow and not chaos and not concurrent" \
        --tb=short
    print_success "Backend unit tests completed"
}

# Run backend integration tests
run_backend_integration() {
    print_header "Backend Integration Tests"
    cd "$REPO_ROOT/backend"
    uv run pytest tests/test_integration.py -v --tb=short
    print_success "Backend integration tests completed"
}

# Run backend smoke tests
run_backend_smoke() {
    print_header "Backend Smoke Tests"
    cd "$REPO_ROOT/backend"
    uv run pytest tests/test_smoke.py -v -m smoke --tb=short
    print_success "Backend smoke tests completed"
}

# Run contract tests
run_contracts() {
    print_header "API Contract Tests"
    cd "$REPO_ROOT/backend"
    uv run pytest tests/test_contracts.py -v --tb=short
    print_success "Contract tests completed"
}

# Run property-based tests
run_property() {
    print_header "Property-Based Tests"
    cd "$REPO_ROOT/backend"
    uv run pytest tests/test_property_based.py -v --tb=short
    print_success "Property-based tests completed"
}

# Run security tests
run_security() {
    print_header "Security Tests"
    cd "$REPO_ROOT/backend"

    print_info "Running security unit tests..."
    uv run pytest tests/test_security.py -v --tb=short || true

    print_info "Running IT compliance tests..."
    uv run pytest tests/test_it_compliance.py -v --tb=short || true

    print_info "Running bandit security scan..."
    pip install bandit -q 2>/dev/null || true
    bandit -r . -f txt -ll || true

    print_success "Security tests completed"
}

# Run AI safety and bias tests
run_ai_safety() {
    print_header "AI Safety & Bias Tests"
    cd "$REPO_ROOT/backend"

    print_info "Running AI safety tests..."
    uv run pytest tests/test_ai_safety_ethics.py -v --tb=short || true

    print_info "Running human-centered AI tests..."
    uv run pytest tests/test_human_centered_ai.py -v --tb=short || true

    print_info "Running LLM bias tests..."
    uv run pytest tests/test_llm_bias_mitigation.py -v --tb=short || true

    print_success "AI safety tests completed"
}

# Run IT department audit
run_it_audit() {
    print_header "IT Department Audit"
    cd "$REPO_ROOT/backend"

    print_info "Running IT audit tests..."
    uv run pytest tests/test_it_department_audit.py -v --tb=short

    print_info "Generating IT Audit Report..."
    uv run python -c "from tests.test_it_department_audit import generate_it_audit_report; print(generate_it_audit_report())" > it-audit-report.md

    print_success "IT audit completed - report saved to backend/it-audit-report.md"
}

# Run frontend unit tests
run_frontend_unit() {
    print_header "Frontend Unit Tests"
    cd "$REPO_ROOT/frontend"
    npm test -- --coverage --watchAll=false
    print_success "Frontend unit tests completed"
}

# Run E2E tests
run_e2e() {
    print_header "E2E Tests (Playwright)"
    cd "$REPO_ROOT/frontend"
    npx playwright test --project=chromium
    print_success "E2E tests completed"
}

# Run accessibility tests
run_accessibility() {
    print_header "Accessibility Tests"
    cd "$REPO_ROOT/frontend"
    npx playwright test e2e/accessibility.spec.ts --project=chromium || true
    print_success "Accessibility tests completed"
}

# Run all backend tests
run_all_backend() {
    run_backend_unit
    run_backend_integration
    run_backend_smoke
    run_contracts
    run_property
}

# Run all frontend tests
run_all_frontend() {
    run_frontend_unit
    run_e2e
    run_accessibility
}

# Run quick smoke tests only
run_quick() {
    print_header "Quick Smoke Tests"
    cd "$REPO_ROOT/backend"
    uv run pytest tests/test_smoke.py -v -m smoke --tb=line -q
    print_success "Quick smoke tests completed"
}

# Run all tests
run_all() {
    print_header "Running All Tests"

    # Backend
    run_backend_unit
    run_backend_integration
    run_backend_smoke
    run_contracts
    run_property
    run_security
    run_ai_safety

    # Frontend
    run_frontend_unit
    run_e2e
    run_accessibility

    print_header "All Tests Completed!"
}

# Main
case "${1:-all}" in
    backend)
        run_all_backend
        ;;
    frontend)
        run_all_frontend
        ;;
    security)
        run_security
        ;;
    ai-safety|ai|bias)
        run_ai_safety
        ;;
    it-audit|audit)
        run_it_audit
        ;;
    quick|smoke)
        run_quick
        ;;
    unit)
        run_backend_unit
        run_frontend_unit
        ;;
    integration)
        run_backend_integration
        ;;
    e2e)
        run_e2e
        ;;
    contracts)
        run_contracts
        ;;
    property)
        run_property
        ;;
    accessibility|a11y)
        run_accessibility
        ;;
    all)
        run_all
        ;;
    help|--help|-h)
        echo "Usage: $0 [category]"
        echo ""
        echo "Categories:"
        echo "  all          Run all tests (default)"
        echo "  backend      Backend tests only"
        echo "  frontend     Frontend tests only"
        echo "  security     Security tests"
        echo "  ai-safety    AI safety/bias tests"
        echo "  it-audit     IT department audit + report"
        echo "  quick        Quick smoke tests"
        echo "  unit         Unit tests only"
        echo "  integration  Integration tests only"
        echo "  e2e          E2E tests only"
        echo "  contracts    API contract tests"
        echo "  property     Property-based tests"
        echo "  accessibility WCAG accessibility tests"
        echo ""
        ;;
    *)
        echo "Unknown category: $1"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
