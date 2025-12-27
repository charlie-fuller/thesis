"""
Pytest configuration and fixtures for Thesis backend tests.

This file contains shared fixtures and configuration used across all test modules.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["TESTING"] = "true"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-key-for-testing-only"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role-key"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["VOYAGE_API_KEY"] = "test-voyage-key"


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
        "sub": "test-user-id-12345",
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
        "sub": "test-user-id-12345",
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
        "id": "admin-user-id-12345",
        "email": "admin@example.com",
        "role": "admin",
        "client_id": "00000000-0000-0000-0000-000000000001"
    }


@pytest.fixture
def regular_user():
    """Return regular user data."""
    return {
        "id": "regular-user-id-12345",
        "email": "user@example.com",
        "role": "user",
        "client_id": "00000000-0000-0000-0000-000000000001"
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
        "processed": True
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
        "created_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_message():
    """Sample message data."""
    return {
        "id": "msg-123",
        "conversation_id": "conv-123",
        "role": "user",
        "content": "Hello, this is a test message",
        "created_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_chunk():
    """Sample document chunk with embedding."""
    return {
        "id": "chunk-123",
        "document_id": "doc-123",
        "content": "This is a sample chunk of text from a document.",
        "chunk_index": 0,
        "embedding": [0.1] * 1024
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
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])

    # Mock user lookup for auth
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={"role": "user", "client_id": regular_user["client_id"]}
    )

    # Mock documents list
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

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
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={"role": "admin", "client_id": admin_user["client_id"]}
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
    return b"""%PDF-1.4
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
# Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    # Add any cleanup logic here
