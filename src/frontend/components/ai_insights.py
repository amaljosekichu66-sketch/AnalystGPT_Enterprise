"""
AI Insights component.

Displays AI-generated business insights from the
AnalystGPT Enterprise AI Insight Engine.
"""

from __future__ import annotations

from typing import Any

import json

import streamlit as st


# ==========================================================
# Helpers
# ==========================================================


def _extract_ai_report(
    data: Any,
) -> dict[str, Any] | None:
    """
    Accept multiple backend formats.

    Supports:
    - ai_report dict
    - report_data dict
    - JSON string
    """

    if data is None:
        return None

    if isinstance(
        data,
        str,
    ):
        try:
            data = json.loads(
                data,
            )
        except Exception:
            return None

    if not isinstance(
        data,
        dict,
    ):
        return None

    #
    # ReportService payload
    #

    if data.get(
        "ai_report",
    ):
        return data[
            "ai_report"
        ]

    #
    # Dashboard payload
    #

    if data.get(
        "report",
    ):

        report = data[
            "report"
        ]

        if isinstance(
            report,
            dict,
        ):

            if report.get(
                "ai_report",
            ):
                return report[
                    "ai_report"
                ]

            if report.get(
                "ai",
            ):
                return report[
                    "ai"
                ]

    #
    # Already AI report
    #

    return data


def _value(
    report: dict[str, Any],
    key: str,
    default=None,
):
    return report.get(
        key,
        default,
    )


# ==========================================================
# Public
# ==========================================================


def render_ai_insights(
    data: Any,
) -> None:
    """
    Render AI business insights.
    """

    st.header(
        "🧠 AI Business Insights"
    )

    ai_report = _extract_ai_report(
        data,
    )

    if not ai_report:

        st.info(
            "AI insights have not been generated yet."
        )

        return

    #
    # Executive Summary
    #

    summary = _value(
        ai_report,
        "executive_summary",
    )

    if summary:

        st.subheader(
            "📋 Executive Summary"
        )

        st.success(
            summary,
        )

    #
    # Recommendations
    #

    recommendations = _value(
        ai_report,
        "recommendations",
        [],
    )

    if recommendations:

        st.subheader(
            "💡 Recommendations"
        )

        for item in recommendations:

            st.markdown(
                f"- {item}"
            )

    #
    # Explanations
    #

    explanations = _value(
        ai_report,
        "explanations",
        [],
    )

    if explanations:

        st.subheader(
            "📖 Explanations"
        )

        for item in explanations:

            st.info(
                item,
            )

    #
    # Narrative
    #

    narrative = _value(
        ai_report,
        "narrative",
    )

    if narrative:

        st.subheader(
            "📝 Business Narrative"
        )

        st.write(
            narrative,
        )

    #
    # Metadata
    #

    st.divider()

    st.subheader(
        "⚙ AI Engine"
    )

    col1, col2, col3 = st.columns(
        3,
    )

    with col1:

        st.metric(
            "Model",
            _value(
                ai_report,
                "model",
                "-",
            ),
        )

    with col2:

        st.metric(
            "Provider",
            _value(
                ai_report,
                "provider",
                "-",
            ),
        )

    with col3:

        execution_time = _value(
            ai_report,
            "execution_time",
        )

        if execution_time is None:

            st.metric(
                "Generation Time",
                "-",
            )

        else:

            st.metric(
                "Generation Time",
                f"{float(execution_time):.2f} s",
            )