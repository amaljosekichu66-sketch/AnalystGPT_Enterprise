"""
Enterprise Dashboard Page

AnalystGPT Enterprise

Sprint 11
"""

from __future__ import annotations

import streamlit as st

from src.core.config import (
    DATAFRAME_PREVIEW_ROWS,
)

from src.frontend.components.ai_insights import (
    render_ai_insights,
)
from src.frontend.components.dashboard_summary import (
    render_dashboard_summary,
)
from src.frontend.components.empty_state import (
    render_empty_state,
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

    st.title(
        "📊 Enterprise Dashboard"
    )

    st.caption(
        "Enterprise overview of the current analytics pipeline."
    )

    with loading(
        "Loading dashboard..."
    ):

        dashboard_data = get_dashboard_data()

    # ==========================================================
    # Empty State
    # ==========================================================

    if not dashboard_data["dataset_loaded"]:

        render_empty_state(
            title="No Dataset Loaded",
            message=(
                "Upload a CSV, Excel or JSON dataset "
                "from the Upload page."
            ),
            button_label="Go to Upload",
        )

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
    # Status + Summary
    # ==========================================================

    left, right = st.columns(
        2,
        gap="large",
    )

    with left:

        render_pipeline_status(
            dashboard_data,
        )

    with right:

        render_dashboard_summary(
            dashboard_data,
        )

    st.divider()

    # ==========================================================
    # AI Insights
    # ==========================================================

    render_ai_insights(
        dashboard_data.get(
            "ai_report",
        )
    )

    st.divider()

    # ==========================================================
    # Quick Actions + Preview
    # ==========================================================

    left, right = st.columns(
        [1, 2],
        gap="large",
    )

    with left:

        render_quick_actions()

    with right:

        st.subheader(
            "🔍 Dataset Preview"
        )

        st.dataframe(
            dashboard_data[
                "dataframe"
            ].head(
                DATAFRAME_PREVIEW_ROWS
            ),
            width="stretch",
        )

    st.divider()

    # ==========================================================
    # Dataset Schema
    # ==========================================================

    st.subheader(
        "📋 Dataset Schema"
    )

    schema = (
        dashboard_data[
            "dataframe"
        ]
        .dtypes
        .astype(str)
        .rename("Data Type")
        .reset_index()
    )

    schema.columns = [
        "Column",
        "Data Type",
    ]

    st.dataframe(
        schema,
        hide_index=True,
        width="stretch",
    )