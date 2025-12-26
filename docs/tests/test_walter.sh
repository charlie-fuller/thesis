#!/bin/bash

# Walter End-to-End Test Script (using curl)
# Tests backend health, authentication, chat, and image generation

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
TEST_EMAIL="${TEST_EMAIL:-walter-test@example.com}"
TEST_PASSWORD="${TEST_PASSWORD:-WalterTest123!}"

# Test counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_header() {
    echo -e "\n${BOLD}${BLUE}======================================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Test 1: Backend Health Check
test_health() {
    print_header "TEST 1: Backend Health Check"

    response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/health")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "Backend is healthy"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"

        if echo "$body" | grep -q '"database":"connected"'; then
            print_info "Database connection verified"
        else
            print_warning "Database connection unclear"
        fi
    else
        print_error "Health check failed (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

# Test 2: User Authentication
test_auth() {
    print_header "TEST 2: User Authentication"

    # Try signup first (may fail if user exists - that's OK)
    print_info "Attempting to create test user..."

    signup_response=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/auth/signup" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"name\":\"Walter Test User\"}")

    signup_code=$(echo "$signup_response" | tail -n1)

    if [ "$signup_code" = "200" ]; then
        print_info "Test user created successfully"
    elif [ "$signup_code" = "400" ]; then
        print_info "Test user already exists (OK)"
    else
        print_warning "Signup returned HTTP $signup_code"
    fi

    # Now try login
    print_info "Attempting to login..."

    login_response=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

    login_code=$(echo "$login_response" | tail -n1)
    login_body=$(echo "$login_response" | sed '$d')

    if [ "$login_code" = "200" ]; then
        print_success "Login successful"

        # Extract access token
        ACCESS_TOKEN=$(echo "$login_body" | jq -r '.access_token')
        USER_ID=$(echo "$login_body" | jq -r '.user.id')

        print_info "User ID: $USER_ID"
        print_info "Access Token: ${ACCESS_TOKEN:0:20}..."

        return 0
    else
        print_error "Login failed (HTTP $login_code)"
        echo "$login_body"
        return 1
    fi
}

# Test 3: Walter Persona Verification
test_walter_persona() {
    print_header "TEST 3: Walter L&D Persona Verification"

    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "Skipping: Not authenticated"
        return 1
    fi

    query="I need to create a training program for our team. Where should I start?"
    print_info "Query: $query"

    chat_response=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/chat" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{\"message\":\"$query\",\"use_rag\":false}")

    chat_code=$(echo "$chat_response" | tail -n1)
    chat_body=$(echo "$chat_response" | sed '$d')

    if [ "$chat_code" = "200" ]; then
        print_success "Chat response received"

        reply=$(echo "$chat_body" | jq -r '.reply')

        # Check for Walter persona indicators
        indicators_found=0

        if echo "$reply" | grep -qi -e "ROI" -e "business problem" -e "KPI"; then
            print_info "✓ ROI-first approach detected"
            ((indicators_found++))
        fi

        if echo "$reply" | grep -qi -e "DDLD" -e "performance gap" -e "desired state"; then
            print_info "✓ DDLD framework detected"
            ((indicators_found++))
        fi

        if echo "$reply" | grep -qi -e "behavior" -e "on the job" -e "performance"; then
            print_info "✓ Behavior-focused approach detected"
            ((indicators_found++))
        fi

        if [ $indicators_found -ge 2 ]; then
            print_success "Walter persona verified!"
        else
            print_warning "Walter persona not strongly detected"
        fi

        echo ""
        echo "Response preview:"
        echo "$reply" | head -c 300
        echo "..."

    else
        print_error "Chat failed (HTTP $chat_code)"
        echo "$chat_body"
        return 1
    fi
}

# Test 4: Image Generation
test_image_generation() {
    print_header "TEST 4: Image Generation with Nano Banana"

    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "Skipping: Not authenticated"
        return 1
    fi

    prompt="A friendly learning professional coaching a team, professional illustration"
    print_info "Prompt: $prompt"

    image_response=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/images/generate" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{\"prompt\":\"$prompt\"}")

    image_code=$(echo "$image_response" | tail -n1)
    image_body=$(echo "$image_response" | sed '$d')

    if [ "$image_code" = "200" ]; then
        print_success "Image generated successfully"

        model=$(echo "$image_body" | jq -r '.model')
        image_url=$(echo "$image_body" | jq -r '.image_url')

        print_info "Model: $model"
        print_info "Image data length: ${#image_url} characters"

        if [[ "$image_url" == data:image* ]]; then
            print_success "Image is base64 encoded (expected format)"
        else
            print_warning "Unexpected image format"
        fi

    else
        print_error "Image generation failed (HTTP $image_code)"
        echo "$image_body"
        return 1
    fi
}

# Print summary
print_summary() {
    print_header "TEST SUMMARY"

    total=$((PASSED + FAILED + WARNINGS))

    echo "Total Tests: $total"
    echo -e "${GREEN}Passed: $PASSED${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo -e "${RED}Failed: $FAILED${NC}"

    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}✓ ALL CRITICAL TESTS PASSED!${NC}"
        if [ $WARNINGS -gt 0 ]; then
            echo -e "${YELLOW}⚠ Review warnings above${NC}"
        fi
    else
        echo -e "\n${RED}${BOLD}✗ SOME TESTS FAILED${NC}"
        echo -e "${RED}Review errors above and fix before deployment${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BOLD}${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║         WALTER L&D ASSISTANT - END-TO-END TEST SUITE           ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    print_info "Backend URL: $BACKEND_URL"
    print_info "Test User: $TEST_EMAIL"
    print_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_warning "jq not installed - JSON parsing may be limited"
        print_info "Install with: brew install jq"
    fi

    # Run tests
    test_health || exit 1
    test_auth || exit 1
    test_walter_persona
    test_image_generation

    # Print summary
    print_summary

    # Exit with appropriate code
    if [ $FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main
main
