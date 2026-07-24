"""
Report list component for AnalystGPT Enterprise.
"""

import streamlit as st


def render_report_list(data: dict) -> None:
    """
    Render the list of available reports.

    Parameters
    ----------
    data : dict
        Report information returned by ReportService.
    """

    st.subheader("📑 Available Reports")

    if not data["dataset_loaded"]:

        st.info(
            "No reports are available.\n\n"
            "Upload a dataset first."
        )

        return

    reports = data["reports"]

    for report in reports:

        st.success(report)