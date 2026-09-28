"""
Unit tests for the frontend REST API client.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.frontend.services.api_client import APIClient

# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def client() -> APIClient:
    """Create API client."""
    return APIClient(base_url="http://localhost:8000")


# ==========================================================
# Internal GET
# ==========================================================


@patch("src.frontend.services.api_client.httpx.Client.request")
def test_get_success(mock_request, client):
    """Test internal GET helper."""
    response = MagicMock()
    response.json.return_value = {"success": True}
    response.raise_for_status.return_value = None
    mock_request.return_value = response

    result = client._get("/health")

    assert result["success"] is True
    mock_request.assert_called_once_with(
        method="GET",
        url="/health",
        params=None,
        json=None,
        headers=None,
    )


# ==========================================================
# Internal POST
# ==========================================================


@patch("src.frontend.services.api_client.httpx.Client.request")
def test_post_success(mock_request, client):
    """Test internal POST helper."""
    payload = {"input_path": "sample.csv"}
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"success": True}
    mock_request.return_value = response

    result = client._post("/pipeline", payload)

    assert result["success"] is True
    mock_request.assert_called_once_with(
        method="POST",
        url="/pipeline",
        params=None,
        json=payload,
        headers=None,
    )


# ==========================================================
# Root
# ==========================================================


@patch.object(APIClient, "_get")
def test_root(mock_get, client):
    """Test root endpoint."""
    mock_get.return_value = {}
    client.root()
    mock_get.assert_called_once_with("/")


# ==========================================================
# Health
# ==========================================================


@patch.object(APIClient, "_get")
def test_health(mock_get, client):
    """Test health endpoint."""
    mock_get.return_value = {}
    client.health()
    mock_get.assert_called_once_with("/api/health")


# ==========================================================
# Version
# ==========================================================


@patch.object(APIClient, "_get")
def test_version(mock_get, client):
    """Test version endpoint."""
    mock_get.return_value = {}
    client.version()
    mock_get.assert_called_once_with("/api/version")


# ==========================================================
# Dashboard
# ==========================================================


@patch.object(APIClient, "_get")
def test_dashboard(mock_get, client):
    """Test dashboard endpoint."""
    mock_get.return_value = {}
    client.dashboard(dataset="test_dataset")
    # The actual call uses /powerbi/dashboard with a query parameter
    mock_get.assert_called_once_with(
        "/api/powerbi/dashboard",
        params={"dataset": "test_dataset"},
    )


# ==========================================================
# Reports
# ==========================================================


@patch.object(APIClient, "_get")
def test_reports(mock_get, client):
    """Test reports endpoint."""
    mock_get.return_value = {}
    client.reports()
    mock_get.assert_called_once_with("/api/reports")


# ==========================================================
# Pipeline
# ==========================================================


@patch.object(APIClient, "_post")
def test_run_pipeline(mock_post, client):
    """Test pipeline endpoint."""
    payload = {"input_path": "sample.csv"}
    mock_post.return_value = {}
    client.run_pipeline(payload)
    mock_post.assert_called_once_with("/api/pipeline", payload)


# ==========================================================
# Context Manager
# ==========================================================


@patch.object(APIClient, "close")
def test_context_manager(mock_close):
    """Test context manager closes client."""
    with APIClient(base_url="http://localhost:8000") as client:
        assert isinstance(client, APIClient)
    mock_close.assert_called_once()


# ==========================================================
# Close
# ==========================================================


def test_close(client):
    """Test HTTP client closes correctly."""
    with patch.object(client._client, "close") as mock_close:
        client.close()
        mock_close.assert_called_once()
