"""
Enterprise About Page

AnalystGPT Enterprise

Sprint 10
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.about_card import (
    render_about_card,
)

from src.frontend.components.footer import (
    render_footer,
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

    with loading("Loading application information..."):

        render_about_card()

    st.divider()

    st.info(
        "Sprint 10 focuses on delivering a polished "
        "enterprise frontend while preserving backend "
        "architecture and enabling a smooth migration "
        "to the planned React frontend."
    )

    render_footer()