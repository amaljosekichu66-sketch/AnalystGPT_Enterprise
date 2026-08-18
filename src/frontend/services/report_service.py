"""
Report service for AnalystGPT Enterprise.

Sprint 11
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import streamlit as st

from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import (
    get_dataset,
    get_dataset_path,
)

# ==========================================================
# Reports Cache (Session-Level)
# ==========================================================

_REPORTS_CACHE_KEY = "reports_cache"
_REPORTS_DATASET_KEY = "reports_dataset"


def _get_cached_reports(
    dataset_path: str | None,
) -> dict[str, Any] | None:
    """
    Retrieve cached report data if valid for the current dataset.
    """
    if not dataset_path:
        return None

    if st.session_state.get(_REPORTS_DATASET_KEY) != dataset_path:
        return None

    cached = st.session_state.get(_REPORTS_CACHE_KEY)
    if cached is None:
        return None

    return deepcopy(cached)


def _cache_reports(
    dataset_path: str | None,
    report_data: dict[str, Any],
) -> None:
    """
    Cache successful report data in session state.
    """
    if not dataset_path:
        return

    st.session_state[_REPORTS_DATASET_KEY] = dataset_path
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

        reports.append(
            "Correlation Analysis"
        )

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
        "filename": (
            uploaded_file.name
            if uploaded_file
            else None
        ),
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
    dataset_path = get_dataset_path()

    cached = _get_cached_reports(dataset_path)
    if cached is not None:
        return cached

    report_data = (
        _local_report_data()
    )

    try:

        with APIClient() as client:

            api_response = (
                client.get_reports()
            )

        report_data[
            "api_status"
        ] = api_response

        if (
            not isinstance(
                api_response,
                dict,
            )
        ):

            return report_data

        if not api_response.get(
            "success",
            True,
        ):

            report_data[
                "api_error"
            ] = api_response.get(
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
                    report_data[
                        "reports"
                    ],
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
            _cache_reports(dataset_path, report_data)

        return report_data

    except (
        httpx.HTTPError,
        ConnectionError,
        TimeoutError,
        OSError,
    ) as exc:

        report_data[
            "api_error"
        ] = str(exc)

        return report_data


# ==========================================================
# Export Helpers
# ==========================================================


def _existing_report() -> Path | None:
    """
    Locate an existing generated report.
    """

    candidates = [
        Path(
            "reports/analystgpt_report.txt"
        ),
        Path(
            "reports/report.txt"
        ),
    ]

    for candidate in candidates:

        if candidate.exists():

            return candidate

    return None


# ==========================================================
# Export API
# ==========================================================


def export_text_report() -> dict[str, Any]:
    """
    Generate and export a plain-text report artifact.
    """
    user = st.session_state.get("authenticated_user") or st.session_state.get("user")
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)

    app = st.session_state.get("application")
    if app is None:
        try:
            from src.application.app import Application
            app = Application()
        except Exception:
            app = None

    if app is not None:
        from src.application.reporting_orchestrator import ReportingOrchestrator
        orchestrator = ReportingOrchestrator(app)
        return orchestrator.export_text_report(user_id=user_id)

    report = _existing_report()

    if report is None:

        return {
            "success": False,
            "message": (
                "No generated report was found."
            ),
        }

    return {
        "success": True,
        "message": (
            "Report ready for download."
        ),
        "path": str(report),
        "filename": report.name,
        "mime_type": "text/plain",
    }


def export_pdf_report() -> dict[str, Any]:
    """
    Generate and export a PDF report artifact.
    """
    user = st.session_state.get("authenticated_user") or st.session_state.get("user")
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)

    app = st.session_state.get("application")
    if app is None:
        try:
            from src.application.app import Application
            app = Application()
        except Exception:
            app = None

    if app is not None:
        from src.application.reporting_orchestrator import ReportingOrchestrator
        orchestrator = ReportingOrchestrator(app)
        return orchestrator.export_pdf_report(user_id=user_id)

    pdf = Path(
        "reports/analystgpt_report.pdf"
    )

    if pdf.exists():

        return {
            "success": True,
            "message": (
                "PDF report ready."
            ),
            "path": str(pdf),
            "filename": pdf.name,
            "mime_type": "application/pdf",
        }

    return {
        "success": False,
        "message": (
            "No generated report was found to export as PDF."
        ),
    }