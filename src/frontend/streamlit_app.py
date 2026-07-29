"""
AnalystGPT Enterprise

Enterprise Streamlit Frontend Entry Point

Sprint 11
"""

from __future__ import annotations

import streamlit as st

from src.core.constants import (
    APP_NAME,
)

from src.core.logger import logger

from src.frontend.components.footer import (
    render_footer,
)

from src.frontend.views import (
    about_page,
    dashboard_page,
    report_page,
    upload_page,
)

# ==========================================================
# Constants
# ==========================================================

APP_TITLE = APP_NAME

DEFAULT_PAGE = "Dashboard"

PAGES = {
    "Dashboard": dashboard_page.render,
    "Upload": upload_page.render,
    "Reports": report_page.render,
    "About": about_page.render,
}

# ==========================================================
# Page Configuration
# ==========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================
# Session Initialization
# ==========================================================

if "current_page" not in st.session_state:

    st.session_state.current_page = DEFAULT_PAGE

if "backend_connected" not in st.session_state:

    st.session_state.backend_connected = True

# ==========================================================
# Sidebar
# ==========================================================

with st.sidebar:

    st.title("📊 AnalystGPT")

    st.caption(
        "Enterprise Analytics Platform"
    )

    st.divider()

    if st.button(
        "🏠 Dashboard",
        width="stretch",
    ):
        st.session_state.current_page = (
            "Dashboard"
        )

    if st.button(
        "📁 Upload Dataset",
        width="stretch",
    ):
        st.session_state.current_page = (
            "Upload"
        )

    if st.button(
        "📄 Reports",
        width="stretch",
    ):
        st.session_state.current_page = (
            "Reports"
        )

    if st.button(
        "ℹ️ About",
        width="stretch",
    ):
        st.session_state.current_page = (
            "About"
        )

    st.divider()

    if st.session_state.backend_connected:

        st.success(
            "Backend Connected"
        )

    else:

        st.error(
            "Backend Offline"
        )

    st.success(
        "AI Insight Engine Enabled"
    )

# ==========================================================
# Page Router
# ==========================================================

page = st.session_state.current_page

try:

    if page not in PAGES:

        logger.warning(
            "Unknown frontend page: %s",
            page,
        )

        st.warning(
            "Unknown page requested."
        )

        page = DEFAULT_PAGE

    logger.info(
        "Opening frontend page: %s",
        page,
    )

    PAGES[page]()

except Exception as error:

    logger.exception(
        "Frontend error."
    )

    st.error(
        "An unexpected error occurred."
    )

    with st.expander(
        "Technical Details"
    ):

        st.exception(
            error
        )

# ==========================================================
# Global Footer
# ==========================================================

render_footer()