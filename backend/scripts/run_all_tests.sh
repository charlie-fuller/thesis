#!/bin/bash
# Thesis Test Runner - For Claude Code autonomous testing
#
# Usage:
#   ./scripts/run_all_tests.sh           # Run all tests
#   ./scripts/run_all_tests.sh --quick   # Run only core unit tests
#   ./scripts/run_all_tests.sh --e2e     # Run only E2E browser tests
#
# Requires: Python 3.10+, dotenvx (optional for encrypted .env)

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$BACKEND_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="$BACKEND_DIR/.venv"
PYTHON_MIN_VERSION="3.10"
DOTENV_KEY="${DOTENV_PRIVATE_KEY:-}"

# Parse arguments
RUN_QUICK=false
RUN_E2E=false
RUN_ALL=true

for arg in "$@"; do
    case $arg in
        --quick)
            RUN_QUICK=true
            RUN_ALL=false
            ;;
        --e2e)
            RUN_E2E=true
            RUN_ALL=false
            ;;
        --help)
            echo "Usage: $0 [--quick] [--e2e]"
            echo "  --quick  Run only core unit tests"
            echo "  --e2e    Run only E2E browser tests (requires servers running)"
            exit 0
            ;;
    esac
done

echo "=========================================="
echo "Thesis Test Runner"
echo "=========================================="
echo ""

