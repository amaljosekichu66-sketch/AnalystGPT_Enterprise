"""
Report service for AnalystGPT Enterprise.

Provides report information using the REST API when available,
with automatic fallback to the local Streamlit session.
"""

from __future__ import annotations

from typing import Any

import httpx
import pandas as pd
import streamlit as st

from src.application.reporting_orchestrator import (
    ReportingOrchestrator,
)
from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import get_dataset


@st.cache_data(show_spinner=False)
def _generate_reports(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Generate available report names.
    """

    reports = [
        "Dataset Summary",
        "Quality Report",
        "Analytics Report",
        "Column Profile",
    ]

    numeric_columns = dataframe.select_dtypes(
        include="number",
    )

    if not numeric_columns.empty:

        reports.append(
            "Correlation Analysis",
        )

    return reports


def _local_report_data() -> dict[str, Any]:
    """
    Build report information from the current session.
    """

    uploaded_file, dataframe = get_dataset()

    if dataframe is None:

        return {
            "dataset_loaded": False,
            "filename": None,
            "reports": [],
            "dataframe": None,
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
        "source": "session",
    }


def get_report_data() -> dict[str, Any]:
    """
    Return report information.

    Uses the REST API when available and
    falls back to the local session.
    """

    try:

        with APIClient() as client:

            api_response = client.reports()

        report_data = _local_report_data()

        report_data["api_status"] = api_response

        report_data["source"] = "api"

        return report_data

    except (
        httpx.HTTPError,
        ConnectionError,
        TimeoutError,
        OSError,
    ):

        return _local_report_data()


# ==========================================================
# Export Services
# ==========================================================


def export_text_report() -> dict[str, Any]:
    """
    Request a text report export.

    The frontend delegates export requests to the
    Application Layer. Actual export implementation
    will be completed in a future reporting sprint.
    """

    uploaded_file, dataframe = get_dataset()

    if dataframe is None:

        return {
            "success": False,
            "message": "No dataset available.",
        }

    orchestrator = ReportingOrchestrator()

    return orchestrator.export_text_report(
        dataframe=dataframe,
        filename=(
            uploaded_file.name
            if uploaded_file
            else "dataset"
        ),
    )


def export_pdf_report() -> dict[str, Any]:
    """
    Request a PDF report export.

    The frontend delegates export requests to the
    Application Layer. Actual export implementation
    will be completed in a future reporting sprint.
    """

    uploaded_file, dataframe = get_dataset()

    if dataframe is None:

        return {
            "success": False,
            "message": "No dataset available.",
        }

    orchestrator = ReportingOrchestrator()

    return orchestrator.export_pdf_report(
        dataframe=dataframe,
        filename=(
            uploaded_file.name
            if uploaded_file
            else "dataset"
        ),
    )