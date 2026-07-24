"""
Dashboard service for AnalystGPT Enterprise.

Provides dashboard information using the REST API when available,
with automatic fallback to the local Streamlit session.
"""

from __future__ import annotations

from typing import Any

import httpx
import pandas as pd
import streamlit as st

from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import get_dataset


@st.cache_data(show_spinner=False)
def _calculate_dashboard_metrics(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Compute dashboard metrics.

    Cached automatically by Streamlit.
    """

    numeric_columns = dataframe.select_dtypes(
        include="number",
    ).shape[1]

    categorical_columns = dataframe.select_dtypes(
        exclude="number",
    ).shape[1]

    return {
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "memory": dataframe.memory_usage(deep=True).sum()
        / (1024 * 1024),
        "missing": int(
            dataframe.isna().sum().sum()
        ),
        "duplicates": int(
            dataframe.duplicated().sum()
        ),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
    }


def _local_dashboard_data() -> dict[str, Any]:
    """
    Build dashboard information from the local session.
    """

    uploaded_file, dataframe = get_dataset()

    if dataframe is None:
        return {
            "dataset_loaded": False,
            "filename": None,
            "rows": 0,
            "columns": 0,
            "memory": 0.0,
            "missing": 0,
            "duplicates": 0,
            "numeric_columns": 0,
            "categorical_columns": 0,
            "dataframe": None,
            "source": "session",
        }

    metrics = _calculate_dashboard_metrics(
        dataframe,
    )

    return {
        "dataset_loaded": True,
        "filename": (
            uploaded_file.name
            if uploaded_file
            else None
        ),
        "dataframe": dataframe,
        "source": "session",
        **metrics,
    }


def get_dashboard_data() -> dict[str, Any]:
    """
    Return dashboard data.

    Uses REST API when available and falls back to
    the current Streamlit session.
    """

    try:

        with APIClient() as client:

            api_response = client.dashboard()

        dashboard_data = _local_dashboard_data()

        dashboard_data["api_status"] = api_response

        dashboard_data["source"] = "api"

        return dashboard_data

    except (
        httpx.HTTPError,
        ConnectionError,
        TimeoutError,
        OSError,
    ):

        return _local_dashboard_data()