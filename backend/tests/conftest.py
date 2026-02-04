"""Pytest configuration and fixtures for Thesis backend tests.

This file contains shared fixtures and configuration used across all test modules.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Load real .env file first (before setting any test defaults)
# This ensures integration tests have access to real credentials
from dotenv import load_dotenv

_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

import pytest
from fastapi.testclient import TestClient

# Detect if we're running ONLY integration tests
# Check sys.argv for test_integration.py to avoid mock pollution
_running_integration_only = any("test_integration.py" in arg for arg in sys.argv)

# Set test environment variables before importing app
# BUT skip for integration-only runs to preserve real credentials
if not _running_integration_only:
    os.environ["TESTING"] = "true"

    # Only set fallback test values if no real credentials are present
    # This allows integration tests to run with real .env values
    def _set_if_not_real(key: str, test_value: str, min_real_length: int = 30):
        """Set environment variable only if current value looks like a placeholder."""
        current = os.environ.get(key, "")
        if not current or len(current) < min_real_length or "test" in current.lower():
            os.environ[key] = test_value

    _set_if_not_real("SUPABASE_JWT_SECRET", "test-jwt-secret-key-for-testing-only", 50)
    _set_if_not_real("SUPABASE_URL", "https://test.supabase.co", 20)
    _set_if_not_real("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key", 50)
    _set_if_not_real("ANTHROPIC_API_KEY", "test-anthropic-key", 20)
    _set_if_not_real("VOYAGE_API_KEY", "test-voyage-key", 20)


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for database operations."""
    mock = MagicMock()

    # Mock table operations
    mock.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
    mock.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.table.return_value.update.return_value.execute.return_value = MagicMock(data=[])
    mock.table.return_value.delete.return_value.execute.return_value = MagicMock(data=[])

    # Mock storage operations
    mock.storage.from_.return_value.upload.return_value = MagicMock(path="test-path")
    mock.storage.from_.return_value.download.return_value = b"test content"
    mock.storage.from_.return_value.remove.return_value = MagicMock()

    return mock


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client for Claude API calls."""
    mock = MagicMock()

    # Mock streaming response
    mock_stream = MagicMock()
    mock_stream.text_stream = iter(["Hello", " ", "from", " ", "Claude!"])
    mock.messages.stream.return_value.__enter__.return_value = mock_stream

    return mock


@pytest.fixture
def mock_voyage():
    """Mock Voyage AI client for embeddings."""
    mock = MagicMock()

    # Mock embedding response
    mock.embed.return_value.embeddings = [[0.1] * 1024]

    return mock


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing."""
    from datetime import datetime, timedelta, timezone

    import jwt

    payload = {
        "sub": "00000000-0000-0000-0000-000000000002",
        "email": "testuser@example.com",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token for testing."""
    from datetime import datetime, timedelta, timezone

    import jwt

    payload = {
        "sub": "00000000-0000-0000-0000-000000000002",
        "email": "testuser@example.com",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
    }

    return jwt.encode(payload, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")


@pytest.fixture
def admin_user():
    """Return admin user data."""
    return {
        "id": "00000000-0000-0000-0000-000000000003",
        "email": "admin@example.com",
        "role": "admin",
        "client_id": "00000000-0000-0000-0000-000000000001",
    }


@pytest.fixture
def regular_user():
    """Return regular user data."""
    return {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "user@example.com",
        "role": "user",
        "client_id": "00000000-0000-0000-0000-000000000001",
    }


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_document():
    """Sample document data."""
    return {
        "id": "doc-123",
        "client_id": "00000000-0000-0000-0000-000000000001",
        "uploaded_by": "test-user-id",
        "filename": "test-document.pdf",
        "storage_path": "test-client/test-document.pdf",
        "storage_url": "https://test.supabase.co/storage/v1/object/test-document.pdf",
        "mime_type": "application/pdf",
        "file_size": 1024,
        "processed": True,
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation data."""
    return {
        "id": "conv-123",
        "user_id": "test-user-id",
        "client_id": "00000000-0000-0000-0000-000000000001",
        "title": "Test Conversation",
        "archived": False,
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_message():
    """Sample message data."""
    return {
        "id": "msg-123",
        "conversation_id": "conv-123",
        "role": "user",
        "content": "Hello, this is a test message",
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_chunk():
    """Sample document chunk with embedding."""
    return {
        "id": "chunk-123",
        "document_id": "doc-123",
        "content": "This is a sample chunk of text from a document.",
        "chunk_index": 0,
        "embedding": [0.1] * 1024,
    }


# ============================================================================
# Test Client Fixtures
# ============================================================================


@pytest.fixture
def test_client():
    """Create a test client with mocked dependencies."""
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])

    with patch("database.get_supabase", return_value=mock_supabase):
        from main import app

        with TestClient(app) as client:
            yield client


@pytest.fixture
def authenticated_client(valid_jwt_token, regular_user):
    """Create an authenticated test client with properly mocked database."""
    mock_supabase = MagicMock()

    # Default mock for conversations list
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = (
        MagicMock(data=[])
    )

    # Mock user lookup for auth
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
        MagicMock(data={"role": "user", "client_id": regular_user["client_id"]})
    )

    # Mock documents list
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

    with patch("database.get_supabase", return_value=mock_supabase):
        from main import app

        with TestClient(app) as client:
            client.headers = {"Authorization": f"Bearer {valid_jwt_token}"}
            yield client