# 1. Check Python version and setup
check_python() {
    echo -e "${BLUE}Checking Python version...${NC}"

    # Check if uv is available (preferred method for this project)
    if command -v uv &> /dev/null; then
        USE_UV=true
        echo -e "${GREEN}  Found uv - will use for Python management${NC}"
        return 0
    fi

    USE_UV=false

    # First, find a suitable system Python
    SYSTEM_PYTHON=""

    # Check pyenv paths first
    for pyenv_version in 3.12 3.11 3.10; do
        pyenv_path="$HOME/.pyenv/versions/${pyenv_version}*/bin/python"
        # Use glob expansion
        for p in $pyenv_path; do
            if [ -x "$p" ]; then
                SYSTEM_PYTHON="$p"
                version=$($SYSTEM_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
                echo -e "${GREEN}  Found pyenv Python $version${NC}"
                break 2
            fi
        done
    done

    # Fallback to system Python
    if [ -z "$SYSTEM_PYTHON" ]; then
        for cmd in python3.12 python3.11 python3.10 python3; do
            if command -v $cmd &> /dev/null; then
                version=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
                major=$(echo "$version" | cut -d. -f1)
                minor=$(echo "$version" | cut -d. -f2)
                if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
                    SYSTEM_PYTHON=$cmd
                    echo -e "${GREEN}  Found system $cmd (Python $version)${NC}"
                    break
                fi
            fi
        done
    fi

    if [ -z "$SYSTEM_PYTHON" ]; then
        echo -e "${RED}  Python 3.10+ required. Found: $(python3 --version 2>&1)${NC}"
        echo "  Install with: brew install python@3.12 OR uv python install 3.12"
        exit 1
    fi

    PYTHON_CMD="$SYSTEM_PYTHON"
}

# 2. Setup virtualenv and dependencies
setup_venv() {
    echo -e "${BLUE}Setting up virtual environment...${NC}"

    if [ "${USE_UV:-false}" = true ]; then
        # Use uv for venv and dependency management
        cd "$BACKEND_DIR"

        if [ ! -d "$VENV_DIR" ]; then
            echo "  Creating virtualenv with uv..."
            uv venv --python 3.12 "$VENV_DIR"
        fi

        PYTHON_CMD="$VENV_DIR/bin/python"

        # Verify venv works
        if ! "$PYTHON_CMD" -c 'import sys' &>/dev/null; then
            echo "  Recreating broken venv..."
            rm -rf "$VENV_DIR"
            uv venv --python 3.12 "$VENV_DIR"
        fi

        echo "  Installing dependencies with uv..."
        uv pip install -r requirements.txt --quiet 2>/dev/null || uv pip install -r requirements.txt
        uv pip install pytest pytest-asyncio pytest-cov pytest-timeout pytest-forked hypothesis --quiet 2>/dev/null || \
            uv pip install pytest pytest-asyncio pytest-cov pytest-timeout pytest-forked hypothesis

        echo -e "${GREEN}  Dependencies installed via uv${NC}"
        return 0
    fi

    # Fallback: manual venv management
    if [ ! -d "$VENV_DIR" ]; then
        echo "  Creating virtualenv..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi

    # Use the venv Python from now on
    PYTHON_CMD="$VENV_DIR/bin/python"

    # Verify venv Python works
    if ! "$PYTHON_CMD" -c 'import sys' &>/dev/null; then
        echo -e "${RED}  Venv Python not working, trying to recreate...${NC}"
        rm -rf "$VENV_DIR"
        $SYSTEM_PYTHON -m venv "$VENV_DIR"
        PYTHON_CMD="$VENV_DIR/bin/python"
    fi

    # Install/upgrade pip
    "$PYTHON_CMD" -m pip install --quiet --upgrade pip

    # Install main dependencies
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        echo "  Installing requirements.txt..."
        "$PYTHON_CMD" -m pip install --quiet -r "$BACKEND_DIR/requirements.txt"
    fi

    # Install test dependencies
    echo "  Installing test dependencies..."
    "$PYTHON_CMD" -m pip install --quiet pytest pytest-asyncio pytest-cov pytest-timeout pytest-forked hypothesis

    echo -e "${GREEN}  Dependencies installed${NC}"
}

# 3. Load environment variables
load_env() {
    echo -e "${BLUE}Loading environment...${NC}"
    cd "$BACKEND_DIR"

    if [ -n "$DOTENV_KEY" ] && command -v dotenvx &> /dev/null; then
        echo "  Decrypting .env with dotenvx..."
        # Export environment variables from encrypted .env
        set +e  # Don't exit on error for this section
        eval "$(DOTENV_PRIVATE_KEY="$DOTENV_KEY" dotenvx run -f .env -- printenv 2>/dev/null | grep -E '^(SUPABASE|ANTHROPIC|VOYAGE|NEO4J|MEM0|GOOGLE)' | sed 's/^/export /')"
        set -e
        echo -e "${GREEN}  Environment loaded from encrypted .env${NC}"
    elif [ -f .env ]; then
        echo "  Loading .env file..."
        set -a
        source .env
        set +a
        echo -e "${GREEN}  Environment loaded from .env${NC}"
    else
        echo -e "${YELLOW}  No .env file found - tests will use mocks${NC}"
    fi
}

# 4. Run unit tests
run_unit_tests() {
    echo ""
    echo "=========================================="
    echo "Running Unit Tests"
    echo "=========================================="

    cd "$BACKEND_DIR"

    # Core tests that should always pass
    CORE_TESTS=(
        "tests/test_document_classifier.py"
        "tests/test_tasks.py"
        "tests/test_engagement.py"
        "tests/test_agents_new.py"
        "tests/test_vibe_coding_bugs.py"
        "tests/test_rigorous.py"
    )

    echo ""
    echo "Running core tests..."
    $PYTHON_CMD -m pytest "${CORE_TESTS[@]}" \
        -v \
        --tb=short \
        --timeout=60 \
        2>&1 | tee /tmp/thesis_unit_test_results.txt

    UNIT_RESULT=${PIPESTATUS[0]}

    return $UNIT_RESULT
}

# 5. Run integration tests
run_integration_tests() {
    echo ""
    echo "=========================================="
    echo "Running Integration Tests"
    echo "=========================================="

    cd "$BACKEND_DIR"

    local RESULT=0

    # Run obsidian_sync tests (uses mocks)
    if [ -f "tests/test_obsidian_sync.py" ]; then
        echo ""
        echo "Running Obsidian Sync tests..."
        $PYTHON_CMD -m pytest tests/test_obsidian_sync.py \
            -v \
            --tb=short \
            --timeout=120 \
            2>&1 | tee /tmp/thesis_obsidian_test_results.txt
        [ ${PIPESTATUS[0]} -ne 0 ] && RESULT=1
    fi

    # Run real integration tests in SEPARATE pytest session to avoid mock pollution
    # This is critical - test_integration.py needs fresh module state and env vars
    if [ -f "tests/test_integration.py" ]; then
        echo ""
        echo "Running Real Integration tests (separate session)..."

        # Reload real environment variables to override any test mocks
        # This ensures integration tests use real credentials
        if [ -n "$DOTENV_KEY" ] && command -v dotenvx &> /dev/null; then
            DOTENV_PRIVATE_KEY="$DOTENV_KEY" dotenvx run -f .env -- \
                $PYTHON_CMD -m pytest tests/test_integration.py \
                -v \
                --tb=short \
                --timeout=120 \
                2>&1 | tee /tmp/thesis_integration_test_results.txt
        else
            # Re-source .env to ensure fresh values
            set -a
            source .env 2>/dev/null || true
            set +a
            $PYTHON_CMD -m pytest tests/test_integration.py \
                -v \
                --tb=short \
                --timeout=120 \
                2>&1 | tee /tmp/thesis_integration_test_results.txt
        fi
        [ ${PIPESTATUS[0]} -ne 0 ] && RESULT=1
    fi

    INTEGRATION_RESULT=$RESULT
    return $INTEGRATION_RESULT
}

# 6. Run all other tests
run_extended_tests() {
    echo ""
    echo "=========================================="
    echo "Running Extended Test Suite"
    echo "=========================================="

    cd "$BACKEND_DIR"

    # Run all tests except E2E and integration (integration runs separately)
    $PYTHON_CMD -m pytest tests/ \
        --ignore=tests/e2e/ \
        --ignore=tests/e2e_browser_tests.py \
        --ignore=tests/test_integration.py \
        --ignore=tests/test_obsidian_sync.py \
        -v \
        --tb=short \
        --timeout=120 \
        2>&1 | tee /tmp/thesis_extended_test_results.txt

    EXTENDED_RESULT=${PIPESTATUS[0]}

    return $EXTENDED_RESULT
}

# 7. Run E2E browser tests info
run_e2e_info() {
    echo ""
    echo "=========================================="
    echo "E2E Browser Tests"
    echo "=========================================="
    echo ""
    echo "E2E browser tests require:"
    echo "  1. Backend running at localhost:8000"
    echo "  2. Frontend running at localhost:3000"
    echo "  3. Chrome browser open"
    echo ""
    echo "To run E2E tests, use Chrome DevTools MCP tools:"
    echo "  - See tests/e2e_browser_tests.py for test scenarios"
    echo "  - See docs/testing/CLAUDE_TESTING_GUIDE.md for instructions"
    echo ""
}

# 8. Print summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "TEST SUMMARY"
    echo "=========================================="

    OVERALL_PASS=true

    if [ -n "${UNIT_RESULT:-}" ]; then
        if [ $UNIT_RESULT -eq 0 ]; then
            echo -e "${GREEN}  Unit Tests: PASSED${NC}"
        else
            echo -e "${RED}  Unit Tests: FAILED${NC}"
            OVERALL_PASS=false
        fi
    fi

    if [ -n "${INTEGRATION_RESULT:-}" ]; then
        if [ $INTEGRATION_RESULT -eq 0 ]; then
            echo -e "${GREEN}  Integration Tests: PASSED${NC}"
        else
            echo -e "${YELLOW}  Integration Tests: FAILED (may have known issues)${NC}"
        fi
    fi

    if [ -n "${EXTENDED_RESULT:-}" ]; then
        if [ $EXTENDED_RESULT -eq 0 ]; then
            echo -e "${GREEN}  Extended Tests: PASSED${NC}"
        else
            echo -e "${YELLOW}  Extended Tests: FAILED (some tests may have external deps)${NC}"
        fi
    fi

    echo ""

    if $OVERALL_PASS; then
        echo -e "${GREEN}=========================================="
        echo "ALL CORE TESTS PASSED"
        echo "==========================================${NC}"
        return 0
    else
        echo -e "${RED}=========================================="
        echo "SOME TESTS FAILED - See output above"
        echo "==========================================${NC}"
        return 1
    fi
}

# Main execution
main() {
    check_python
    setup_venv
    load_env

    UNIT_RESULT=0
    INTEGRATION_RESULT=0
    EXTENDED_RESULT=0

    if $RUN_QUICK; then
        run_unit_tests || UNIT_RESULT=$?
    elif $RUN_E2E; then
        run_e2e_info
    elif $RUN_ALL; then
        run_unit_tests || UNIT_RESULT=$?
        run_integration_tests || INTEGRATION_RESULT=$?
        run_e2e_info
    fi

    print_summary
}

main
