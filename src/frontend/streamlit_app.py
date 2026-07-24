"""
AnalystGPT Enterprise

Enterprise Streamlit Frontend Entry Point

Sprint 10
"""

from __future__ import annotations

import streamlit as st

from src.core.logger import logger

from src.frontend.views import (
    about_page,
    dashboard_page,
    report_page,
    upload_page,
)

# ==========================================================
# Constants
# ==========================================================

APP_TITLE = "AnalystGPT Enterprise"

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

# Future Sprint 11
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
        use_container_width=True,
    ):
        st.session_state.current_page = "Dashboard"

    if st.button(
        "📁 Upload Dataset",
        use_container_width=True,
    ):
        st.session_state.current_page = "Upload"

    if st.button(
        "📄 Reports",
        use_container_width=True,
    ):
        st.session_state.current_page = "Reports"

    if st.button(
        "ℹ️ About",
        use_container_width=True,
    ):
        st.session_state.current_page = "About"

    st.divider()

    if st.session_state.backend_connected:

        st.success(
            "Backend Connected"
        )

    else:

        st.error(
            "Backend Offline"
        )

    st.info(
        "Sprint 10"
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
# Footer
# ==========================================================

st.divider()

left, middle, right = st.columns(3)

with left:

    st.caption(
        "AnalystGPT Enterprise"
    )

    st.caption(
        "v10.0.0"
    )

with middle:

    st.caption(
        "Python • Streamlit • FastAPI • PostgreSQL • SQLite • Pandas"
    )

with right:

    st.caption(
        "MIT License"
    )

    st.caption(
        "© 2026 Amal Jose"
    )