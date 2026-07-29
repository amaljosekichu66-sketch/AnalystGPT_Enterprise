"""
Report service for AnalystGPT Enterprise.

Sprint 11
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import streamlit as st

from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import (
    get_dataset,
)


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

    Falls back to the local session when
    the REST API is unavailable.
    """

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
    Return information about an existing
    text report.

    The actual download is handled by the
    Streamlit download button.
    """

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
    }


def export_pdf_report() -> dict[str, Any]:
    """
    PDF export placeholder.

    Sprint 11 does not generate PDF reports.
    """

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
        }

    return {
        "success": False,
        "message": (
            "PDF export is not yet available. "
            "Generate a PDF exporter in Sprint 12."
        ),
    }