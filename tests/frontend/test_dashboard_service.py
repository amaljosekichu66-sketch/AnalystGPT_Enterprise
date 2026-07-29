"""
Unit tests for the Dashboard Service.
"""

from unittest.mock import MagicMock, patch

import httpx
import pandas as pd
import pytest
import streamlit as st  # <-- Added this import

from src.frontend.services.dashboard_service import (
    _local_dashboard_data,
    clear_dashboard_cache,
    get_dashboard_data,
)


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture
def sample_dataframe():
    """Sample dataframe."""
    return pd.DataFrame(
        {
            "id": [1, 2, 2],
            "name": ["Alice", "Bob", "Bob"],
            "salary": [100, 200, None],
        }
    )


@pytest.fixture
def uploaded_file():
    """Mock uploaded file."""
    file = MagicMock()
    file.name = "employees.csv"
    return file


# ==========================================================
# Local Dashboard Tests
# ==========================================================

@patch("src.frontend.services.dashboard_service.get_dataset")
def test_local_dashboard_without_dataset(mock_get_dataset):
    """Local dashboard with no dataset."""
    mock_get_dataset.return_value = (None, None)
    result = _local_dashboard_data()
    assert result["dataset_loaded"] is False
    assert result["filename"] is None
    assert result["rows"] == 0
    assert result["columns"] == 0
    assert result["source"] == "session"


@patch("src.frontend.services.dashboard_service.get_dataset")
def test_local_dashboard_with_dataset(mock_get_dataset, uploaded_file, sample_dataframe):
    """Local dashboard with dataset."""
    mock_get_dataset.return_value = (uploaded_file, sample_dataframe)
    result = _local_dashboard_data()
    assert result["dataset_loaded"] is True
    assert result["filename"] == "employees.csv"
    assert result["rows"] == 3
    assert result["columns"] == 3
    assert result["missing"] == 1
    assert result["duplicates"] == 0
    assert result["numeric_columns"] == 2
    assert result["categorical_columns"] == 1
    assert result["source"] == "session"


# ==========================================================
# Cache Tests
# ==========================================================

def test_clear_dashboard_cache():
    """Test clearing the dashboard cache."""
    with patch("streamlit.session_state", {"dashboard_cache": "data", "dashboard_dataset": "path"}):
        clear_dashboard_cache()
        assert "dashboard_cache" not in st.session_state
        assert "dashboard_dataset" not in st.session_state


# ==========================================================
# API Integration Tests
# ==========================================================

@patch("src.frontend.services.dashboard_service.get_dataset")
@patch("src.frontend.services.dashboard_service.get_dataset_path")
@patch("src.frontend.services.dashboard_service._get_cached_dashboard")
@patch("src.frontend.services.dashboard_service.APIClient")
def test_dashboard_api_success(
    mock_client_cls,
    mock_cache,
    mock_get_path,
    mock_get_dataset,
    uploaded_file,
    sample_dataframe,
):
    """
    Dashboard uses API successfully when dataset is loaded locally and no cache exists.
    """
    # Arrange
    dataset_path = "/fake/path/dataset.csv"
    mock_get_path.return_value = dataset_path
    mock_cache.return_value = None  # No cached data

    # Mock get_dataset to return a real dataset so _local_dashboard_data loads it
    mock_get_dataset.return_value = (uploaded_file, sample_dataframe)

    # Mock the API client
    client = MagicMock()
    client.powerbi_dashboard.return_value = {
        "success": True,
        "execution_time": 1.23,
        "output_path": "reports/report.txt",
        "report": {"some": "data"},
        "ai_report": {"summary": "AI summary"},
    }
    mock_client_cls.return_value.__enter__.return_value = client

    # Act
    with patch("streamlit.session_state", {}):
        result = get_dashboard_data()

    # Assert
    assert result["source"] == "api"
    assert result["api_status"] is not None
    assert result["api_status"]["success"] is True
    assert result["execution_time"] == 1.23
    assert result["output_path"] == "reports/report.txt"
    assert result["ai_report"] == {"summary": "AI summary"}
    assert result["backend_report"] == {"some": "data"}

    client.powerbi_dashboard.assert_called_once_with(dataset_path)
    mock_client_cls.return_value.__enter__.assert_called_once()
    mock_client_cls.return_value.__exit__.assert_called_once()


