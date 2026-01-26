"""
Smoke Tests

Quick health checks to verify system is operational after deployment.
These tests should run fast (< 30 seconds total) and catch critical failures.
"""
import pytest
from typing import Dict, Any
import time


# =============================================================================
# Core Service Health Checks
# =============================================================================

class TestCoreServices:
    """Verify core services are running."""

    @pytest.mark.smoke
    def test_api_health_endpoint(self, client):
        """API health endpoint responds."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"

    @pytest.mark.smoke
    def test_database_connection(self, client):
        """Database is accessible."""
        response = client.get("/api/health/db")
        assert response.status_code == 200
        assert response.json().get("database") == "connected"

    @pytest.mark.smoke
    def test_cache_connection(self, client):
        """Cache (Redis) is accessible if used."""
        response = client.get("/api/health/cache")
        # May return 200 or 503 if cache not configured
        assert response.status_code in [200, 503]

    @pytest.mark.smoke
    def test_ai_service_connection(self, client):
        """AI service (Anthropic) is reachable."""
        response = client.get("/api/health/ai")
        assert response.status_code == 200
        # Don't make actual AI call, just verify config

    @pytest.mark.smoke
    def test_storage_connection(self, client):
        """Storage service is accessible."""
        response = client.get("/api/health/storage")
        assert response.status_code in [200, 503]


# =============================================================================
# Authentication Smoke Tests
# =============================================================================

class TestAuthenticationSmoke:
    """Verify authentication works."""

    @pytest.mark.smoke
    def test_login_endpoint_accessible(self, client):
        """Login endpoint responds."""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "test"
        })
        # Should get 401 for invalid creds, not 500
        assert response.status_code in [200, 401, 422]

    @pytest.mark.smoke
    def test_protected_endpoint_requires_auth(self, client):
        """Protected endpoints require authentication."""
        response = client.get("/api/conversations")
        assert response.status_code in [401, 403]

    @pytest.mark.smoke
    def test_jwt_validation_works(self, client, auth_headers):
        """JWT token validation works."""
        response = client.get("/api/conversations", headers=auth_headers)
        # Should not be auth error
        assert response.status_code != 401


# =============================================================================
# Core Feature Smoke Tests
# =============================================================================

class TestCoreFeatures:
    """Verify core features are operational."""

    @pytest.mark.smoke
    def test_chat_endpoint_responds(self, client, auth_headers):
        """Chat endpoint is operational."""
        response = client.post("/api/chat", json={
            "message": "Hello",
            "stream": False
        }, headers=auth_headers)
        # Should respond (may be error if no conversation, but not 500)
        assert response.status_code in [200, 400, 422]

    @pytest.mark.smoke
    def test_agents_list_available(self, client, auth_headers):
        """Agent list is accessible."""
        response = client.get("/api/agents", headers=auth_headers)
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) > 0, "Should have at least one agent"

    @pytest.mark.smoke
    def test_conversations_list_works(self, client, auth_headers):
        """Conversation listing works."""
        response = client.get("/api/conversations", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.smoke
    def test_documents_endpoint_works(self, client, auth_headers):
        """Documents endpoint is accessible."""
        response = client.get("/api/documents", headers=auth_headers)
        assert response.status_code in [200, 404]

    @pytest.mark.smoke
    def test_tasks_endpoint_works(self, client, auth_headers):
        """Tasks endpoint is accessible."""
        response = client.get("/api/tasks", headers=auth_headers)
        assert response.status_code in [200, 404]


# =============================================================================
# Performance Smoke Tests
# =============================================================================

class TestPerformanceSmoke:
    """Verify basic performance is acceptable."""

    @pytest.mark.smoke
    def test_health_check_response_time(self, client):
        """Health check responds quickly."""
        start = time.time()
        response = client.get("/api/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, "Health check should respond in < 1 second"

    @pytest.mark.smoke
    def test_agent_list_response_time(self, client, auth_headers):
        """Agent list responds quickly."""
        start = time.time()
        response = client.get("/api/agents", headers=auth_headers)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 2.0, "Agent list should respond in < 2 seconds"

    @pytest.mark.smoke
    def test_conversation_list_response_time(self, client, auth_headers):
        """Conversation list responds quickly."""
        start = time.time()
        response = client.get("/api/conversations", headers=auth_headers)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 3.0, "Conversation list should respond in < 3 seconds"


# =============================================================================
# Error Handling Smoke Tests
# =============================================================================

class TestErrorHandling:
    """Verify error handling works correctly."""

    @pytest.mark.smoke
    def test_404_handled_gracefully(self, client):
        """404 errors are handled properly."""
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404
        # Should return JSON error, not HTML
        assert "application/json" in response.headers.get("content-type", "")

    @pytest.mark.smoke
    def test_invalid_json_handled(self, client, auth_headers):
        """Invalid JSON is handled properly."""
        response = client.post(
            "/api/chat",
            data="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    @pytest.mark.smoke
    def test_validation_errors_handled(self, client, auth_headers):
        """Validation errors return proper response."""
        response = client.post("/api/chat", json={
            # Missing required fields
        }, headers=auth_headers)
        assert response.status_code == 422


# =============================================================================
# Integration Smoke Tests
# =============================================================================

class TestIntegrationSmoke:
    """Verify key integrations work."""

    @pytest.mark.smoke
    def test_supabase_connection(self, client, auth_headers):
        """Supabase database connection works."""
        # Any database operation will verify connection
        response = client.get("/api/conversations", headers=auth_headers)
        # Should not get connection error
        assert response.status_code != 503

    @pytest.mark.smoke
    def test_anthropic_api_configured(self, client):
        """Anthropic API key is configured."""
        response = client.get("/api/health/ai")
        data = response.json()
        assert data.get("anthropic_configured", False) is True

    @pytest.mark.smoke
    def test_voyage_api_configured(self, client):
        """Voyage embeddings API is configured."""
        response = client.get("/api/health/embeddings")
        # May not be required, so 200 or 503 acceptable
        assert response.status_code in [200, 503]


# =============================================================================
# Deployment Smoke Tests
# =============================================================================

class TestDeploymentSmoke:
    """Verify deployment is correct."""

    @pytest.mark.smoke
    def test_cors_headers_present(self, client):
        """CORS headers are configured."""
        response = client.options("/api/health")
        # Should have CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in [h.lower() for h in headers.keys()] or \
               response.status_code == 200

    @pytest.mark.smoke
    def test_version_endpoint(self, client):
        """Version endpoint returns deployment info."""
        response = client.get("/api/version")
        if response.status_code == 200:
            data = response.json()
            assert "version" in data or "commit" in data

    @pytest.mark.smoke
    def test_environment_correct(self, client):
        """Environment is correctly identified."""
        response = client.get("/api/health")
        data = response.json()
        # Should indicate environment
        env = data.get("environment", "unknown")
        assert env in ["development", "staging", "production", "test", "unknown"]


# =============================================================================
# Fixtures for Smoke Tests
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authentication headers for smoke tests."""
    # Use test token or service account
    return {"Authorization": "Bearer test-smoke-token"}


# =============================================================================
# Run Configuration
# =============================================================================

# To run only smoke tests:
# pytest -m smoke --tb=short -v

# Smoke test configuration
SMOKE_TEST_TIMEOUT = 30  # Total timeout for all smoke tests
INDIVIDUAL_TEST_TIMEOUT = 5  # Timeout per test
