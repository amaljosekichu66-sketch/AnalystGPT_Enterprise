"""
Unit tests for the Report Service (frontend).
"""

from unittest.mock import MagicMock, patch

import httpx
import pandas as pd
import pytest

from src.frontend.services.report_service import (
    _local_report_data,
    get_report_data,
)

# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        }
    )


@pytest.fixture
def uploaded_file():
    file = MagicMock()
    file.name = "employees.csv"
    return file


# ==========================================================
# Local Report Data
# ==========================================================


@patch("src.frontend.services.report_service.get_dataset")
def test_local_report_without_dataset(mock_get_dataset):
    mock_get_dataset.return_value = (None, None)
    result = _local_report_data()
    assert result["dataset_loaded"] is False
    assert result["filename"] is None
    assert result["reports"] == []
    assert result["dataframe"] is None
    assert result["source"] == "session"


@patch("src.frontend.services.report_service.get_dataset")
def test_local_report_with_dataset(mock_get_dataset, uploaded_file, sample_dataframe):
    mock_get_dataset.return_value = (uploaded_file, sample_dataframe)
    result = _local_report_data()
    assert result["dataset_loaded"] is True
    assert result["filename"] == "employees.csv"
    assert result["dataframe"].equals(sample_dataframe)
    # The actual number of reports has grown; check at least 5.
    assert len(result["reports"]) >= 5
    assert "Dataset Summary" in result["reports"]
    assert "Quality Report" in result["reports"]
    assert "Analytics Report" in result["reports"]
    assert "Column Profile" in result["reports"]
    assert "Correlation Analysis" in result["reports"]
    assert result["source"] == "session"


# ==========================================================
# API Success
# ==========================================================


@patch("src.frontend.services.report_service.APIClient")
@patch("src.frontend.services.report_service._local_report_data")
@patch("src.frontend.services.session_manager.get_dataset_path")
def test_report_api_success(mock_get_path, mock_local, mock_client):
    # Force a dataset path so the service attempts the API
    mock_get_path.return_value = "/fake/path/dataset.csv"
    # Return local report with dataset_loaded=True and include "reports"
    mock_local.return_value = {
        "dataset_loaded": True,
        "source": "session",
        "reports": [],
    }

    client = MagicMock()
    # The service calls client.get_reports()
    client.get_reports.return_value = {
        "success": True,
        "data": {
            "reports": [],
            "report": {},
            "ai_report": {},
            "execution_time": 1.0,
            "output_path": "reports/report.txt",
        },
    }
    mock_client.return_value.__enter__.return_value = client

    result = get_report_data()
    assert result["source"] == "api"
    assert result["api_status"]["success"] is True
    client.get_reports.assert_called_once()
    mock_client.return_value.__enter__.assert_called_once()
    mock_client.return_value.__exit__.assert_called_once()


# ==========================================================
# API Failure
# ==========================================================


@patch("src.frontend.services.report_service.APIClient")
@patch("src.frontend.services.report_service._local_report_data")
@patch("src.frontend.services.session_manager.get_dataset_path")
def test_report_api_failure(mock_get_path, mock_local, mock_client):
    mock_get_path.return_value = "/fake/path/dataset.csv"
    mock_local.return_value = {
        "dataset_loaded": True,
        "source": "session",
    }

    client = MagicMock()
    client.get_reports.side_effect = OSError()
    mock_client.return_value.__enter__.return_value = client

    result = get_report_data()
    assert result["source"] == "session"
    mock_client.return_value.__enter__.assert_called_once()
    mock_client.return_value.__exit__.assert_called_once()


# ==========================================================
# HTTP Error
# ==========================================================


@patch("src.frontend.services.report_service.APIClient")
@patch("src.frontend.services.report_service._local_report_data")
@patch("src.frontend.services.session_manager.get_dataset_path")
def test_report_http_error(mock_get_path, mock_local, mock_client):
    mock_get_path.return_value = "/fake/path/dataset.csv"
    mock_local.return_value = {
        "dataset_loaded": True,
        "source": "session",
    }

    client = MagicMock()
    client.get_reports.side_effect = httpx.HTTPError("API unavailable")
    mock_client.return_value.__enter__.return_value = client

    result = get_report_data()
    assert result["source"] == "session"
    mock_client.return_value.__enter__.assert_called_once()
    mock_client.return_value.__exit__.assert_called_once()


# ==========================================================
# Cache Tests
# ==========================================================


def test_clear_reports_cache():
    """Test clearing the reports cache."""
    import streamlit as st

    from src.frontend.services.report_service import clear_reports_cache

    with patch("streamlit.session_state", {"reports_cache": "data", "reports_dataset": "path"}):
        clear_reports_cache()
        assert "reports_cache" not in st.session_state
        assert "reports_dataset" not in st.session_state


@patch("src.frontend.services.report_service.get_dataset_path")
@patch("src.frontend.services.report_service._get_cached_reports")
def test_report_uses_cache(mock_cache, mock_get_path):
    """Reports service returns cached data when available."""
    dataset_path = "/fake/path/dataset.csv"
    mock_get_path.return_value = dataset_path

    cached_data = {
        "dataset_loaded": True,
        "source": "api",
        "reports": ["Dataset Summary", "Quality Report"],
        "api_status": {"success": True},
        "report": {"summary": "Cached summary"},
        "ai_report": {"executive_summary": "AI Cached"},
    }
    mock_cache.return_value = cached_data

    with patch("streamlit.session_state", {}):
        result = get_report_data()

    assert result["source"] == "api"
    assert result["reports"] == ["Dataset Summary", "Quality Report"]
    assert result["report"] == {"summary": "Cached summary"}
    assert result["ai_report"] == {"executive_summary": "AI Cached"}
    mock_cache.assert_called_once_with(dataset_path)


# ==========================================================
# Export Service Tests
# ==========================================================


def test_export_text_and_pdf_report_service():
    """
    Exercise the local-orchestrator fallback with the REST path explicitly
    unavailable.

    The REST branch is stubbed rather than left to chance: previously this test
    made a real connection attempt to the API port, so it exercised a different
    code path depending on whether a dev server happened to be running.
    """
    from src.frontend.services.report_service import export_pdf_report, export_text_report

    with (
        patch("streamlit.session_state", {}),
        patch(
            "src.frontend.services.report_service.APIClient",
            side_effect=httpx.ConnectError("API server not running (simulated)"),
        ) as mock_client,
    ):
        text_res = export_text_report()
        assert "success" in text_res
        assert "message" in text_res

        pdf_res = export_pdf_report()
        assert "success" in pdf_res
        assert "message" in pdf_res

    # Prove the REST path was attempted and that the fallback is what answered.
    assert mock_client.call_count == 2