@pytest.fixture
def admin_client(valid_jwt_token, admin_user):
    """Create an authenticated admin test client."""
    mock_supabase = MagicMock()

    # Mock user lookup for auth
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
        MagicMock(data={"role": "admin", "client_id": admin_user["client_id"]})
    )

    with patch("database.get_supabase", return_value=mock_supabase):
        from main import app

        with TestClient(app) as client:
            client.headers = {"Authorization": f"Bearer {valid_jwt_token}"}
            yield client


# ============================================================================
# Async Fixtures
# ============================================================================


@pytest.fixture
def mock_async_supabase():
    """Mock async Supabase operations."""
    mock = AsyncMock()
    mock.execute_query = AsyncMock(return_value={"data": [], "error": None})
    return mock


# ============================================================================
# File Fixtures
# ============================================================================


@pytest.fixture
def sample_pdf_bytes():
    """Return minimal valid PDF bytes for testing."""
    # Minimal PDF structure
    return b"""%PDF-1.4.
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [] /Count 0 >> endobj
xref
0 3
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
trailer << /Size 3 /Root 1 0 R >>
startxref
115
%%EOF"""


@pytest.fixture
def sample_txt_content():
    """Return sample text content for testing."""
    return b"""This is a sample text document for testing.

It contains multiple paragraphs of text that can be used to test
document processing, chunking, and embedding generation.

Key points:
1. First point about testing
2. Second point about document processing
3. Third point about embeddings

This concludes the sample document."""


# ============================================================================
# Module State Management
# ============================================================================

import sys

# Store original modules that might get mocked
_PROTECTED_MODULES = ["config", "database", "services", "auth", "anthropic"]
_original_modules = {}


def _save_original_modules():
    """Save original modules before tests run."""
    for name in _PROTECTED_MODULES:
        if name in sys.modules:
            _original_modules[name] = sys.modules[name]


def _restore_modules():
    """Restore original modules if they were replaced with mocks."""
    for name, module in _original_modules.items():
        if name in sys.modules:
            current = sys.modules[name]
            # If current module is a Mock, restore original
            if hasattr(current, "_mock_name") or type(current).__name__ == "MagicMock":
                sys.modules[name] = module


# Save modules at import time
_save_original_modules()


@pytest.fixture(scope="session", autouse=True)
def restore_modules_session():
    """Restore any mocked modules at the start of the test session."""
    _restore_modules()
    yield


# ============================================================================
# Cleanup
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    # Restore modules that may have been mocked
    _restore_modules()


# ============================================================================
# Agent Testing Fixtures
# ============================================================================


