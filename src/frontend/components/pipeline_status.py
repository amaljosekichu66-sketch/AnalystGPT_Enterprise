"""
Pipeline status component for AnalystGPT Enterprise.
"""

import streamlit as st


def render_pipeline_status(data: dict) -> None:
    """
    Render the current pipeline status.

    Parameters
    ----------
    data : dict
        Dashboard information returned by DashboardService.
    """

    st.subheader("⚙️ Pipeline Status")

    if not data["dataset_loaded"]:

        st.error("❌ No dataset loaded.")

        return

    st.success("✅ Dataset Uploaded")

    st.success("✅ Session Active")

    st.info("⏳ Ready for Cleaning")

    st.info("⏳ Ready for Analytics")

    st.info("⏳ Ready for Reporting")