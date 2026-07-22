"""
Integration tests for the version endpoint.
"""

from fastapi.testclient import TestClient

from src.api.server import app
from src.core.constants import APP_VERSION

client = TestClient(app)


# ==========================================================
# Version Endpoint Tests
# ==========================================================

def test_version_endpoint_returns_success() -> None:
    """
    Verify that the version endpoint returns HTTP 200.
    """

    response = client.get("/api/version")

    assert response.status_code == 200


def test_version_endpoint_returns_expected_response() -> None:
    """
    Verify that the version endpoint returns
    the current application version.
    """

    response = client.get("/api/version")

    data = response.json()

    assert data["success"] is True
    assert data["version"] == APP_VERSION