"""
Enterprise Reports Page

AnalystGPT Enterprise

Sprint 11
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.ai_insights import (
    render_ai_insights,
)
from src.frontend.components.empty_state import (
    render_empty_state,
)
from src.frontend.components.loading_state import (
    loading,
)
from src.frontend.components.report_list import (
    render_report_list,
)
from src.frontend.components.report_preview import (
    render_report_preview,
)
from src.frontend.services.report_service import (
    export_pdf_report,
    export_text_report,
    get_report_data,
)


def render() -> None:
    """
    Render the enterprise Reports page.
    """

    st.title(
        "📄 Reports Centre"
    )

    st.caption(
        "View generated reports, AI insights, and "
        "submit export requests through the "
        "Application Layer."
    )

    with loading(
        "Loading reports..."
    ):

        report_data = get_report_data()

    # ==========================================================
    # Empty State
    # ==========================================================

    if not report_data["dataset_loaded"]:

        if render_empty_state(
            title="No Dataset Available",
            message=(
                "Upload and process a dataset before "
                "viewing reports."
            ),
            button_label="Go to Upload",
        ):
            st.session_state.current_page = "Upload"
            st.rerun()

        return

    # ==========================================================
    # Dataset Banner
    # ==========================================================

    st.success(
        f"Current Dataset: {report_data['filename']}"
    )

    if report_data.get(
        "source"
    ) == "api":

        st.success(
            "Connected to AnalystGPT REST API."
        )

    else:

        st.warning(
            "REST API unavailable. "
            "Displaying locally available reports."
        )

    if report_data.get(
        "api_error"
    ):

        st.info(
            report_data[
                "api_error"
            ]
        )

    if report_data.get(
        "execution_time"
    ):

        st.caption(
            f"Pipeline Execution Time: "
            f"{report_data['execution_time']:.2f} s"
        )

    if report_data.get(
        "output_path"
    ):

        st.caption(
            f"Report Output: "
            f"{report_data['output_path']}"
        )

    st.divider()

    # ==========================================================
    # Report List + Preview
    # ==========================================================

    left, right = st.columns(
        [1, 2],
        gap="large",
    )

    with left:

        render_report_list(
            report_data,
        )

    with right:

        render_report_preview(
            report_data,
        )

    st.divider()

    # ==========================================================
    # AI Insight Engine
    # ==========================================================

    st.subheader(
        "🧠 AI Insight Engine"
    )

    render_ai_insights(
        report_data,
    )

    st.divider()

    # ==========================================================
    # Export Centre
    # ==========================================================

    st.subheader(
        "📤 Export Centre"
    )

    st.caption(
        "Export requests are routed through the "
        "Application Layer to preserve the "
        "enterprise architecture."
    )

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    with col1:

        if st.button(
            "📄 Export Text Report",
            width="stretch",
        ):

            with loading(
                "Submitting text export..."
            ):

                result = export_text_report()

            if result["success"]:

                st.success(
                    result["message"]
                )

            else:

                st.warning(
                    result["message"]
                )

    with col2:

        if st.button(
            "📑 Export PDF Report",
            width="stretch",
        ):

            with loading(
                "Submitting PDF export..."
            ):

                result = export_pdf_report()

            if result["success"]:

                st.success(
                    result["message"]
                )

            else:

                st.warning(
                    result["message"]
                )

    st.info(
        "Reports include both the analytical report "
        "and AI-generated business insights when "
        "available."
    )