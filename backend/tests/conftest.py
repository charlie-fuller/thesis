"""Pytest configuration and fixtures for Thesis backend tests.

This file contains shared fixtures and configuration used across all test modules.
Updated for PocketBase migration: mocks pb_client instead of Supabase.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Detect if we're running ONLY integration tests
_running_integration_only = any("test_integration.py" in arg for arg in sys.argv)

# Set test environment variables before importing app
if not _running_integration_only:
    os.environ["TESTING"] = "true"
    os.environ.setdefault("THESIS_API_KEY", "test-api-key")
    os.environ.setdefault("THESIS_POCKETBASE_URL", "http://127.0.0.1:8090")
    os.environ.setdefault("THESIS_ANTHROPIC_API_KEY", "test-anthropic-key")
    os.environ.setdefault("THESIS_VOYAGE_API_KEY", "test-voyage-key")


# ============================================================================
# PocketBase Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_pb():
    """Mock PocketBase client (pb_client module) for database operations.

    Patches the module-level functions in pb_client so that any code
    calling pb_client.get_record(), pb_client.list_records(), etc.
    gets mock responses.
    """
    mock = MagicMock()

    # Default return values matching pb_client function signatures
    mock.list_records.return_value = {"page": 1, "perPage": 200, "totalPages": 1, "totalItems": 0, "items": []}
    mock.get_record.return_value = None
    mock.create_record.return_value = {"id": "test-id", "created": "2025-01-01T00:00:00Z"}
    mock.update_record.return_value = {"id": "test-id", "updated": "2025-01-01T00:00:00Z"}
    mock.delete_record.return_value = None
    mock.get_first.return_value = None
    mock.get_all.return_value = []
    mock.count.return_value = 0
    mock.escape_filter.side_effect = lambda v: v.replace("'", "\\'")
    mock.parse_json_field.side_effect = lambda v, default=None: v if isinstance(v, (dict, list)) else default

    return mock


@pytest.fixture
def mock_pb_patched(mock_pb):
    """Context manager that patches all pb_client functions.

    Usage in tests:
        def test_something(self, mock_pb_patched):
            mock_pb, patches = mock_pb_patched
            mock_pb.get_record.return_value = {"id": "123", "name": "test"}
            # ... test code that calls pb_client functions ...
    """
    patches = {}
    pb_functions = [
        "list_records", "get_record", "create_record", "update_record",
        "delete_record", "get_first", "get_all", "count",
        "escape_filter", "parse_json_field",
    ]
    active_patches = []
    for fn_name in pb_functions:
        p = patch(f"pb_client.{fn_name}", getattr(mock_pb, fn_name))
        active_patches.append(p)
        patches[fn_name] = p.start()

    yield mock_pb, patches

    for p in active_patches:
        p.stop()


# ============================================================================
# Authentication Fixtures (API key based)
# ============================================================================


@pytest.fixture
def api_key():
    """Return the test API key."""
    return os.environ.get("THESIS_API_KEY", "test-api-key")


@pytest.fixture
def auth_headers(api_key):
    """Return auth headers with the test API key."""
    return {"Authorization": f"Bearer {api_key}"}


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
# Mock Fixtures (AI providers)
# ============================================================================


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
    mock.embed.return_value.embeddings = [[0.1] * 1024]
    return mock


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
        "created": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_message():
    """Sample message data."""
    return {
        "id": "msg-123",
        "conversation_id": "conv-123",
        "role": "user",
        "content": "Hello, this is a test message",
        "created": "2025-01-01T00:00:00Z",
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
def test_client(mock_pb):
    """Create a test client with mocked PocketBase.

    The app uses API key auth middleware. Requests without a valid
    API key will get 401. Use authenticated_client for auth'd requests.
    """
    with patch("pb_client.init_pb"), \
         patch("pb_client._client", MagicMock()), \
         patch("pb_client.list_records", mock_pb.list_records), \
         patch("pb_client.get_record", mock_pb.get_record), \
         patch("pb_client.create_record", mock_pb.create_record), \
         patch("pb_client.update_record", mock_pb.update_record), \
         patch("pb_client.delete_record", mock_pb.delete_record), \
         patch("pb_client.get_first", mock_pb.get_first), \
         patch("pb_client.get_all", mock_pb.get_all), \
         patch("pb_client.count", mock_pb.count):
        from main import app

        with TestClient(app) as client:
            yield client


@pytest.fixture
def authenticated_client(test_client, auth_headers):
    """Create an authenticated test client.

    Uses the test API key defined in THESIS_API_KEY env var.
    """
    test_client.headers.update(auth_headers)
    yield test_client


@pytest.fixture
def admin_client(test_client, auth_headers):
    """Create an authenticated admin test client.

    Note: With API key auth, there is no role distinction at the auth layer.
    Admin vs user is determined by business logic, not the auth middleware.
    """
    test_client.headers.update(auth_headers)
    yield test_client


# ============================================================================
# File Fixtures
# ============================================================================


@pytest.fixture
def sample_pdf_bytes():
    """Return minimal valid PDF bytes for testing."""
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


_PROTECTED_MODULES = ["config", "pb_client", "services", "auth", "anthropic"]
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
            if hasattr(current, "_mock_name") or type(current).__name__ == "MagicMock":
                sys.modules[name] = module


_save_original_modules()


@pytest.fixture(scope="session", autouse=True)
def restore_modules_session():
    """Restore any mocked modules at the start of the test session."""
    _restore_modules()
    yield


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    _restore_modules()


# ============================================================================
# Agent Testing Fixtures
# ============================================================================


@pytest.fixture
def sample_compliance_response():
    """Sample response text with known manifesto principle trigger phrases."""
    return (
        "We need to measure the state change from baseline to target. "
        "Research shows that evidence supports this approach based on available data. "
        "This is a non-deterministic informed interpretation, not ground truth. "
        "People are the center of this transformation and we must consider the human experience. "
        "I recommend this approach, but ultimately you decide."
    )


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
        "created": "2025-01-01T00:00:00Z",
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
