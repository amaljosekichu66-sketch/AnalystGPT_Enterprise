"""
Integration tests for the health endpoint.
"""

from fastapi.testclient import TestClient

from src.api.server import app
from src.core.constants import HEALTH_STATUS

client = TestClient(app)


# ==========================================================
# Health Endpoint Tests
# ==========================================================

def test_health_endpoint_returns_success() -> None:
    """
    Verify that the health endpoint returns HTTP 200.
    """

    response = client.get("/api/health")

    assert response.status_code == 200


def test_health_endpoint_returns_expected_response() -> None:
    """
    Verify that the health endpoint returns
    the expected health status.
    """

    response = client.get("/api/health")

    data = response.json()

    assert data["success"] is True
    assert data["status"] == HEALTH_STATUS