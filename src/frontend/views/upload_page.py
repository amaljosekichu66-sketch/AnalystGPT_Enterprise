"""
Upload page for AnalystGPT Enterprise.

Sprint 11
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.charts import render_charts
from src.frontend.components.column_profile import (
    render_column_profile,
)
from src.frontend.components.dataset_info import (
    render_dataset_info,
)
from src.frontend.components.dataset_quality import (
    render_dataset_quality,
)
from src.frontend.components.uploader import (
    render_uploader,
)
from src.frontend.services.session_manager import (
    clear_dataset,
    get_dataset_path,
    store_dataset,
)


def render() -> None:
    """
    Render the Upload page.
    """

    st.title("📁 Upload Dataset")

    st.write(
        "Upload datasets to begin the analytics pipeline."
    )

    uploaded_file, dataframe = render_uploader()

    if dataframe is None:
        return

    # ==========================================================
    # Preserve Temporary Dataset Path
    # ==========================================================

    dataset_path = get_dataset_path()

    # ==========================================================
    # Reset Previous Session
    # ==========================================================

    clear_dataset()

    # ==========================================================
    # Restore Dataset
    # ==========================================================

    store_dataset(
        uploaded_file=uploaded_file,
        dataframe=dataframe,
        dataset_path=dataset_path,
    )

    # ==========================================================
    # Dataset Information
    # ==========================================================

    with st.expander(
        "📊 Dataset Information",
        expanded=True,
    ):
        render_dataset_info(
            uploaded_file,
            dataframe,
        )

    # ==========================================================
    # Dataset Quality
    # ==========================================================

    with st.expander(
        "✅ Dataset Quality",
        expanded=True,
    ):
        render_dataset_quality(
            dataframe,
        )

    # ==========================================================
    # Visual Analytics
    # ==========================================================

    with st.expander(
        "📈 Visual Analytics",
        expanded=False,
    ):
        render_charts(
            dataframe,
        )

    # ==========================================================
    # Column Profile
    # ==========================================================

    with st.expander(
        "📋 Column Profile",
        expanded=False,
    ):
        render_column_profile(
            dataframe,
        )

    # ==========================================================
    # Dataset Preview
    # ==========================================================

    st.subheader("🔍 Dataset Preview")

    st.dataframe(
        dataframe.head(20),
        width="stretch",
    )

    # ==========================================================
    # Session Status
    # ==========================================================

    st.divider()

    st.success(
        "✅ Dataset uploaded successfully."
    )

    st.success(
        "✅ Dataset stored in the current session."
    )

    if dataset_path:

        st.caption(
            f"Dataset Path: {dataset_path}"
        )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Rows",
            f"{len(dataframe):,}",
        )

    with col2:

        st.metric(
            "Columns",
            len(dataframe.columns),
        )

    st.info(
        "The dataset is now available to the Dashboard, "
        "Reports, Power BI endpoints, and the AI Insight "
        "Engine."
    )

    st.success(
        "🚀 Dataset is ready for enterprise pipeline execution."
    )