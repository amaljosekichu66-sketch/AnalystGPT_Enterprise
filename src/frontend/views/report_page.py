"""
Enterprise Reports Page

AnalystGPT Enterprise

Sprint 14 Phase 1 — Frontend UX Stabilization
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.empty_state import (
    render_empty_state,
)
from src.frontend.components.export_buttons import (
    render_export_buttons,
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
from src.frontend.components.scroll_to_top import (
    scroll_to_top,
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
    scroll_to_top()

    st.title("📄 Reports Centre")

    st.caption(
        "View generated reports, inspect preview artifacts, and "
        "submit export requests through the Application Layer."
    )

    with loading("Loading reports and previews..."):

        report_data = get_report_data()

    # ==========================================================
    # Empty State
    # ==========================================================

    if not report_data.get("dataset_loaded"):

        render_empty_state(
            title="No Dataset Available",
            message=("Upload and process a dataset before " "viewing reports."),
            icon="📄",
            button_label="Go to Upload",
            target_page="Upload",
        )

        return

    # ==========================================================
    # Dataset Banner
    # ==========================================================

    st.success(f"Current Dataset: {report_data['filename']}")

    if report_data.get("source") == "api":

        st.success("Connected to AnalystGPT REST API.")

    else:

        st.warning("REST API unavailable. " "Displaying locally available reports.")

    if report_data.get("api_error"):

        st.info(report_data["api_error"])

    if report_data.get("execution_time"):

        st.caption(f"Pipeline Execution Time: " f"{report_data['execution_time']:.2f} s")

    if report_data.get("output_path"):

        st.caption(f"Report Output: " f"{report_data['output_path']}")

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
    # AI Insights Navigation Callout
    # ==========================================================

    st.subheader("🧠 AI Business Insights")

    st.caption(
        "AI executive summaries, recommendations, and narratives " "are now hosted in the dedicated AI Insights page."
    )

    if st.button("🚀 Open AI Insights Page", width="stretch"):
        st.session_state.current_page = "AI Insights"
        st.rerun()

    st.divider()

    # ==========================================================
    # Export Centre
    # ==========================================================

    st.subheader("📤 Export Centre")

    st.caption(
        "Export requests are routed through the " "Application Layer to preserve the " "enterprise architecture."
    )

    report_info = report_data.get("report")
    report_id = report_info.get("id") or report_info.get("report_id") if isinstance(report_info, dict) else None

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    with col1:
        if st.button(
            "📄 Export Text Report",
            width="stretch",
            key="btn_export_text",
        ):
            with loading("Submitting text export..."):
                result = export_text_report(report_id=report_id)
            st.session_state["exported_text_result"] = result
            if result.get("success"):
                st.success(result.get("message", "Text report ready for download."))
            else:
                st.warning(result.get("message", "Text export failed."))

        text_result = st.session_state.get("exported_text_result")
        if text_result and text_result.get("success"):
            render_export_buttons(text_result, key_prefix="text")

    with col2:
        if st.button(
            "📑 Export PDF Report",
            width="stretch",
            key="btn_export_pdf",
        ):
            with loading("Submitting PDF export..."):
                result = export_pdf_report(report_id=report_id)
            st.session_state["exported_pdf_result"] = result
            if result.get("success"):
                st.success(result.get("message", "PDF report ready."))
            else:
                st.warning(result.get("message", "PDF export failed."))

        pdf_result = st.session_state.get("exported_pdf_result")
        if pdf_result and pdf_result.get("success"):
            render_export_buttons(pdf_result, key_prefix="pdf")

    st.info(
        "Reports include structured quality metrics, descriptive statistics, "
        "and analytical summaries generated from the pipeline."
    )
