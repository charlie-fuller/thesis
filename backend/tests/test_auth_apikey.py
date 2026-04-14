import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import verify_api_key


@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    app.middleware("http")(verify_api_key)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_valid_api_key(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/test", headers={"Authorization": "Bearer test-key-123"})
        assert resp.status_code == 200


def test_invalid_api_key(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/test", headers={"Authorization": "Bearer wrong-key"})
        assert resp.status_code == 401


def test_missing_api_key(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/test")
        assert resp.status_code == 401


def test_health_bypasses_auth(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/health")
        assert resp.status_code == 200
