"""
Enterprise Dashboard Page

AnalystGPT Enterprise

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import streamlit as st

from src.core.config import DATAFRAME_PREVIEW_ROWS
from src.frontend.components.charts import render_charts
from src.frontend.components.column_profile import render_column_profile
from src.frontend.components.dashboard_summary import render_dashboard_summary
from src.frontend.components.empty_state import render_empty_state
from src.frontend.components.kpi_cards import render_kpi_cards
from src.frontend.components.loading_state import loading
from src.frontend.components.pipeline_status import render_pipeline_status
from src.frontend.components.quick_actions import render_quick_actions
from src.frontend.components.scroll_to_top import scroll_to_top
from src.frontend.services.dashboard_service import get_dashboard_data


def render() -> None:
    """
    Render the enterprise dashboard.
    """
    scroll_to_top()

    st.title("📊 Enterprise Dashboard")
    st.caption("High-level analytical overview, visual analytics, and operational health of the active dataset.")

    with loading("Loading dashboard analytics..."):
        dashboard_data = get_dashboard_data()

    # ==========================================================
    # 1. Empty State
    # ==========================================================
    if not dashboard_data.get("dataset_loaded"):
        render_empty_state(
            title="No Dataset Loaded",
            message="Upload a CSV, Excel or JSON dataset from the Upload page to view dashboard analytics.",
            icon="📊",
            button_label="Go to Upload",
            target_page="Upload",
        )
        return

    df = dashboard_data["dataframe"]

    # ==========================================================
    # 2. Dataset Context Banner
    # ==========================================================
    st.success(f"Active Dataset: **{dashboard_data['filename']}** ({len(df):,} rows, {len(df.columns)} columns)")

    st.divider()

    # ==========================================================
    # 3. Primary Key Performance Indicators (Top-Level)
    # ==========================================================
    render_kpi_cards(dashboard_data)

    st.divider()

    # ==========================================================
    # 4. Pipeline Execution & Operational Health Summary
    # ==========================================================
    left, right = st.columns(2, gap="large")
    with left:
        render_pipeline_status(dashboard_data)
    with right:
        render_dashboard_summary(dashboard_data)

    st.divider()

    # ==========================================================
    # 5. Visual Analytics (2x2 / 3x3 Responsive Grid)
    # ==========================================================
    st.subheader("📈 Visual Analytics")
    st.caption("Selective high-value charts planned from semantic column profiles and distributions.")
    render_charts(df)

    st.divider()

    # ==========================================================
    # 6. Data Exploration & Schema Overview
    # ==========================================================
    st.subheader("🔍 Dataset Preview & Semantic Profile")

    tab_preview, tab_schema = st.tabs(["Dataset Preview", "Semantic Column Profile"])

    with tab_preview:
        st.caption(f"Displaying first {DATAFRAME_PREVIEW_ROWS} rows of dataset.")
        st.dataframe(df.head(DATAFRAME_PREVIEW_ROWS), width="stretch")

    with tab_schema:
        render_column_profile(df)

    st.divider()

    # ==========================================================
    # 7. Quick Actions
    # ==========================================================
    render_quick_actions()
