"""
Report preview component for AnalystGPT Enterprise.

Displays the generated reporting output together
with AI Insight Engine results.
"""

from __future__ import annotations

from typing import Any

import json

import streamlit as st


# ==========================================================
# Dataset Summary
# ==========================================================


def _render_dataset_summary(
    data: dict[str, Any],
) -> None:
    """
    Render uploaded dataset summary.
    """

    dataframe = data.get(
        "dataframe",
    )

    if dataframe is None:

        return

    st.subheader(
        "📊 Dataset Summary"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Rows",
            len(dataframe),
        )

        st.metric(
            "Columns",
            len(dataframe.columns),
        )

    with col2:

        st.metric(
            "Missing Values",
            int(
                dataframe.isna().sum().sum()
            ),
        )

        st.metric(
            "Duplicate Rows",
            int(
                dataframe.duplicated().sum()
            ),
        )


# ==========================================================
# Reporting Layer
# ==========================================================


def _render_reporting(
    report: Any,
) -> None:
    """
    Render Reporting Layer output.
    """

    st.subheader(
        "📑 Reporting Layer"
    )

    if not report:

        st.info(
            "No reporting output available."
        )

        return

    if isinstance(
        report,
        dict,
    ):

        if report.get(
            "executive_summary"
        ):

            st.markdown(
                "### Executive Summary"
            )

            st.write(
                report[
                    "executive_summary"
                ]
            )

        if report.get(
            "kpis"
        ):

            st.markdown(
                "### KPI Summary"
            )

            st.json(
                report[
                    "kpis"
                ],
                expanded=False,
            )

        st.markdown(
            "### Raw Report"
        )

        st.json(
            report,
            expanded=False,
        )

    else:

        st.code(
            str(report),
        )


# ==========================================================
# AI Output
# ==========================================================


def _render_ai(
    ai_report: Any,
) -> None:
    """
    Render AI Insight Engine output.
    """

    st.subheader(
        "🧠 AI Insight Engine"
    )

    if not ai_report:

        st.info(
            "AI report not available."
        )

        return

    if isinstance(
        ai_report,
        str,
    ):

        try:

            ai_report = json.loads(
                ai_report,
            )

        except Exception:

            st.write(
                ai_report,
            )

            return

    summary = ai_report.get(
        "executive_summary",
    )

    if summary:

        st.success(
            summary,
        )

    recommendations = ai_report.get(
        "recommendations",
        [],
    )

    if recommendations:

        st.markdown(
            "### Recommendations"
        )

        for item in recommendations:

            st.markdown(
                f"- {item}"
            )

    explanations = ai_report.get(
        "explanations",
        [],
    )

    if explanations:

        st.markdown(
            "### Explanations"
        )

        for item in explanations:

            st.info(
                item,
            )

    narrative = ai_report.get(
        "narrative",
    )

    if narrative:

        st.markdown(
            "### Narrative"
        )

        st.write(
            narrative,
        )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Model",
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

        value = ai_report.get(
            "execution_time",
        )

        if value is None:

            st.metric(
                "AI Time",
                "-",
            )

        else:

            st.metric(
                "AI Time",
                f"{float(value):.2f} s",
            )


# ==========================================================
# Public
# ==========================================================


def render_report_preview(
    data: dict[str, Any],
) -> None:
    """
    Render report preview.
    """

    st.subheader(
        "📄 Report Preview"
    )

    if not data.get(
        "dataset_loaded",
    ):

        st.info(
            "No report available."
        )

        return

    _render_dataset_summary(
        data,
    )

    st.divider()

    _render_reporting(
        data.get(
            "report",
        ),
    )

    st.divider()

    _render_ai(
        data.get(
            "ai_report",
        ),
    )