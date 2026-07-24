"""
Enterprise Reports Page

AnalystGPT Enterprise

Sprint 10
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.empty_state import (
    render_empty_state,
)

from src.frontend.components.footer import (
    render_footer,
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

    st.title("📄 Reports Centre")

    st.caption(
        "View generated reports and submit export "
        "requests through the application layer."
    )

    with loading("Loading reports..."):

        report_data = get_report_data()

    # ==========================================================
    # Empty State
    # ==========================================================

    if not report_data["dataset_loaded"]:

        render_empty_state(
            title="No Dataset Available",
            message=(
                "Upload and process a dataset before "
                "viewing reports."
            ),
            button_label="Go to Upload",
        )

        render_footer()

        return

    # ==========================================================
    # Dataset Banner
    # ==========================================================

    st.success(
        f"Current Dataset: {report_data['filename']}"
    )

    st.divider()

    # ==========================================================
    # Reports + Preview
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
    # Export Centre
    # ==========================================================

    st.subheader("📤 Export Centre")

    st.caption(
        "Export requests are routed through the "
        "Application Layer. Report generation "
        "will be connected when the "
        "Reporting Orchestrator implementation "
        "is completed."
    )

    col1, col2 = st.columns(
        2,
        gap="large",
    )

    # ----------------------------------------------------------
    # Text Export
    # ----------------------------------------------------------

    with col1:

        if st.button(
            "📄 Export Text Report",
            use_container_width=True,
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

    # ----------------------------------------------------------
    # PDF Export
    # ----------------------------------------------------------

    with col2:

        if st.button(
            "📑 Export PDF Report",
            use_container_width=True,
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
        "Report export is intentionally routed "
        "through the Application Layer to "
        "preserve the enterprise architecture."
    )

    render_footer()