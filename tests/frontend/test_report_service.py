"""
Unit tests for the Report Service.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

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
    """
    Sample dataframe.
    """

    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": [
                "Alice",
                "Bob",
                "Charlie",
            ],
        }
    )


@pytest.fixture
def uploaded_file():
    """
    Mock uploaded file.
    """

    file = MagicMock()

    file.name = "employees.csv"

    return file


# ==========================================================
# Local Report Data
# ==========================================================


@patch(
    "src.frontend.services.report_service.get_dataset",
)
def test_local_report_without_dataset(
    mock_get_dataset,
):
    """
    Local report with no dataset.
    """

    mock_get_dataset.return_value = (
        None,
        None,
    )

    result = _local_report_data()

    assert result["dataset_loaded"] is False
    assert result["filename"] is None
    assert result["reports"] == []
    assert result["dataframe"] is None
    assert result["source"] == "session"


@patch(
    "src.frontend.services.report_service.get_dataset",
)
def test_local_report_with_dataset(
    mock_get_dataset,
    uploaded_file,
    sample_dataframe,
):
    """
    Local report with dataset.
    """

    mock_get_dataset.return_value = (
        uploaded_file,
        sample_dataframe,
    )

    result = _local_report_data()

    assert result["dataset_loaded"] is True
    assert result["filename"] == "employees.csv"

    assert result["dataframe"].equals(
        sample_dataframe,
    )

    assert len(result["reports"]) == 5

    assert "Dataset Summary" in result["reports"]
    assert "Quality Report" in result["reports"]
    assert "Analytics Report" in result["reports"]
    assert "Column Profile" in result["reports"]
    assert "Correlation Analysis" in result["reports"]

    assert result["source"] == "session"


# ==========================================================
# API Success
# ==========================================================


@patch(
    "src.frontend.services.report_service.APIClient",
)
@patch(
    "src.frontend.services.report_service._local_report_data",
)
def test_report_api_success(
    mock_local,
    mock_client,
):
    """
    Report service uses API successfully.
    """

    mock_local.return_value = {
        "dataset_loaded": True,
        "source": "session",
    }

    client = MagicMock()

    client.reports.return_value = {
        "success": True,
    }

    mock_client.return_value.__enter__.return_value = client

    result = get_report_data()

    assert result["source"] == "api"

    assert result["api_status"]["success"] is True

    client.reports.assert_called_once()

    mock_client.return_value.__enter__.assert_called_once()

    mock_client.return_value.__exit__.assert_called_once()


# ==========================================================
# API Failure
# ==========================================================


@patch(
    "src.frontend.services.report_service.APIClient",
)
@patch(
    "src.frontend.services.report_service._local_report_data",
)
def test_report_api_failure(
    mock_local,
    mock_client,
):
    """
    Report service falls back to session.
    """

    mock_local.return_value = {
        "dataset_loaded": False,
        "source": "session",
    }

    client = MagicMock()

    client.reports.side_effect = OSError()

    mock_client.return_value.__enter__.return_value = client

    result = get_report_data()

    assert result["source"] == "session"

    mock_client.return_value.__enter__.assert_called_once()

    mock_client.return_value.__exit__.assert_called_once()


# ==========================================================
# HTTP Error
# ==========================================================


@patch(
    "src.frontend.services.report_service.APIClient",
)
@patch(
    "src.frontend.services.report_service._local_report_data",
)
def test_report_http_error(
    mock_local,
    mock_client,
):
    """
    HTTP errors fall back to session.
    """

    mock_local.return_value = {
        "dataset_loaded": False,
        "source": "session",
    }

    client = MagicMock()

    client.reports.side_effect = httpx.HTTPError(
        "API unavailable",
    )

    mock_client.return_value.__enter__.return_value = client

    result = get_report_data()

    assert result["source"] == "session"

    mock_client.return_value.__enter__.assert_called_once()

    mock_client.return_value.__exit__.assert_called_once()