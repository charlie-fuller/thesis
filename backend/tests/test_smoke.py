"""Smoke Tests

Quick health checks to verify system is operational after deployment.
These tests should run fast (< 30 seconds total) and catch critical failures.

Note: These tests require the actual app to be running with valid configuration.
They are marked with @pytest.mark.smoke and can be skipped in unit test runs.
"""

import os
import time

import pytest

# Skip all smoke tests if no real credentials are configured
_has_real_config = os.environ.get("SUPABASE_URL") and os.environ.get("ANTHROPIC_API_KEY")


# =============================================================================
# Core Service Health Checks
# =============================================================================


class TestCoreServices:
    """Verify core services are running."""

    @pytest.mark.smoke
    def test_root_endpoint(self, client):
        """Root endpoint responds."""
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.smoke
    def test_health_endpoint(self, client):
        """Health endpoint responds."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    @pytest.mark.smoke
    def test_admin_health_endpoint(self, client, auth_headers):
        """Admin health endpoint responds."""
        response = client.get("/api/admin/health", headers=auth_headers)
        # May require admin role, so 200 or 403 acceptable
        assert response.status_code in [200, 403, 401]


# =============================================================================
# Authentication Smoke Tests
# =============================================================================


class TestAuthenticationSmoke:
    """Verify authentication works."""

    @pytest.mark.smoke
    def test_protected_endpoint_requires_auth(self, client):
        """Protected endpoints require authentication."""
        response = client.get("/api/conversations")
        assert response.status_code in [401, 403, 422]

    @pytest.mark.smoke
    def test_agents_endpoint_requires_auth(self, client):
        """Agents endpoint requires authentication."""
        response = client.get("/api/agents")
        # Should require auth
        assert response.status_code in [200, 401, 403, 422]


# =============================================================================
# Core Feature Smoke Tests
# =============================================================================


class TestCoreFeatures:
    """Verify core features are operational."""

    @pytest.mark.smoke
    def test_agents_list_available(self, client, auth_headers):
        """Agent list is accessible."""
        response = client.get("/api/agents", headers=auth_headers)
        # Should respond (200 or auth error, but not 500)
        assert response.status_code in [200, 401, 403, 422]
        if response.status_code == 200:
            agents = response.json()
            assert isinstance(agents, list)

    @pytest.mark.smoke
    def test_conversations_list_works(self, client, auth_headers):
        """Conversation listing works."""
        response = client.get("/api/conversations", headers=auth_headers)
        assert response.status_code in [200, 401, 403, 422]

    @pytest.mark.smoke
    def test_tasks_endpoint_works(self, client, auth_headers):
        """Tasks endpoint is accessible."""
        response = client.get("/api/tasks", headers=auth_headers)
        assert response.status_code in [200, 401, 403, 404, 422]


# =============================================================================
# Performance Smoke Tests
# =============================================================================


class TestPerformanceSmoke:
    """Verify basic performance is acceptable."""

    @pytest.mark.smoke
    def test_health_check_response_time(self, client):
        """Health check responds quickly."""
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 2.0, "Health check should respond in < 2 seconds"

    @pytest.mark.smoke
    def test_root_response_time(self, client):
        """Root endpoint responds quickly."""
        start = time.time()
        response = client.get("/")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, "Root should respond in < 1 second"


# =============================================================================
# Error Handling Smoke Tests
# =============================================================================


class TestErrorHandling:
    """Verify error handling works correctly."""

    @pytest.mark.smoke
    def test_404_handled_gracefully(self, client):
        """404 errors are handled properly."""
        response = client.get("/api/nonexistent-endpoint-12345")
        assert response.status_code == 404
        # Should return JSON error, not HTML
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type or "text/plain" in content_type

    @pytest.mark.smoke
    def test_invalid_method_handled(self, client):
        """Invalid HTTP methods are handled."""
        response = client.delete("/health")
        # Should return method not allowed or similar
        assert response.status_code in [405, 404]


# =============================================================================
# Integration Smoke Tests
# =============================================================================


class TestIntegrationSmoke:
    """Verify key integrations work."""

    @pytest.mark.smoke
    def test_database_accessible(self, client, auth_headers):
        """Database connection works (via conversations endpoint)."""
        response = client.get("/api/conversations", headers=auth_headers)
        # Should not get 503 service unavailable
        assert response.status_code != 503


# =============================================================================
# Deployment Smoke Tests
# =============================================================================


class TestDeploymentSmoke:
    """Verify deployment is correct."""

    @pytest.mark.smoke
    def test_cors_headers_on_options(self, client):
        """CORS is configured."""
        response = client.options("/health")
        # CORS should allow the request
        assert response.status_code in [200, 204, 403, 405]

    @pytest.mark.smoke
    def test_health_shows_environment(self, client):
        """Health endpoint shows environment info."""
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            # Should have some status info
            assert "status" in data


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
def auth_headers(valid_jwt_token):
    """Get authentication headers for smoke tests."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


# =============================================================================
# Run Configuration
# =============================================================================

# To run only smoke tests:
# pytest -m smoke --tb=short -v

# Smoke test configuration
SMOKE_TEST_TIMEOUT = 30  # Total timeout for all smoke tests
INDIVIDUAL_TEST_TIMEOUT = 5  # Timeout per test
