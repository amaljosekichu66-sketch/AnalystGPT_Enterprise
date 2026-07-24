"""
Unit tests for the Dashboard Service.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import httpx
import pandas as pd
import pytest

from src.frontend.services.dashboard_service import (
    _local_dashboard_data,
    get_dashboard_data,
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
            "id": [1, 2, 2],
            "name": [
                "Alice",
                "Bob",
                "Bob",
            ],
            "salary": [
                100,
                200,
                None,
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
# Local Dashboard
# ==========================================================


@patch(
    "src.frontend.services.dashboard_service.get_dataset",
)
def test_local_dashboard_without_dataset(
    mock_get_dataset,
):
    """
    Local dashboard with no dataset.
    """

    mock_get_dataset.return_value = (
        None,
        None,
    )

    result = _local_dashboard_data()

    assert result["dataset_loaded"] is False
    assert result["filename"] is None
    assert result["rows"] == 0
    assert result["columns"] == 0
    assert result["source"] == "session"


@patch(
    "src.frontend.services.dashboard_service.get_dataset",
)
def test_local_dashboard_with_dataset(
    mock_get_dataset,
    uploaded_file,
    sample_dataframe,
):
    """
    Local dashboard with dataset.
    """

    mock_get_dataset.return_value = (
        uploaded_file,
        sample_dataframe,
    )

    result = _local_dashboard_data()

    assert result["dataset_loaded"] is True
    assert result["filename"] == "employees.csv"
    assert result["rows"] == 3
    assert result["columns"] == 3
    assert result["missing"] == 1

    # duplicated() compares complete rows.
    # Salary differs, so there are no duplicate rows.
    assert result["duplicates"] == 0

    assert result["numeric_columns"] == 2
    assert result["categorical_columns"] == 1
    assert result["source"] == "session"


# ==========================================================
# API Success
# ==========================================================


@patch(
    "src.frontend.services.dashboard_service.APIClient",
)
@patch(
    "src.frontend.services.dashboard_service._local_dashboard_data",
)
def test_dashboard_api_success(
    mock_local,
    mock_client,
):
    """
    Dashboard uses API successfully.
    """

    mock_local.return_value = {
        "dataset_loaded": True,
        "source": "session",
    }

    client = MagicMock()

    client.dashboard.return_value = {
        "success": True,
    }

    mock_client.return_value.__enter__.return_value = client

    result = get_dashboard_data()

    assert result["source"] == "api"
    assert result["api_status"]["success"] is True

    client.dashboard.assert_called_once()

    mock_client.return_value.__enter__.assert_called_once()
    mock_client.return_value.__exit__.assert_called_once()


# ==========================================================
# API Failure
# ==========================================================


@patch(
    "src.frontend.services.dashboard_service.APIClient",
)
@patch(
    "src.frontend.services.dashboard_service._local_dashboard_data",
)
def test_dashboard_api_failure(
    mock_local,
    mock_client,
):
    """
    Dashboard falls back to session.
    """

    mock_local.return_value = {
        "dataset_loaded": False,
        "source": "session",
    }

    client = MagicMock()

    client.dashboard.side_effect = OSError()

    mock_client.return_value.__enter__.return_value = client

    result = get_dashboard_data()

    assert result["source"] == "session"

    mock_client.return_value.__enter__.assert_called_once()
    mock_client.return_value.__exit__.assert_called_once()


# ==========================================================
# API HTTP Error
# ==========================================================


@patch(
    "src.frontend.services.dashboard_service.APIClient",
)
@patch(
    "src.frontend.services.dashboard_service._local_dashboard_data",
)
def test_dashboard_http_error(
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

    client.dashboard.side_effect = httpx.HTTPError(
        "API unavailable",
    )

    mock_client.return_value.__enter__.return_value = client

    result = get_dashboard_data()

    assert result["source"] == "session"

    mock_client.return_value.__enter__.assert_called_once()
    mock_client.return_value.__exit__.assert_called_once()