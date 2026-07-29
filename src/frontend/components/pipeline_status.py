"""
Pipeline status component for AnalystGPT Enterprise.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_pipeline_status(
    data: dict[str, Any],
) -> None:
    """
    Render pipeline status using the actual
    backend/session state.
    """

    st.subheader(
        "⚙️ Pipeline Status"
    )

    #
    # Dataset
    #

    if not data.get(
        "dataset_loaded",
    ):

        st.error(
            "❌ No dataset loaded."
        )

        return

    st.success(
        "✅ Dataset Loaded"
    )

    #
    # Backend
    #

    source = data.get(
        "source",
        "session",
    )

    if source == "api":

        st.success(
            "✅ Backend Connected"
        )

    else:

        st.warning(
            "⚠ Session Mode"
        )

    #
    # Pipeline
    #

    backend_report = data.get(
        "backend_report",
    )

    if backend_report:

        st.success(
            "✅ Analytics Pipeline Completed"
        )

    else:

        st.info(
            "Pipeline has not been executed."
        )

    #
    # AI
    #

    ai_report = data.get(
        "ai_report",
    )

    if ai_report:

        st.success(
            "✅ AI Insights Generated"
        )

    else:

        st.info(
            "AI Insight Engine has not generated results."
        )

    #
    # Metrics
    #

    st.divider()

    execution_time = data.get(
        "execution_time",
    )

    output_path = data.get(
        "output_path",
    )

    col1, col2 = st.columns(
        2,
    )

    with col1:

        if execution_time is not None:

            st.metric(
                "Pipeline Time",
                f"{execution_time:.2f} s",
            )

        else:

            st.metric(
                "Pipeline Time",
                "-",
            )

    with col2:

        if output_path:

            st.text_input(
                "Output Report",
                output_path,
                disabled=True,
            )

    #
    # AI Metadata
    #

    if ai_report:

        st.divider()

        col1, col2, col3 = st.columns(
            3,
        )

        with col1:

            st.metric(
                "AI Model",
                ai_report.get(
                    "model",
                    "-",
                ),
            )

        with col2:

            st.metric(
                "Provider",
                ai_report.get(
                    "provider",
                    "-",
                ),
            )

        with col3:

            ai_time = ai_report.get(
                "execution_time",
            )

            if ai_time is None:

                st.metric(
                    "AI Time",
                    "-",
                )

            else:

                st.metric(
                    "AI Time",
                    f"{float(ai_time):.2f} s",
                )

    #
    # API Error
    #

    api_error = data.get(
        "api_error",
    )

    if api_error:

        st.divider()

        st.warning(
            f"REST API unavailable.\n\n{api_error}"
        )