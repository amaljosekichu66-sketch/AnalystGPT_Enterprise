"""
Dashboard service for AnalystGPT Enterprise.

Provides dashboard information using the REST API when available,
with automatic fallback to the local Streamlit session.

The service caches successful dashboard data in st.session_state to avoid
repeating expensive backend calls during the same session.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import httpx
import pandas as pd
import streamlit as st

from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import (
    get_dataset,
    get_dataset_path,
)
from src.core.logger import logger


# ==========================================================
# Constants
# ==========================================================

_EMPTY_DASHBOARD: dict[str, Any] = {
    "dataset_loaded": False,
    "filename": None,
    "rows": 0,
    "columns": 0,
    "memory": 0.0,
    "missing": 0,
    "duplicates": 0,
    "numeric_columns": 0,
    "categorical_columns": 0,
    "execution_time": None,
    "output_path": None,
    "dataframe": None,
    "backend_report": {},
    "ai_report": None,
    "api_status": None,
    "api_error": None,
    "source": "session",
}


# ==========================================================
# Dashboard Cache (Session‑Level)
# ==========================================================

_CACHE_KEY = "dashboard_cache"
_CACHE_DATASET = "dashboard_dataset"


def _deepcopy_metadata(dashboard: dict[str, Any]) -> dict[str, Any]:
    """
    Return a shallow copy of the dashboard with deep copies of mutable
    metadata fields (backend_report, api_status, ai_report) to prevent
    accidental sharing. The DataFrame is kept as a reference (shared).
    """
    copy_dict = dashboard.copy()
    # Deep-copy nested dictionaries that might be mutated elsewhere
    copy_dict["backend_report"] = deepcopy(dashboard.get("backend_report", {}))
    copy_dict["api_status"] = deepcopy(dashboard.get("api_status"))
    copy_dict["ai_report"] = deepcopy(dashboard.get("ai_report"))
    return copy_dict


def _get_cached_dashboard(
    dataset_path: str,
) -> dict[str, Any] | None:
    """
    Retrieve a cached dashboard if it matches the given dataset path.
    Returns a shallow copy with deep-copied metadata to prevent mutation.
    """
    if st.session_state.get(_CACHE_DATASET) != dataset_path:
        return None

    cached = st.session_state.get(_CACHE_KEY)
    if cached is None:
        return None

    return _deepcopy_metadata(cached)


def _cache_dashboard(
    dataset_path: str,
    dashboard: dict[str, Any],
) -> None:
    """
    Store a copy of the dashboard in the session cache.
    The DataFrame is shared (not copied), but metadata is deep-copied.
    """
    st.session_state[_CACHE_DATASET] = dataset_path
    st.session_state[_CACHE_KEY] = _deepcopy_metadata(dashboard)


def clear_dashboard_cache() -> None:
    """
    Clear the cached dashboard data.
    Should be called when a new dataset is uploaded.
    """
    st.session_state.pop(_CACHE_KEY, None)
    st.session_state.pop(_CACHE_DATASET, None)


# ==========================================================
# Local Dashboard Metrics
# ==========================================================

@st.cache_data(show_spinner=False)
def _calculate_dashboard_metrics(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:

    numeric_columns = dataframe.select_dtypes(
        include="number",
    ).shape[1]

    categorical_columns = dataframe.select_dtypes(
        exclude="number",
    ).shape[1]

    return {
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "memory": (
            dataframe.memory_usage(
                deep=True,
            ).sum()
            / (1024 * 1024)
        ),
        "missing": int(
            dataframe.isna().sum().sum()
        ),
        "duplicates": int(
            dataframe.duplicated().sum()
        ),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
    }


# ==========================================================
# Local Session
# ==========================================================

def _local_dashboard_data() -> dict[str, Any]:

    uploaded_file, dataframe = get_dataset()

    if dataframe is None:
        return deepcopy(_EMPTY_DASHBOARD)

    metrics = _calculate_dashboard_metrics(dataframe)

    return {
        "dataset_loaded": True,
        "filename": uploaded_file.name if uploaded_file else None,
        "execution_time": None,
        "output_path": None,
        "dataframe": dataframe,
        "backend_report": {},
        "ai_report": None,
        "api_status": None,
        "api_error": None,
        "source": "session",
        **metrics,
    }


# ==========================================================
# AI Extraction
# ==========================================================

def _extract_ai_report(
    payload: dict[str, Any],
) -> dict[str, Any] | None:

    if not payload:
        return None

    return payload.get("ai_report")


# ==========================================================
# Dashboard Service
# ==========================================================

def get_dashboard_data() -> dict[str, Any]:

    dataset_path = get_dataset_path()

    logger.info("=" * 80)
    logger.info("FRONTEND DASHBOARD SERVICE")
    logger.info("=" * 80)
    logger.info("Dataset Path : %s", dataset_path)

    if not dataset_path:
        logger.info("No dataset selected. Returning local session data.")
        return _local_dashboard_data()

    # ----------------------------------------------------------
    # 1. Check session cache (only successful responses)
    # ----------------------------------------------------------

    cached = _get_cached_dashboard(dataset_path)
    if cached is not None:
        logger.info("Using cached dashboard data (no backend call).")
        return cached

    # ----------------------------------------------------------
    # 2. Build from local session (fallback before API)
    # ----------------------------------------------------------

    dashboard = _local_dashboard_data()

    if not dashboard["dataset_loaded"]:
        logger.warning("Dataset not loaded locally; returning empty dashboard.")
        return dashboard

    # ----------------------------------------------------------
    # 3. Try to fetch from backend API
    # ----------------------------------------------------------

    try:
        logger.info("Calling backend API for dashboard data...")

        with APIClient(timeout=180) as client:
            response = client.powerbi_dashboard(dataset_path)

        logger.info("Backend response received successfully.")

        # Populate dashboard from API response
        dashboard["api_status"] = response
        dashboard["source"] = "api"
        dashboard["backend_report"] = response.get("report", {})
        dashboard["ai_report"] = _extract_ai_report(response)
        dashboard["execution_time"] = response.get("execution_time")
        dashboard["output_path"] = response.get("output_path")

        # ----------------------------------------------------------
        # 4. Cache ONLY successful responses
        # ----------------------------------------------------------

        if response.get("success", False):
            _cache_dashboard(dataset_path, dashboard)
            logger.info("Dashboard data cached for future requests.")
        else:
            logger.warning(
                "Backend returned unsuccessful response. Not caching."
            )

        return dashboard

    except httpx.ReadTimeout:
        dashboard["api_error"] = "Backend request timed out."
        logger.warning(
            "Backend request timed out. Falling back to local session (not cached)."
        )
        return dashboard

    except httpx.HTTPError as exc:
        dashboard["api_error"] = str(exc)
        logger.error("HTTP error: %s", exc)
        return dashboard

    except Exception as exc:
        dashboard["api_error"] = str(exc)
        logger.exception("Unexpected error in dashboard service")
        return dashboard