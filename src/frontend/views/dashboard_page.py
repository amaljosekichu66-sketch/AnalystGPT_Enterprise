"""
Enterprise Dashboard Page

AnalystGPT Enterprise

Sprint 10
"""

from __future__ import annotations

import streamlit as st

from src.core.config import (
    DATAFRAME_PREVIEW_ROWS,
)

from src.frontend.components.dashboard_summary import (
    render_dashboard_summary,
)

from src.frontend.components.empty_state import (
    render_empty_state,
)

from src.frontend.components.footer import (
    render_footer,
)

from src.frontend.components.kpi_cards import (
    render_kpi_cards,
)

from src.frontend.components.loading_state import (
    loading,
)

from src.frontend.components.pipeline_status import (
    render_pipeline_status,
)

from src.frontend.components.quick_actions import (
    render_quick_actions,
)

from src.frontend.services.dashboard_service import (
    get_dashboard_data,
)


def render() -> None:
    """
    Render the enterprise dashboard.
    """

    st.title("📊 Enterprise Dashboard")

    st.caption(
        "Enterprise overview of the current "
        "analytics pipeline."
    )

    with loading("Loading dashboard..."):

        dashboard_data = get_dashboard_data()

    # ==========================================================
    # Empty State
    # ==========================================================

    if not dashboard_data["dataset_loaded"]:

        render_empty_state(
            title="No Dataset Loaded",
            message=(
                "Upload a CSV, Excel or JSON dataset "
                "from the Upload page to begin."
            ),
            button_label="Go to Upload",
        )

        render_footer()

        return

    # ==========================================================
    # Dataset Banner
    # ==========================================================

    st.success(
        f"Current Dataset: {dashboard_data['filename']}"
    )

    st.divider()

    # ==========================================================
    # KPI Cards
    # ==========================================================

    render_kpi_cards(
        dashboard_data,
    )

    st.divider()

    # ==========================================================
    # Pipeline + Summary
    # ==========================================================

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    with col1:

        render_pipeline_status(
            dashboard_data,
        )

    with col2:

        render_dashboard_summary(
            dashboard_data,
        )

    st.divider()

    # ==========================================================
    # Quick Actions + Preview
    # ==========================================================

    col1, col2 = st.columns(
        [1, 2],
        gap="large",
    )

    with col1:

        render_quick_actions()

    with col2:

        st.subheader("🔍 Dataset Preview")

        st.caption(
            f"Showing first "
            f"{DATAFRAME_PREVIEW_ROWS:,} rows."
        )

        st.dataframe(
            dashboard_data["dataframe"].head(
                DATAFRAME_PREVIEW_ROWS,
            ),
            use_container_width=True,
        )

    st.divider()

    # ==========================================================
    # Dataset Schema
    # ==========================================================

    st.subheader("📋 Dataset Schema")

    datatype_summary = (
        dashboard_data["dataframe"]
        .dtypes
        .astype(str)
        .rename("Data Type")
        .reset_index()
    )

    datatype_summary.columns = [
        "Column",
        "Data Type",
    ]

    st.dataframe(
        datatype_summary,
        hide_index=True,
        use_container_width=True,
    )

    render_footer()