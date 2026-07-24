"""
Dashboard summary component for AnalystGPT Enterprise.
"""

import streamlit as st


def render_dashboard_summary(data: dict) -> None:
    """
    Render dashboard summary information.

    Parameters
    ----------
    data : dict
        Dashboard information from DashboardService.
    """

    st.subheader("📋 Dataset Summary")

    if not data["dataset_loaded"]:
        st.info("No dataset available.")
        return

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "**Dataset Name**",
            data["filename"],
        )

        st.write(
            "**Rows**",
            f"{data['rows']:,}",
        )

        st.write(
            "**Columns**",
            data["columns"],
        )

    with col2:

        st.write(
            "**Numeric Columns**",
            data["numeric_columns"],
        )

        st.write(
            "**Categorical Columns**",
            data["categorical_columns"],
        )

        st.write(
            "**Memory Usage**",
            f"{data['memory']:.2f} MB",
        )