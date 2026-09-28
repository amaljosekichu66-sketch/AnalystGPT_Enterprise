"""
Dashboard summary component for AnalystGPT Enterprise.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def _safe_metric(
    label: str,
    value: Any,
) -> None:
    """
    Safely render a metric.
    """

    if value is None:
        value = "-"

    st.metric(
        label,
        value,
    )


def render_dashboard_summary(
    data: dict[str, Any],
) -> None:
    """
    Render dashboard summary information.
    """

    st.subheader("📋 Dashboard Summary")

    if not data.get(
        "dataset_loaded",
    ):

        st.info("No dataset available.")

        return

    # ==========================================================
    # Extract Backend Payload
    # ==========================================================

    backend = data.get(
        "backend_report",
        {},
    )

    ai_report = data.get(
        "ai_report",
    )

    report = {}

    if isinstance(
        backend,
        dict,
    ):

        #
        # DashboardService returns:
        #
        # backend_report
        #   └── report
        #
        report = backend.get(
            "report",
            backend,
        )

    execution_time = (
        data.get(
            "execution_time",
        )
        or backend.get(
            "execution_time",
        )
        or report.get(
            "execution_time",
        )
    )

    output_path = (
        data.get(
            "output_path",
        )
        or backend.get(
            "output_path",
        )
        or report.get(
            "output_path",
        )
        or report.get(
            "export_path",
        )
    )

    # ==========================================================
    # Dataset Information
    # ==========================================================

    st.markdown("### 📊 Dataset Information")

    left, right = st.columns(
        2,
    )

    with left:

        st.write(
            "**Dataset**",
            data.get(
                "filename",
                "-",
            ),
        )

        st.write(
            "**Rows**",
            f"{data.get('rows',0):,}",
        )

        st.write(
            "**Columns**",
            data.get(
                "columns",
                0,
            ),
        )

        st.write(
            "**Memory Usage**",
            f"{data.get('memory',0):.2f} MB",
        )

    with right:

        st.write(
            "**Numeric Columns**",
            data.get(
                "numeric_columns",
                0,
            ),
        )

        st.write(
            "**Categorical Columns**",
            data.get(
                "categorical_columns",
                0,
            ),
        )

        st.write(
            "**Missing Values**",
            f"{data.get('missing',0):,}",
        )

        st.write(
            "**Duplicate Rows**",
            f"{data.get('duplicates',0):,}",
        )

    # ==========================================================
    # Backend Pipeline
    # ==========================================================

    st.divider()

    st.markdown("### ⚙ Backend Pipeline")

    left, right = st.columns(
        2,
    )

    with left:

        _safe_metric(
            "Source",
            data.get(
                "source",
                "session",
            ).upper(),
        )

        if execution_time is not None:

            _safe_metric(
                "Pipeline Time",
                f"{execution_time:.2f} s",
            )

        if output_path:

            st.text_input(
                "Report Output",
                output_path,
                disabled=True,
            )

    with right:

        if ai_report:

            _safe_metric(
                "AI Model",
                ai_report.get(
                    "model",
                    "-",
                ),
            )

            _safe_metric(
                "AI Provider",
                ai_report.get(
                    "provider",
                    "-",
                ),
            )

            ai_time = ai_report.get(
                "execution_time",
            )

            if ai_time is not None:

                _safe_metric(
                    "AI Time",
                    f"{ai_time:.2f} s",
                )

        else:

            st.info("AI report not available.")

    # ==========================================================
    # Reporting Status
    # ==========================================================

    st.divider()

    st.markdown("### 📑 Reporting Status")

    if report:

        st.success("✅ Reporting completed successfully.")

    else:

        st.warning("Reporting output is not available.")

    if data.get(
        "api_error",
    ):

        st.error(data["api_error"])

    elif (
        data.get(
            "source",
        )
        == "api"
    ):

        st.success("Connected to AnalystGPT REST API.")

    else:

        st.info("Displaying locally available dashboard information.")