@pytest.fixture
def sample_agent_response():
    """Sample agent response for quality testing."""
    return """**Key AI Trends for 2026**.

Based on recent Gartner research, enterprise AI adoption is accelerating with three dominant trends:

1. **Agentic AI** - Autonomous systems capable of multi-step reasoning
2. **Multimodal Foundation Models** - Integration of text, image, and code
3. **AI Engineering Platforms** - Operationalizing AI at scale

McKinsey estimates 75% of enterprises will adopt agentic AI by 2027.

*Sources: Gartner Hype Cycle 2025, McKinsey AI Adoption Report*"""


@pytest.fixture
def mock_agent_responses():
    """Mock responses from different agents."""
    return {
        "atlas": "Research shows AI adoption is accelerating with 65% of enterprises piloting generative AI.",
        "capital": "ROI analysis shows 3-year NPV of $2.4M with 14-month payback period.",
        "guardian": "Security assessment identifies three key risks: data privacy, model vulnerabilities, and compliance gaps.",
        "counselor": "Legal review identifies IP ownership and liability as primary concerns.",
        "sage": "Change management should focus on building champions and addressing employee concerns.",
    }


@pytest.fixture
def coordinator_context():
    """Context for coordinator agent testing."""
    return {
        "conversation_history": [],
        "available_agents": ["atlas", "capital", "guardian", "counselor", "sage"],
        "client_context": "Enterprise AI implementation for financial services company",
    }


# ============================================================================
# Security Testing Fixtures
# ============================================================================


@pytest.fixture
def malicious_inputs():
    """Collection of malicious inputs for security testing."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1; UPDATE users SET role='admin'",
            "UNION SELECT * FROM users",
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2fetc/passwd",
        ],
        "template_injection": [
            "{{7*7}}",
            "${7*7}",
            "{{config.items()}}",
        ],
    }


@pytest.fixture
def rate_limit_config():
    """Rate limit configuration for testing."""
    return {
        "chat": {"requests_per_minute": 20},
        "upload": {"requests_per_minute": 10},
        "search": {"requests_per_minute": 50},
    }


# ============================================================================
# Meeting Room Fixtures
# ============================================================================


@pytest.fixture
def sample_meeting_room():
    """Sample meeting room data."""
    return {
        "id": "room-123",
        "name": "Strategy Meeting",
        "topic": "AI Implementation Strategy",
        "autonomous_mode": False,
        "participants": ["atlas", "capital", "guardian"],
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_meeting_messages():
    """Sample meeting room messages."""
    return [
        {"role": "user", "content": "What are the key considerations?"},
        {"role": "assistant", "agent_id": "atlas", "content": "Research shows..."},
        {"role": "assistant", "agent_id": "capital", "content": "Financial analysis..."},
    ]


# ============================================================================
# Integration Test Fixtures
# ============================================================================


@pytest.fixture
def integration_supabase():
    """Real Supabase client for integration tests.

    Only used when INTEGRATION_TESTS=true is set.
    """
    import os

    if os.environ.get("INTEGRATION_TESTS") != "true":
        pytest.skip("Integration tests disabled")

    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        pytest.skip("Supabase credentials not configured")

    return create_client(url, key)


@pytest.fixture
def integration_client(integration_supabase):
    """Test client for integration tests with real database."""
    from main import app

    with TestClient(app) as client:
        yield client


# ============================================================================
# Performance Testing Fixtures
# ============================================================================


@pytest.fixture
def performance_config():
    """Performance testing configuration."""
    return {
        "response_time_targets": {
            "p50": 100,  # ms
            "p95": 300,
            "p99": 500,
        },
        "concurrent_users": 50,
        "test_duration_seconds": 60,
    }


# ============================================================================
# Project Testing Fixtures
# ============================================================================


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        "id": "opp-123",
        "client_id": "00000000-0000-0000-0000-000000000001",
        "name": "AI Chatbot Implementation",
        "description": "Implement customer service chatbot",
        "status": "discovery",
        "impact_score": 8,
        "feasibility_score": 7,
        "alignment_score": 9,
        "tier": 1,
    }


@pytest.fixture
def sample_stakeholder():
    """Sample stakeholder data."""
    return {
        "id": "stake-123",
        "client_id": "00000000-0000-0000-0000-000000000001",
        "name": "John Smith",
        "role": "CTO",
        "email": "john.smith@example.com",
        "sentiment_score": 0.8,
        "engagement_level": "high",
    }
