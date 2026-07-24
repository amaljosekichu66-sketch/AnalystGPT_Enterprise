"""
Report preview component for AnalystGPT Enterprise.
"""

import streamlit as st


def render_report_preview(data: dict) -> None:
    """
    Render a preview of the current report.

    Parameters
    ----------
    data : dict
        Report information from ReportService.
    """

    st.subheader("📄 Report Preview")

    if not data["dataset_loaded"]:
        st.info("No report available.")
        return

    dataframe = data["dataframe"]

    rows = len(dataframe)
    columns = len(dataframe.columns)
    missing = int(dataframe.isna().sum().sum())
    duplicates = int(dataframe.duplicated().sum())

    preview = {
        "Dataset": data["filename"],
        "Rows": f"{rows:,}",
        "Columns": columns,
        "Missing Values": missing,
        "Duplicate Rows": duplicates,
    }

    st.json(preview)