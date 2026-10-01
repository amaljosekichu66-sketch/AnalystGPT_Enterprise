"""
Unit tests for the Dashboard Service.
"""

from unittest.mock import MagicMock, patch

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
# Read-only API tests (P2-06)
# ==========================================================

DATASET = "0b7c1f2e-3d4a-4b5c-8d9e-0f1a2b3c4d5e"


@pytest.fixture(autouse=True)
def clean_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


@pytest.fixture
def api(uploaded_file, sample_dataframe):
    with (
        patch("src.frontend.services.dashboard_service.get_dataset", return_value=(uploaded_file, sample_dataframe)),
        patch("src.frontend.services.dashboard_service.get_dataset_version_id", return_value=DATASET),
        patch("src.frontend.services.dashboard_service.APIClient") as client_cls,
    ):
        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client
        client.dataset_analysis.return_value = {"dataset_version_id": DATASET, "visualization_plan": {}, "profile": {}}
        client.powerbi_dashboard.return_value = {
            "success": True,
            "report": {"title": "r"},
            "ai_job_id": "job_42",
            "pipeline_run_id": 7,
            "report_id": 9,
        }
        yield client


def test_viewing_the_dashboard_never_runs_the_pipeline(api) -> None:
    data = get_dashboard_data()

    api.run_pipeline.assert_not_called()
    api.run_pipeline_for.assert_not_called()
    assert data["analysed"] is True
    assert data["ai_job_id"] == "job_42" and data["report_id"] == 9
    assert st.session_state["ai_job_id"] == "job_42"


def test_not_yet_analysed_dataset_is_reported_as_such(api) -> None:
    api.powerbi_dashboard.side_effect = RuntimeError("Backend returned HTTP 404: No pipeline result")

    data = get_dashboard_data()

    assert data["analysed"] is False and data["api_error"] is None
    api.run_pipeline.assert_not_called()


def test_api_down_gives_a_readable_message(api) -> None:
    api.powerbi_dashboard.side_effect = RuntimeError("Unable to connect to backend: refused")

    data = get_dashboard_data()

    assert data["api_error"] == "The analytics service is not reachable right now. Please try again shortly."


def test_successful_dashboard_is_cached(api) -> None:
    get_dashboard_data()
    get_dashboard_data()
    assert api.powerbi_dashboard.call_count == 1


def test_clear_dashboard_cache(api) -> None:
    get_dashboard_data()
    clear_dashboard_cache()
    get_dashboard_data()
    assert api.powerbi_dashboard.call_count == 2
