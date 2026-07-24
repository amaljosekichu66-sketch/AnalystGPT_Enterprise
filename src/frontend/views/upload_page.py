"""
Upload page for AnalystGPT Enterprise.
"""

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
    # Store dataset in session
    # ==========================================================

    store_dataset(
        uploaded_file,
        dataframe,
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

    st.subheader("🔍 Preview")

    st.dataframe(
        dataframe.head(20),
        use_container_width=True,
    )

    # ==========================================================
    # Session Status
    # ==========================================================

    st.info(
        "📌 Dataset has been stored in the current session "
        "and is available to the Dashboard and Reports."
    )

    st.success(
        "✅ Dataset is ready for backend processing."
    )