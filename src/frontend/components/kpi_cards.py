"""
KPI cards component for AnalystGPT Enterprise.
"""

import streamlit as st


def render_kpi_cards(data: dict) -> None:
    """
    Render dashboard KPI cards.

    Parameters
    ----------
    data : dict
        Dashboard information from dashboard_service.
    """

    st.subheader("📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Rows",
            value=f"{data['rows']:,}",
        )

    with col2:
        st.metric(
            label="Columns",
            value=data["columns"],
        )

    with col3:
        st.metric(
            label="Missing Values",
            value=f"{data['missing']:,}",
        )

    with col4:
        st.metric(
            label="Duplicate Rows",
            value=f"{data['duplicates']:,}",
        )