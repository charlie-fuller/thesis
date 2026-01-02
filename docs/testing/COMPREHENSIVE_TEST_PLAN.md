# Thesis Platform - Comprehensive Test Plan

**Version:** 1.0
**Created:** 2025-12-27
**Purpose:** Complete code review, quality assessment, and testing framework

---

## Table of Contents

1. [Overview](#overview)
2. [Code Quality Indicators](#code-quality-indicators)
3. [Backend Testing](#backend-testing)
4. [Frontend Testing](#frontend-testing)
5. [Database Testing](#database-testing)
6. [Integration Testing](#integration-testing)
7. [Performance Testing](#performance-testing)
8. [Security Testing](#security-testing)
9. [Code Smell Detection](#code-smell-detection)
10. [Automated Test Checklist](#automated-test-checklist)

---

## Overview

### Platform Architecture

```
Frontend (Next.js 16 + React 19)
    ↓ HTTPS/SSE
Backend (FastAPI + Python 3.11)
    ├── 13 Specialized Agents
    ├── 22 API Route Modules
    ├── RAG Document Pipeline
    └── Neo4j Graph Integration
         ↓
Database Layer
    ├── Supabase (PostgreSQL + pgvector)
    └── Neo4j (Graph DB)
```

### Test Coverage Goals

| Layer | Current | Target |
|-------|---------|--------|
| Backend Unit Tests | ~55 tests | 200+ tests |
| Frontend Unit Tests | 0 tests | 100+ tests |
| Integration Tests | 0 tests | 50+ tests |
| E2E Tests | 0 tests | 20+ tests |

---

## Code Quality Indicators

### "Vibe Coding" Detection Patterns

These patterns indicate code that may have been written without full understanding:

1. **Copy-Paste Duplication**
   - Same logic repeated across files
   - Inconsistent naming for same operations
   - Magic numbers without constants

2. **Unclear Error Handling**
   - Bare `except Exception` blocks
   - Errors silently swallowed
   - Inconsistent error response formats

3. **Oversized Components/Modules**
   - Files over 500 lines without clear separation
   - Components doing multiple unrelated tasks
   - God classes/functions

4. **Missing Type Safety**
   - `any` types in TypeScript
   - No Pydantic validation on inputs
   - Implicit type coercion

5. **Inconsistent Patterns**
   - Different auth approaches in same codebase
   - Mixed async/sync without clear reason
   - Multiple ways to accomplish same task

6. **Dead Code**
   - Unused imports
   - Commented-out code blocks
   - Unreachable code paths

7. **Poor Naming**
   - Single-letter variables (except loops)
   - Cryptic abbreviations
   - Names that don't match behavior

---

## Backend Testing

### 1. Agent System Tests

#### 1.1 Base Agent Tests
```python
# tests/agents/test_base_agent.py

class TestBaseAgent:
    """Test BaseAgent functionality."""

    async def test_agent_initialization(self):
        """Agent should initialize with correct name and display_name."""

    async def test_system_instruction_loading(self):
        """Agent should load system instruction from DB or fallback."""

    async def test_message_building(self):
        """_build_messages should correctly format conversation history."""

    async def test_streaming_response(self):
        """stream() should yield text chunks from Claude API."""

    async def test_memory_integration(self):
        """Agent should incorporate memories into context when available."""
```

#### 1.2 Coordinator Tests
```python
# tests/agents/test_coordinator.py

class TestCoordinatorAgent:
    """Test Coordinator routing and synthesis."""

    async def test_greeting_detection(self):
        """Greetings should be handled directly without specialist routing."""

    async def test_single_domain_routing(self):
        """Single-domain queries should route to one specialist."""
        queries = [
            ("What's the ROI of this project?", ["capital"]),
            ("Is this compliant with GDPR?", ["guardian"]),
            ("Review this contract clause", ["counselor"]),
        ]

    async def test_multi_domain_routing(self):
        """Complex queries should route to multiple specialists."""
        queries = [
            ("What's the ROI and legal risk?", ["capital", "counselor"]),
            ("Security and compliance concerns", ["guardian", "counselor"]),
        ]

    async def test_llm_classification_fallback(self):
        """When keyword matching fails, LLM should classify."""

    async def test_response_synthesis(self):
        """Multiple specialist responses should be synthesized coherently."""

    async def test_graph_context_enrichment(self):
        """When Neo4j available, responses should include graph insights."""
```

#### 1.3 Specialist Agent Tests
```python
# tests/agents/test_specialists.py

class TestSpecialistAgents:
    """Test each specialist agent's domain expertise."""

    # Atlas (Research)
    async def test_atlas_research_synthesis(self):
        """Atlas should provide evidence-based recommendations."""

    async def test_atlas_lean_orientation(self):
        """Atlas should apply Toyota/Lean thinking."""

    # Capital (Finance)
    async def test_capital_roi_calculation(self):
        """Capital should provide ROI metrics and business cases."""

    async def test_capital_sox_awareness(self):
        """Capital should address SOX compliance concerns."""

    # Guardian (Governance)
    async def test_guardian_security_assessment(self):
        """Guardian should identify security concerns."""

    async def test_guardian_shadow_it_detection(self):
        """Guardian should flag shadow IT risks."""

    # Counselor (Legal)
    async def test_counselor_contract_review(self):
        """Counselor should identify contract issues."""

    async def test_counselor_ai_risk_awareness(self):
        """Counselor should address hallucination, bias, liability."""

    # Sage (People)
    async def test_sage_change_management(self):
        """Sage should provide people-first recommendations."""

    async def test_sage_burnout_prevention(self):
        """Sage should flag champion burnout risks."""

    # Oracle (Transcripts)
    async def test_oracle_sentiment_extraction(self):
        """Oracle should extract stakeholder sentiment from transcripts."""

    async def test_oracle_attendee_identification(self):
        """Oracle should identify and classify meeting attendees."""

    # Nexus (Systems Thinking)
    async def test_nexus_feedback_loop_identification(self):
        """Nexus should identify reinforcing and balancing loops."""

    async def test_nexus_leverage_point_analysis(self):
        """Nexus should apply Meadows' leverage points framework."""

    # Strategist (Executive)
    async def test_strategist_executive_engagement(self):
        """Strategist should address C-suite concerns."""

    # Architect (Technical)
    async def test_architect_pattern_recommendations(self):
        """Architect should recommend enterprise AI patterns."""

    # Operator (Operations)
    async def test_operator_process_analysis(self):
        """Operator should analyze processes for automation."""

    # Pioneer (Innovation)
    async def test_pioneer_hype_filtering(self):
        """Pioneer should distinguish hype from reality."""

    # Catalyst (Communications)
    async def test_catalyst_messaging_strategy(self):
        """Catalyst should craft internal AI messaging."""

    # Scholar (L&D)
    async def test_scholar_training_design(self):
        """Scholar should design effective training programs."""
```

### 2. API Route Tests

#### 2.1 Chat Endpoint Tests
```python
# tests/api/test_chat.py

class TestChatEndpoint:
    """Test /api/chat/* endpoints."""

    async def test_chat_requires_authentication(self):
        """Unauthenticated requests should return 401."""

    async def test_chat_validates_message_length(self):
        """Messages over limit should return 400."""

    async def test_chat_requires_conversation_id(self):
        """Requests without conversation_id should return 400."""

    async def test_chat_streaming_format(self):
        """Response should be SSE with correct event types."""

    async def test_chat_rag_context_inclusion(self):
        """When documents exist, RAG context should be included."""

    async def test_chat_rate_limiting(self):
        """Excessive requests should return 429."""

    async def test_chat_error_handling(self):
        """API errors should return structured error response."""
```

#### 2.2 Document Endpoint Tests
```python
# tests/api/test_documents.py

class TestDocumentEndpoints:
    """Test /api/documents/* endpoints."""

    async def test_upload_pdf(self):
        """PDF upload should succeed and create chunks."""

    async def test_upload_txt(self):
        """TXT upload should succeed and create chunks."""

    async def test_upload_unsupported_type(self):
        """Unsupported file types should return 400."""

    async def test_upload_size_limit(self):
        """Files over size limit should return 413."""

    async def test_storage_quota_enforcement(self):
        """Uploads exceeding quota should return 403."""

    async def test_document_deletion(self):
        """Delete should remove document and chunks."""

    async def test_document_search(self):
        """Semantic search should return relevant chunks."""
```

#### 2.3 Agent Management Tests
```python
# tests/api/test_agents.py

class TestAgentEndpoints:
    """Test /api/agents/* endpoints."""

    async def test_list_agents(self):
        """Should return all registered agents."""

    async def test_get_agent_detail(self):
        """Should return agent with current system instruction."""

    async def test_update_system_instruction(self):
        """Should create new version and activate."""

    async def test_instruction_version_history(self):
        """Should return version history with diffs."""

    async def test_activate_previous_version(self):
        """Should be able to rollback to previous version."""
```

#### 2.4 Stakeholder Tests
```python
# tests/api/test_stakeholders.py

class TestStakeholderEndpoints:
    """Test /api/stakeholders/* endpoints."""

    async def test_create_stakeholder(self):
        """Should create stakeholder with required fields."""

    async def test_update_sentiment(self):
        """Should update sentiment score and track history."""

    async def test_add_insight(self):
        """Should add insight linked to stakeholder."""

    async def test_stakeholder_search(self):
        """Should search by name, role, organization."""
```

### 3. Service Tests

#### 3.1 Document Processor Tests
```python
# tests/services/test_document_processor.py

class TestDocumentProcessor:
    """Test RAG pipeline."""

    def test_chunk_size_limits(self):
        """Chunks should respect size limits."""

    def test_chunk_overlap(self):
        """Adjacent chunks should have overlap for context."""

    def test_embedding_generation(self):
        """Voyage AI should generate 1024-dim embeddings."""

    def test_similarity_search_accuracy(self):
        """Similar content should score higher than dissimilar."""
```

#### 3.2 Graph Service Tests
```python
# tests/services/test_graph.py

class TestGraphService:
    """Test Neo4j integration."""

    async def test_connection_handling(self):
        """Should gracefully handle connection failures."""

    async def test_stakeholder_node_creation(self):
        """Should create stakeholder nodes correctly."""

    async def test_relationship_extraction(self):
        """LLM should extract relationships from text."""

    async def test_sync_consistency(self):
        """Graph should stay consistent with PostgreSQL."""
```

---

## Frontend Testing

### 1. Component Tests

#### 1.1 ChatInterface Tests
```typescript
// __tests__/components/ChatInterface.test.tsx

describe('ChatInterface', () => {
  it('should render empty state correctly', () => {});
  it('should display loading state during streaming', () => {});
  it('should render markdown in messages', () => {});
  it('should handle send button click', () => {});
  it('should disable input while streaming', () => {});
  it('should scroll to bottom on new message', () => {});
  it('should display error state on API failure', () => {});
  it('should support keyboard submit (Enter)', () => {});
});
```

#### 1.2 DocumentUpload Tests
```typescript
// __tests__/components/DocumentUpload.test.tsx

describe('DocumentUpload', () => {
  it('should accept valid file types', () => {});
  it('should reject invalid file types', () => {});
  it('should display upload progress', () => {});
  it('should handle upload errors gracefully', () => {});
  it('should enforce file size limits', () => {});
});
```

#### 1.3 AuthContext Tests
```typescript
// __tests__/contexts/AuthContext.test.tsx

describe('AuthContext', () => {
  it('should provide user state to children', () => {});
  it('should handle sign in correctly', () => {});
  it('should handle sign out correctly', () => {});
  it('should refresh profile on demand', () => {});
  it('should persist session across reloads', () => {});
});
```

### 2. Page Tests

```typescript
// __tests__/pages/HomePage.test.tsx

describe('Home Page', () => {
  it('should render stakeholder metrics', () => {});
  it('should display recent activity', () => {});
  it('should handle loading state', () => {});
  it('should show empty state when no data', () => {});
});
```

### 3. API Client Tests

```typescript
// __tests__/api/client.test.ts

describe('API Client', () => {
  it('should include auth token in requests', () => {});
  it('should handle 401 by redirecting to login', () => {});
  it('should retry on network errors', () => {});
  it('should parse JSON responses correctly', () => {});
});
```

---

## Database Testing

### 1. Schema Validation

```sql
-- tests/database/test_schema.sql

-- Verify all required tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'users', 'clients', 'conversations', 'messages',
    'documents', 'document_chunks', 'agents',
    'agent_instruction_versions', 'stakeholders',
    'stakeholder_insights', 'meeting_rooms',
    'meeting_room_participants', 'meeting_room_messages'
);

-- Verify foreign key constraints
SELECT tc.constraint_name, tc.table_name, kcu.column_name,
       ccu.table_name AS referenced_table
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';

-- Verify indexes exist for performance
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public';

-- Verify RLS policies
SELECT schemaname, tablename, policyname, cmd, qual
FROM pg_policies
WHERE schemaname = 'public';
```

### 2. Migration Tests

```python
# tests/database/test_migrations.py

class TestMigrations:
    """Test database migrations."""

    def test_migrations_are_ordered(self):
        """Migration files should have sequential numbers."""

    def test_migrations_are_idempotent(self):
        """Running migrations twice should not error."""

    def test_rollback_capability(self):
        """Each migration should have a rollback path."""
```

### 3. Data Integrity Tests

```python
# tests/database/test_integrity.py

class TestDataIntegrity:
    """Test data integrity constraints."""

    async def test_cascade_delete_conversations(self):
        """Deleting user should cascade to conversations."""

    async def test_cascade_delete_documents(self):
        """Deleting document should cascade to chunks."""

    async def test_agent_instruction_uniqueness(self):
        """Active instruction version should be unique per agent."""
```

---

## Integration Testing

### 1. End-to-End Chat Flow

```python
# tests/integration/test_chat_flow.py

class TestChatFlow:
    """Test complete chat flow."""

    async def test_new_conversation_flow(self):
        """
        1. Create conversation
        2. Send message
        3. Receive streamed response
        4. Verify message saved
        5. Verify agent attribution
        """

    async def test_rag_augmented_chat(self):
        """
        1. Upload document
        2. Wait for processing
        3. Ask question about document
        4. Verify document context in response
        """

    async def test_multi_agent_consultation(self):
        """
        1. Send cross-domain query
        2. Verify multiple agents consulted
        3. Verify synthesized response
        """
```

### 2. Document Processing Flow

```python
# tests/integration/test_document_flow.py

class TestDocumentFlow:
    """Test document upload to search flow."""

    async def test_pdf_to_search(self):
        """
        1. Upload PDF
        2. Verify chunks created
        3. Verify embeddings generated
        4. Search for content
        5. Verify results
        """
```

### 3. Stakeholder Tracking Flow

```python
# tests/integration/test_stakeholder_flow.py

class TestStakeholderFlow:
    """Test stakeholder lifecycle."""

    async def test_transcript_to_stakeholder(self):
        """
        1. Upload transcript
        2. Extract attendees
        3. Create/update stakeholders
        4. Verify sentiment scores
        5. Verify graph relationships
        """
```

---

## Performance Testing

### 1. Response Time Benchmarks

| Endpoint | Target P50 | Target P99 |
|----------|------------|------------|
| `POST /chat/send` (first token) | < 500ms | < 2000ms |
| `POST /documents/upload` (small) | < 1000ms | < 3000ms |
| `GET /conversations` | < 100ms | < 500ms |
| `GET /stakeholders` | < 100ms | < 500ms |

### 2. Load Testing Scenarios

```python
# tests/performance/test_load.py

class TestLoad:
    """Load testing scenarios."""

    async def test_concurrent_chats(self):
        """10 concurrent chat sessions should maintain response times."""

    async def test_document_upload_under_load(self):
        """5 concurrent uploads should complete without timeout."""

    async def test_rag_search_at_scale(self):
        """Search with 10000+ chunks should complete in < 500ms."""
```

### 3. Memory and Resource Tests

```python
# tests/performance/test_resources.py

class TestResources:
    """Test resource consumption."""

    def test_streaming_memory_usage(self):
        """Streaming should not accumulate memory."""

    def test_connection_pool_limits(self):
        """Database connections should be pooled and limited."""

    def test_embedding_batch_efficiency(self):
        """Large documents should batch embedding calls."""
```

---

## Security Testing

### 1. Authentication Tests

```python
# tests/security/test_auth.py

class TestAuthSecurity:
    """Test authentication security."""

    def test_jwt_expiration_enforced(self):
        """Expired tokens should be rejected."""

    def test_jwt_signature_verified(self):
        """Tampered tokens should be rejected."""

    def test_password_not_logged(self):
        """Passwords should never appear in logs."""

    def test_rate_limiting_on_login(self):
        """Failed logins should be rate limited."""
```

### 2. Authorization Tests

```python
# tests/security/test_authz.py

class TestAuthorizationSecurity:
    """Test authorization rules."""

    def test_user_cannot_access_other_users_data(self):
        """RLS should prevent cross-user access."""

    def test_admin_can_access_all_data(self):
        """Admin role should have elevated access."""

    def test_client_isolation(self):
        """Users should only see their client's data."""
```

### 3. Input Validation Tests

```python
# tests/security/test_input.py

class TestInputSecurity:
    """Test input validation."""

    def test_sql_injection_prevention(self):
        """SQL injection attempts should be blocked."""

    def test_xss_prevention(self):
        """XSS payloads should be sanitized."""

    def test_path_traversal_prevention(self):
        """Path traversal in file uploads should be blocked."""

    def test_file_type_validation(self):
        """Only allowed file types should be accepted."""
```

---

## Code Smell Detection

### Backend Code Smells to Check

```python
# scripts/code_quality/check_smells.py

SMELL_PATTERNS = {
    "bare_except": r"except\s*:",
    "todo_fixme": r"#\s*(TODO|FIXME|XXX|HACK)",
    "magic_numbers": r"(?<![\w.])\d{2,}(?![\w.])",
    "long_functions": "functions > 50 lines",
    "deep_nesting": "indentation > 4 levels",
    "god_classes": "classes > 500 lines",
    "unused_imports": "import not used",
    "duplicate_code": "similar blocks > 10 lines",
    "hardcoded_secrets": r"(password|secret|key)\s*=\s*['\"]",
    "print_statements": r"print\(",
}
```

### Frontend Code Smells to Check

```typescript
// scripts/code_quality/check_frontend_smells.ts

const SMELL_PATTERNS = {
  anyType: /:\s*any\b/,
  consoleLog: /console\.(log|debug|info)/,
  inlineStyles: /style=\{\{/,
  largeComponent: 'components > 300 lines',
  propDrilling: 'props passed > 3 levels',
  missingKeys: 'map without key prop',
  useEffectDeps: 'useEffect with missing deps',
  hardcodedStrings: 'strings not in constants',
};
```

### Automated Smell Detection Script

```bash
#!/bin/bash
# scripts/check_code_quality.sh

echo "=== Backend Code Quality ==="

# Bare except blocks
echo "Bare except blocks:"
grep -rn "except:" backend/ --include="*.py" | grep -v "except Exception"

# TODO/FIXME comments
echo "TODO/FIXME comments:"
grep -rn "TODO\|FIXME\|XXX\|HACK" backend/ --include="*.py"

# Long files
echo "Files over 500 lines:"
find backend/ -name "*.py" -exec wc -l {} \; | awk '$1 > 500'

# Unused imports (requires pylint)
echo "Running pylint for unused imports..."
pylint backend/ --disable=all --enable=W0611

echo "=== Frontend Code Quality ==="

# Any types
echo "any types:"
grep -rn ": any" frontend/ --include="*.ts" --include="*.tsx"

# Console logs
echo "console.log statements:"
grep -rn "console.log" frontend/ --include="*.ts" --include="*.tsx"

# Large components
echo "Files over 500 lines:"
find frontend/ -name "*.tsx" -exec wc -l {} \; | awk '$1 > 500'
```

---

## Automated Test Checklist

### Pre-Commit Checks

- [ ] All Python files pass `black` formatting
- [ ] All Python files pass `ruff` linting
- [ ] All TypeScript files pass `eslint`
- [ ] No `any` types in new code
- [ ] No bare `except:` blocks
- [ ] No hardcoded secrets
- [ ] No console.log statements

### CI/CD Pipeline Tests

- [ ] Backend unit tests pass (pytest)
- [ ] Frontend unit tests pass (jest)
- [ ] Integration tests pass
- [ ] Database migrations run cleanly
- [ ] Type checking passes (mypy, tsc)
- [ ] Security scan passes (bandit, npm audit)
- [ ] Performance benchmarks within limits

### Release Checklist

- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] No critical security issues
- [ ] No breaking API changes (or versioned)
- [ ] Documentation updated
- [ ] Changelog updated

---

## Running the Full Test Suite

```bash
# Backend tests
cd backend
source venv/bin/activate
python -m pytest tests/ -v --cov=. --cov-report=html

# Frontend tests
cd frontend
npm test -- --coverage

# Integration tests
cd backend
python -m pytest tests/integration/ -v

# Performance tests
cd backend
python -m pytest tests/performance/ -v --benchmark

# Code quality
./scripts/check_code_quality.sh
```

---

## Next Steps

1. **Immediate**: Run existing tests, identify gaps
2. **Week 1**: Add missing unit tests for agents
3. **Week 2**: Add API route tests
4. **Week 3**: Add frontend component tests
5. **Week 4**: Add integration and E2E tests
6. **Ongoing**: Maintain test coverage in CI/CD
