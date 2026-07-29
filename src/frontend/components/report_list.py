"""
Report list component for AnalystGPT Enterprise.

Displays all available Reporting Layer and
AI Insight Engine reports.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_report_list(
    data: dict[str, Any],
) -> None:
    """
    Render the available reports.
    """

    st.subheader(
        "📑 Available Reports"
    )

    if not data.get(
        "dataset_loaded",
    ):

        st.info(
            "No reports available.\n\n"
            "Upload and process a dataset first."
        )

        return

    # =====================================================
    # Reporting Layer
    # =====================================================

    st.markdown(
        "### 📊 Reporting Layer"
    )

    reports = data.get(
        "reports",
        [],
    )

    if reports:

        for report in reports:

            #
            # REST API
            #

            if isinstance(
                report,
                dict,
            ):

                name = report.get(
                    "name",
                    "Unnamed Report",
                )

                status = report.get(
                    "status",
                    "Available",
                )

                icon = (
                    "✅"
                    if status.lower()
                    == "available"
                    else "⏳"
                )

                st.success(
                    f"{icon} {name}"
                )

            #
            # Session fallback
            #

            else:

                st.success(
                    f"✅ {report}"
                )

    else:

        st.warning(
            "No reports available."
        )

    # =====================================================
    # AI Reports
    # =====================================================

    st.divider()

    st.markdown(
        "### 🧠 AI Insight Engine"
    )

    ai_report = data.get(
        "ai_report",
    )

    if ai_report is None:

        st.info(
            "No AI report has been generated."
        )

        return

    ai_sections = [
        (
            "Executive Summary",
            ai_report.get(
                "executive_summary",
            ),
        ),
        (
            "Recommendations",
            ai_report.get(
                "recommendations",
            ),
        ),
        (
            "Explanations",
            ai_report.get(
                "explanations",
            ),
        ),
        (
            "Business Narrative",
            ai_report.get(
                "narrative",
            ),
        ),
    ]

    for title, value in ai_sections:

        available = False

        if isinstance(
            value,
            list,
        ):

            available = len(value) > 0

        else:

            available = bool(value)

        if available:

            st.success(
                f"✅ {title}"
            )

        else:

            st.warning(
                f"⚠ {title} unavailable"
            )

    # =====================================================
    # AI Metadata
    # =====================================================

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.caption(
            f"**Model:** {ai_report.get('model', '-')}"
        )

        st.caption(
            f"**Provider:** {ai_report.get('provider', '-')}"
        )

    with col2:

        execution_time = ai_report.get(
            "execution_time",
        )

        if execution_time is not None:

            st.caption(
                f"**Generation Time:** {execution_time:.2f}s"
            )