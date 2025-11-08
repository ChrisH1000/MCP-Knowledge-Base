"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from rag_server.server import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_config_endpoint(client):
    """Test config endpoint."""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "RAG_DATA_DIR" in data
    assert data["RAG_API_KEY"] == "***REDACTED***"


def test_unauthorized_request(client):
    """Test API key authentication."""
    response = client.post("/index/build", json={"root": "./"})
    assert response.status_code == 401


def test_authorized_request_missing_root(client):
    """Test authorized request with bad data."""
    response = client.post(
        "/index/build",
        headers={"x-api-key": "test-api-key-123"},
        json={"root": "/nonexistent"},
    )
    assert response.status_code == 400
