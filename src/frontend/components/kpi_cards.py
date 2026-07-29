"""
KPI cards component for AnalystGPT Enterprise.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_kpi_cards(
    data: dict[str, Any],
) -> None:
    """
    Render dashboard KPI cards.
    """

    st.subheader(
        "📊 Key Performance Indicators"
    )

    if not data.get(
        "dataset_loaded",
    ):

        st.info(
            "No dataset loaded."
        )

        return

    ai_report = data.get(
        "ai_report",
    )

    execution_time = data.get(
        "execution_time",
    )

    col1, col2, col3, col4 = st.columns(4)

    # =====================================================
    # Rows
    # =====================================================

    with col1:

        st.metric(
            label="Rows",
            value=f"{data.get('rows', 0):,}",
        )

    # =====================================================
    # Columns
    # =====================================================

    with col2:

        st.metric(
            label="Columns",
            value=data.get(
                "columns",
                0,
            ),
        )

    # =====================================================
    # Pipeline Time
    # =====================================================

    with col3:

        if execution_time is not None:

            st.metric(
                label="Pipeline Time",
                value=f"{execution_time:.2f}s",
            )

        else:

            st.metric(
                label="Missing Values",
                value=f"{data.get('missing', 0):,}",
            )

    # =====================================================
    # AI Status
    # =====================================================

    with col4:

        if ai_report:

            st.metric(
                label="AI Model",
                value=ai_report.get(
                    "model",
                    "-",
                ),
            )

        else:

            st.metric(
                label="Duplicate Rows",
                value=f"{data.get('duplicates', 0):,}",
            )

    # =====================================================
    # Secondary KPI Row
    # =====================================================

    st.markdown("")

    col5, col6, col7, col8 = st.columns(4)

    with col5:

        st.metric(
            "Numeric Columns",
            data.get(
                "numeric_columns",
                0,
            ),
        )

    with col6:

        st.metric(
            "Categorical Columns",
            data.get(
                "categorical_columns",
                0,
            ),
        )

    with col7:

        if ai_report:

            st.metric(
                "AI Time",
                f"{ai_report.get('execution_time', 0):.2f}s",
            )

        else:

            st.metric(
                "Duplicates",
                f"{data.get('duplicates', 0):,}",
            )

    with col8:

        source = data.get(
            "source",
            "session",
        )

        st.metric(
            "Backend",
            "API"
            if source == "api"
            else "Session",
        )