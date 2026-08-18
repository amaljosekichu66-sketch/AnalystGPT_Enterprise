"""
Unit tests for the Session Manager.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pandas as pd

from src.frontend.services import session_manager


# ==========================================================
# Fixtures
# ==========================================================


def create_dataframe() -> pd.DataFrame:
    """
    Create a sample dataframe.
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


# ==========================================================
# Store Dataset
# ==========================================================


@patch("streamlit.session_state", new_callable=dict)
def test_store_dataset(mock_session_state):
    """
    Test storing a dataset.
    """

    dataframe = create_dataframe()

    uploaded_file = MagicMock()

    uploaded_file.name = "employees.csv"

    session_manager.store_dataset(
        uploaded_file,
        dataframe,
    )

    assert (
        mock_session_state[
            session_manager.UPLOADED_FILE_KEY
        ]
        == uploaded_file
    )

    assert (
        mock_session_state[
            session_manager.DATAFRAME_KEY
        ]
        is dataframe
    )


# ==========================================================
# Get DataFrame
# ==========================================================


@patch("streamlit.session_state", new_callable=dict)
def test_get_dataframe(mock_session_state):
    """
    Test retrieving dataframe.
    """

    dataframe = create_dataframe()

    mock_session_state[
        session_manager.DATAFRAME_KEY
    ] = dataframe

    result = session_manager.get_dataframe()

    assert result is dataframe


# ==========================================================
# Get Uploaded File
# ==========================================================


@patch("streamlit.session_state", new_callable=dict)
def test_get_uploaded_file(mock_session_state):
    """
    Test retrieving uploaded file.
    """

    uploaded_file = MagicMock()

    uploaded_file.name = "employees.csv"

    mock_session_state[
        session_manager.UPLOADED_FILE_KEY
    ] = uploaded_file

    result = session_manager.get_uploaded_file()

    assert result == uploaded_file


# ==========================================================
# Has Dataset
# ==========================================================


@patch("streamlit.session_state", new_callable=dict)
def test_has_dataset_true(mock_session_state):
    """
    Test dataset exists.
    """

    dataframe = create_dataframe()

    mock_session_state[
        session_manager.DATAFRAME_KEY
    ] = dataframe

    assert session_manager.has_dataset() is True


@patch("streamlit.session_state", new_callable=dict)
def test_has_dataset_false(mock_session_state):
    """
    Test dataset does not exist.
    """

    assert session_manager.has_dataset() is False


# ==========================================================
# Clear Dataset
# ==========================================================


@patch("streamlit.session_state", new_callable=dict)
def test_clear_dataset(mock_session_state):
    """
    Test clearing stored dataset.
    """

    dataframe = create_dataframe()

    uploaded_file = MagicMock()

    mock_session_state[
        session_manager.DATAFRAME_KEY
    ] = dataframe

    mock_session_state[
        session_manager.UPLOADED_FILE_KEY
    ] = uploaded_file

    session_manager.clear_dataset()

    assert (
        session_manager.DATAFRAME_KEY
        not in mock_session_state
    )

    assert (
        session_manager.UPLOADED_FILE_KEY
        not in mock_session_state
    )


# ==========================================================
# Empty Session
# ==========================================================


@patch("streamlit.session_state", new_callable=dict)
def test_clear_empty_session(mock_session_state):
    """
    Clearing an empty session should not fail.
    """

    session_manager.clear_dataset()

    assert mock_session_state == {}


# ==========================================================
# Cache Invalidation Tests
# ==========================================================


@patch("streamlit.session_state", new_callable=dict)
def test_store_dataset_invalidates_caches(mock_session_state):
    """
    Storing a new dataset must clear existing dashboard and report caches.
    """
    mock_session_state["dashboard_cache"] = {"data": 1}
    mock_session_state["dashboard_dataset"] = "/old/path.csv"
    mock_session_state["reports_cache"] = {"reports": 1}
    mock_session_state["reports_dataset"] = "/old/path.csv"

    dataframe = create_dataframe()
    uploaded_file = MagicMock()
    uploaded_file.name = "new_data.csv"

    session_manager.store_dataset(uploaded_file, dataframe, "/new/path.csv")

    assert "dashboard_cache" not in mock_session_state
    assert "dashboard_dataset" not in mock_session_state
    assert "reports_cache" not in mock_session_state
    assert "reports_dataset" not in mock_session_state
    assert mock_session_state[session_manager.DATASET_PATH_KEY] == "/new/path.csv"


@patch("streamlit.session_state", new_callable=dict)
def test_store_pipeline_result_invalidates_caches(mock_session_state):
    """
    Storing a new pipeline result must clear dashboard and report caches so fresh data is loaded.
    """
    mock_session_state["dashboard_cache"] = {"old": True}
    mock_session_state["reports_cache"] = {"old": True}

    mock_result = MagicMock()
    session_manager.store_pipeline_result(mock_result)

    assert "dashboard_cache" not in mock_session_state
    assert "reports_cache" not in mock_session_state
    assert mock_session_state[session_manager.PIPELINE_RESULT_KEY] is mock_result