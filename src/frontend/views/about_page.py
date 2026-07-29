"""
Enterprise About Page

AnalystGPT Enterprise

Sprint 11
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.about_card import (
    render_about_card,
)

from src.frontend.components.loading_state import (
    loading,
)


def render() -> None:
    """
    Render the enterprise About page.
    """

    st.title("ℹ️ About AnalystGPT Enterprise")

    st.caption(
        "Enterprise Analytics Platform built using "
        "a modular, production-oriented architecture."
    )

    with loading(
        "Loading application information..."
    ):
        render_about_card()

    st.divider()

    st.info(
        "Sprint 11 extends the enterprise platform with "
        "AI Insight Engine integration, backend pipeline "
        "execution from Streamlit, REST API reporting, "
        "and Power BI-ready dashboard services."
    )