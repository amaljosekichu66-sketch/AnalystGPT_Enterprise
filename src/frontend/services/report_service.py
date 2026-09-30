"""
Report service for AnalystGPT Enterprise.

Sprint 11
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import httpx
import pandas as pd
import streamlit as st

from src.core.logger import logger
from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import (
    get_auth_token,
    get_dataset,
    get_dataset_version_id,
)

# ==========================================================
# Reports Cache (Session-Level)
# ==========================================================

_REPORTS_CACHE_KEY = "reports_cache"
_REPORTS_DATASET_KEY = "reports_dataset"


def _get_cached_reports(
    dataset_version_id: str | None,
) -> dict[str, Any] | None:
    """
    Retrieve cached report data if valid for the current dataset.
    """
    if not dataset_version_id:
        return None

    if st.session_state.get(_REPORTS_DATASET_KEY) != dataset_version_id:
        return None

    cached = st.session_state.get(_REPORTS_CACHE_KEY)
    if cached is None:
        return None

    return deepcopy(cached)


def _cache_reports(
    dataset_version_id: str | None,
    report_data: dict[str, Any],
) -> None:
    """
    Cache successful report data in session state.
    """
    if not dataset_version_id:
        return

    st.session_state[_REPORTS_DATASET_KEY] = dataset_version_id
    st.session_state[_REPORTS_CACHE_KEY] = deepcopy(report_data)


def clear_reports_cache() -> None:
    """
    Clear cached report data.
    """
    st.session_state.pop(_REPORTS_CACHE_KEY, None)
    st.session_state.pop(_REPORTS_DATASET_KEY, None)


# ==========================================================
# Local Reports
# ==========================================================


@st.cache_data(show_spinner=False)
def _generate_reports(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Generate locally available report names.
    """

    reports = [
        "Dataset Summary",
        "Quality Report",
        "Analytics Report",
        "Column Profile",
        "AI Executive Summary",
        "AI Recommendations",
        "AI Explanations",
        "AI Narrative",
    ]

    if not dataframe.select_dtypes(
        include="number",
    ).empty:

        reports.append("Correlation Analysis")

    return reports


# ==========================================================
# Local Session
# ==========================================================


def _local_report_data() -> dict[str, Any]:
    """
    Build report information from the
    current Streamlit session.
    """

    uploaded_file, dataframe = get_dataset()

    if dataframe is None:

        return {
            "dataset_loaded": False,
            "filename": None,
            "reports": [],
            "dataframe": None,
            "report": None,
            "ai_report": None,
            "execution_time": None,
            "output_path": None,
            "api_status": None,
            "api_error": None,
            "source": "session",
        }

    return {
        "dataset_loaded": True,
        "filename": (uploaded_file.name if uploaded_file else None),
        "reports": _generate_reports(
            dataframe,
        ),
        "dataframe": dataframe,
        "report": None,
        "ai_report": None,
        "execution_time": None,
        "output_path": None,
        "api_status": None,
        "api_error": None,
        "source": "session",
    }


# ==========================================================
# Report Retrieval
# ==========================================================


def get_report_data() -> dict[str, Any]:
    """
    Retrieve report information.

    Uses session-level cache to avoid repeated backend calls.
    Falls back to the local session when the REST API is unavailable.
    """
    dataset_version_id = get_dataset_version_id()

    cached = _get_cached_reports(dataset_version_id)
    if cached is not None:
        return cached

    report_data = _local_report_data()

    try:

        with APIClient() as client:

            api_response = client.get_reports()

        report_data["api_status"] = api_response

        if not isinstance(
            api_response,
            dict,
        ):

            return report_data

        if not api_response.get(
            "success",
            True,
        ):

            report_data["api_error"] = api_response.get(
                "message",
                "Backend returned an error.",
            )

            return report_data

        #
        # Backend payload
        #

        payload = api_response.get(
            "data",
            api_response,
        )

        report_data.update(
            {
                "report": payload.get(
                    "report",
                ),
                "reports": payload.get(
                    "reports",
                    report_data["reports"],
                ),
                "ai_report": payload.get(
                    "ai_report",
                ),
                "execution_time": payload.get(
                    "execution_time",
                ),
                "output_path": payload.get(
                    "output_path",
                )
                or payload.get(
                    "export_path",
                ),
                "source": "api",
            }
        )

        if api_response.get("success", True):
            _cache_reports(dataset_version_id, report_data)

        return report_data

    except (
        httpx.HTTPError,
        ConnectionError,
        TimeoutError,
        OSError,
    ) as exc:

        report_data["api_error"] = str(exc)

        return report_data


# ==========================================================
# Export API
# ==========================================================


def _export_via_api(kind: str, report_id: int | None, suffix: str, mime_type: str) -> dict[str, Any]:
    """
    Fetch an export from the API and keep its bytes in memory.

    Two things changed (L16, L18). Exports used to be written to shared
    filenames under the report directory - every user's latest export in one
    `analystgpt_report.txt` - and were never deleted. And when the REST call
    failed for ANY reason, a 403 included, the frontend built an Application
    in-process and exported directly, without the API's permission checks.
    The API is now the only path; its error is reported, not worked around.
    """
    token = get_auth_token()
    try:
        with APIClient() as client:
            fetch = client.export_pdf_report if suffix == ".pdf" else client.export_text_report
            content = fetch(report_id=report_id, token=token)
    except Exception as exc:
        logger.warning("%s report export failed: %s", kind, exc)
        if "HTTP 404" in str(exc):
            return {"success": False, "message": f"No generated report was found to export as {kind}."}
        if "HTTP 403" in str(exc):
            return {"success": False, "message": "Your account cannot export reports."}
        return {"success": False, "message": f"The {kind} report could not be exported. Please try again."}

    if not content or (suffix == ".pdf" and not content.startswith(b"%PDF-")):
        return {"success": False, "message": f"No generated report was found to export as {kind}."}

    filename = f"report_{report_id}{suffix}" if report_id is not None else f"analystgpt_report{suffix}"
    return {
        "success": True,
        "message": f"{kind} report ready for download.",
        "filename": filename,
        "mime_type": mime_type,
        "data": content,
    }


def export_text_report(
    report_id: int | None = None,
) -> dict[str, Any]:
    """
    Export a plain-text report through the API.
    """
    return _export_via_api("text", report_id, ".txt", "text/plain")


def export_pdf_report(
    report_id: int | None = None,
) -> dict[str, Any]:
    """
    Export a PDF report through the API.
    """
    return _export_via_api("PDF", report_id, ".pdf", "application/pdf")
