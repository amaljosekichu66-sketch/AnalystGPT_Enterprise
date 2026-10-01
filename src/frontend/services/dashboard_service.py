"""
Dashboard service for AnalystGPT Enterprise.

Read-only (P2-06): viewing the dashboard never runs the pipeline. It used to
call POST /api/pipeline on every cache miss, throw the response away, and
then read the dashboard - so each visit created a pipeline run, and VIEWERs
got a 403 before they saw anything. The pipeline now runs only from the
Upload page's "Run analysis" button.

The dashboard reads GET /api/powerbi/dashboard for the active dataset and
GET /api/datasets/{id}/analysis for its charts and profile. The AI job shown
is the one of the run on screen (`ai_job_id` in the dashboard response), not
the user's latest job, which may belong to another dataset.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd
import streamlit as st

from src.core.logger import logger
from src.frontend.services.api_client import APIClient
from src.frontend.services.errors import friendly_error, http_status
from src.frontend.services.session_manager import (
    ANALYSIS_KEY,
    get_ai_report,
    get_dataset,
    get_dataset_version_id,
    set_ai_job_id,
    set_ai_report,
)

_EMPTY_DASHBOARD: dict[str, Any] = {
    "dataset_loaded": False,
    "analysed": False,
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
    "ai_job_id": None,
    "pipeline_run_id": None,
    "report_id": None,
    "analysis": None,
    "api_status": None,
    "api_error": None,
    "source": "session",
}

_CACHE_KEY = "dashboard_cache"
_CACHE_DATASET = "dashboard_dataset"


def clear_dashboard_cache() -> None:
    """Forget the cached dashboard (a new upload or a new run)."""
    st.session_state.pop(_CACHE_KEY, None)
    st.session_state.pop(_CACHE_DATASET, None)


@st.cache_data(show_spinner=False, max_entries=8, ttl=3600)
def _calculate_dashboard_metrics(dataframe: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "memory": dataframe.memory_usage(deep=True).sum() / (1024 * 1024),
        "missing": int(dataframe.isna().sum().sum()),
        "duplicates": int(dataframe.duplicated().sum()),
        "numeric_columns": dataframe.select_dtypes(include="number").shape[1],
        "categorical_columns": dataframe.select_dtypes(exclude="number").shape[1],
    }


def _local_dashboard_data() -> dict[str, Any]:
    uploaded_file, dataframe = get_dataset()
    if dataframe is None:
        return deepcopy(_EMPTY_DASHBOARD)
    return {
        **deepcopy(_EMPTY_DASHBOARD),
        "dataset_loaded": True,
        "filename": uploaded_file.name if uploaded_file else None,
        "dataframe": dataframe,
        "ai_report": get_ai_report(),
        **_calculate_dashboard_metrics(dataframe),
    }


def _analysis(client: APIClient, dataset_version_id: str) -> dict[str, Any] | None:
    cached = st.session_state.get(ANALYSIS_KEY)
    if isinstance(cached, dict) and cached.get("dataset_version_id") == dataset_version_id:
        return cached
    analysis = client.dataset_analysis(dataset_version_id)
    st.session_state[ANALYSIS_KEY] = analysis
    return analysis


def get_dashboard_data() -> dict[str, Any]:
    """Dashboard data for the active dataset. Never executes the pipeline."""
    dataset_version_id = get_dataset_version_id()
    dashboard = _local_dashboard_data()
    if not dataset_version_id or not dashboard["dataset_loaded"]:
        return dashboard

    if st.session_state.get(_CACHE_DATASET) == dataset_version_id and st.session_state.get(_CACHE_KEY):
        cached = dict(st.session_state[_CACHE_KEY])
        cached["dataframe"] = dashboard["dataframe"]
        cached["ai_report"] = get_ai_report() or cached.get("ai_report")
        return cached

    try:
        with APIClient() as client:
            dashboard["analysis"] = _analysis(client, dataset_version_id)
            response = client.powerbi_dashboard(dataset_version_id)
    except Exception as exc:
        if http_status(exc) == 404:
            # Uploaded but not analysed yet: say so instead of running it.
            dashboard["api_error"] = None
            return dashboard
        dashboard["api_error"] = friendly_error(exc, "dashboard")
        return dashboard

    dashboard.update(
        {
            "analysed": True,
            "api_status": response,
            "source": "api",
            "backend_report": response.get("report", {}),
            "execution_time": response.get("execution_time"),
            "output_path": response.get("output_path"),
            "ai_job_id": response.get("ai_job_id"),
            "pipeline_run_id": response.get("pipeline_run_id"),
            "report_id": response.get("report_id"),
        }
    )
    if response.get("ai_job_id"):
        set_ai_job_id(response["ai_job_id"])
    if response.get("ai_report"):
        set_ai_report(response["ai_report"])
        dashboard["ai_report"] = response["ai_report"]

    if response.get("success", False):
        st.session_state[_CACHE_DATASET] = dataset_version_id
        st.session_state[_CACHE_KEY] = {k: v for k, v in dashboard.items() if k != "dataframe"}
        logger.info("Dashboard data cached for dataset %s.", dataset_version_id)
    return dashboard
