"""
Sidebar component for AnalystGPT Enterprise.
"""

import streamlit as st

from src.frontend.config.settings import (
    ABOUT_PAGE,
    DASHBOARD_PAGE,
    REPORTS_PAGE,
    UPLOAD_PAGE,
)


def render_sidebar() -> str:
    """
    Render the application sidebar and return
    the selected page.
    """

    st.sidebar.title("AnalystGPT")

    selected_page = st.sidebar.radio(
        "Navigation",
        [
            DASHBOARD_PAGE,
            UPLOAD_PAGE,
            REPORTS_PAGE,
            ABOUT_PAGE,
        ],
    )

    return selected_page