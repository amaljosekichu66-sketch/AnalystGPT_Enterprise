"""
Integration tests for the API root endpoint.
"""

from fastapi.testclient import TestClient

from src.api.server import app
from src.core.constants import (
    APP_NAME,
    APP_VERSION,
    APP_STATUS,
    API_DOCS_URL,
)

client = TestClient(app)


# ==========================================================
# Root Endpoint Tests
# ==========================================================

def test_root_endpoint_returns_success() -> None:
    """
    Verify that the root endpoint returns HTTP 200.
    """

    response = client.get("/")

    assert response.status_code == 200


def test_root_endpoint_returns_expected_response() -> None:
    """
    Verify that the root endpoint returns
    the expected application information.
    """

    response = client.get("/")

    data = response.json()

    assert data["success"] is True
    assert data["application"] == APP_NAME
    assert data["version"] == APP_VERSION
    assert data["status"] == APP_STATUS
    assert data["documentation"] == API_DOCS_URL