@patch("src.frontend.services.dashboard_service.get_dataset")
@patch("src.frontend.services.dashboard_service.get_dataset_path")
@patch("src.frontend.services.dashboard_service._get_cached_dashboard")
@patch("src.frontend.services.dashboard_service.APIClient")
def test_dashboard_api_failure(
    mock_client_cls,
    mock_cache,
    mock_get_path,
    mock_get_dataset,
    uploaded_file,
    sample_dataframe,
):
    """Dashboard falls back to session when API raises OSError."""
    dataset_path = "/fake/path/dataset.csv"
    mock_get_path.return_value = dataset_path
    mock_cache.return_value = None

    mock_get_dataset.return_value = (uploaded_file, sample_dataframe)

    client = MagicMock()
    client.powerbi_dashboard.side_effect = OSError("API down")
    mock_client_cls.return_value.__enter__.return_value = client

    with patch("streamlit.session_state", {}):
        result = get_dashboard_data()

    # Should return local session data (since API failed)
    assert result["source"] == "session"
    assert result["dataset_loaded"] is True
    assert "api_error" in result
    assert "API down" in str(result["api_error"])
    mock_client_cls.return_value.__enter__.assert_called_once()
    mock_client_cls.return_value.__exit__.assert_called_once()


@patch("src.frontend.services.dashboard_service.get_dataset")
@patch("src.frontend.services.dashboard_service.get_dataset_path")
@patch("src.frontend.services.dashboard_service._get_cached_dashboard")
@patch("src.frontend.services.dashboard_service.APIClient")
def test_dashboard_http_error(
    mock_client_cls,
    mock_cache,
    mock_get_path,
    mock_get_dataset,
    uploaded_file,
    sample_dataframe,
):
    """HTTP errors fall back to session."""
    dataset_path = "/fake/path/dataset.csv"
    mock_get_path.return_value = dataset_path
    mock_cache.return_value = None

    mock_get_dataset.return_value = (uploaded_file, sample_dataframe)

    client = MagicMock()
    client.powerbi_dashboard.side_effect = httpx.HTTPError("API unavailable")
    mock_client_cls.return_value.__enter__.return_value = client

    with patch("streamlit.session_state", {}):
        result = get_dashboard_data()

    assert result["source"] == "session"
    assert result["dataset_loaded"] is True
    assert "api_error" in result
    assert "API unavailable" in str(result["api_error"])
    mock_client_cls.return_value.__enter__.assert_called_once()
    mock_client_cls.return_value.__exit__.assert_called_once()


@patch("src.frontend.services.dashboard_service.get_dataset_path")
@patch("src.frontend.services.dashboard_service._get_cached_dashboard")
def test_dashboard_uses_cache(mock_cache, mock_get_path):
    """Dashboard returns cached data if available."""
    dataset_path = "/fake/path/dataset.csv"
    mock_get_path.return_value = dataset_path

    cached_data = {
        "dataset_loaded": True,
        "source": "api",
        "rows": 100,
        "columns": 10,
        "api_status": {"success": True},
        "backend_report": {"foo": "bar"},
        "ai_report": {"baz": "qux"},
        "execution_time": 0.5,
        "output_path": "cached_report.txt",
        "dataframe": pd.DataFrame({"x": [1, 2, 3]}),
    }
    mock_cache.return_value = cached_data

    with patch("streamlit.session_state", {}):
        result = get_dashboard_data()

    # Should return the cached data (with metadata deep-copied)
    assert result["source"] == "api"
    assert result["rows"] == 100
    assert result["columns"] == 10
    assert result["execution_time"] == 0.5
    assert result["output_path"] == "cached_report.txt"
    assert result["api_status"] == {"success": True}
    assert result["backend_report"] == {"foo": "bar"}
    assert result["ai_report"] == {"baz": "qux"}
    assert result["dataframe"] is not None
    mock_cache.assert_called_once_with(dataset_path)