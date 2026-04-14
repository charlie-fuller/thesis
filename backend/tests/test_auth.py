"""Authentication Tests.

Tests for API key authentication middleware.
Updated for PocketBase migration: JWT auth replaced with simple API key check.
"""

import os
from unittest.mock import patch

import pytest


# ============================================================================
# API Key Middleware Tests
# ============================================================================


class TestAPIKeyMiddleware:
    """Tests for the verify_api_key middleware."""

    def test_public_path_no_auth_required(self, test_client):
        """Test that public paths bypass authentication."""
        # Health endpoint is public
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_root_path_no_auth_required(self, test_client):
        """Test that root path bypasses authentication."""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_docs_path_no_auth_required(self, test_client):
        """Test that docs path bypasses authentication."""
        response = test_client.get("/docs")
        # May redirect or return HTML
        assert response.status_code in [200, 307]

    def test_protected_endpoint_without_auth(self, test_client):
        """Test that protected endpoints require API key."""
        response = test_client.get("/api/agents")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_key(self, test_client):
        """Test that invalid API keys are rejected."""
        response = test_client.get(
            "/api/agents",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_key(self, authenticated_client):
        """Test that valid API key grants access."""
        response = authenticated_client.get("/api/agents")
        # Should not be 401
        assert response.status_code != 401

    def test_options_request_bypasses_auth(self, test_client):
        """Test that OPTIONS requests bypass auth (CORS preflight)."""
        response = test_client.options("/api/agents")
        assert response.status_code in [200, 204, 405]

    def test_missing_authorization_header(self, test_client):
        """Test that missing Authorization header returns 401."""
        response = test_client.get("/api/conversations")
        assert response.status_code == 401

    def test_malformed_authorization_header(self, test_client):
        """Test that malformed Authorization header returns 401."""
        response = test_client.get(
            "/api/conversations",
            headers={"Authorization": "not-bearer-format"},
        )
        assert response.status_code == 401

    def test_empty_api_key_rejects_all(self, test_client):
        """Test that empty API key setting rejects all requests."""
        with patch.dict(os.environ, {"THESIS_API_KEY": ""}):
            response = test_client.get(
                "/api/agents",
                headers={"Authorization": "Bearer anything"},
            )
            # With empty key, middleware rejects (settings.api_key is falsy)
            assert response.status_code == 401


# ============================================================================
# Auth Response Format Tests
# ============================================================================


class TestAuthResponseFormat:
    """Tests for authentication error response format."""

    def test_401_response_has_detail(self, test_client):
        """Test that 401 responses include a detail message."""
        response = test_client.get("/api/agents")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_401_response_message(self, test_client):
        """Test the 401 error message content."""
        response = test_client.get(
            "/api/agents",
            headers={"Authorization": "Bearer bad-key"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "Invalid" in data["detail"] or "missing" in data["detail"].lower()
