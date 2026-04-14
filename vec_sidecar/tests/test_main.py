import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch("database.get_db") as mock_db:
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        from main import app
        yield TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
