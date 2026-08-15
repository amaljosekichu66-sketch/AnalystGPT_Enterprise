"""
AnalystGPT Enterprise

Enterprise Streamlit Frontend Entry Point

Sprint 11
"""

from __future__ import annotations

import streamlit as st

from src.core.constants import (
    APP_NAME,
    APP_VERSION,
)
from src.core.logger import logger
from src.frontend.components.footer import (
    render_footer,
)
from src.frontend.services.auth_service import AuthService
from src.frontend.services.session_manager import (
    get_current_user,
    get_user_role,
    is_admin,
    is_authenticated,
)
from src.frontend.views import (
    about_page,
    admin_page,
    dashboard_page,
    login_page,
    report_page,
    upload_page,
)

# ==========================================================
# Constants & Page Routing
# ==========================================================

APP_TITLE = APP_NAME

DEFAULT_PAGE = "Dashboard"

PAGES = {
    "Dashboard": dashboard_page.render,
    "Upload": upload_page.render,
    "Reports": report_page.render,
    "Admin": admin_page.render,
    "About": about_page.render,
    "Sign In": login_page.render,
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
    st.caption("Enterprise Analytics Platform")
    st.divider()

    if is_authenticated():
        user = get_current_user() or {}
        username = user.get("username", "User")
        role = get_user_role() or "USER"

        st.markdown(f"**Signed in as:** `{username}`")
        st.caption(f"Role: **{role}**")
        st.divider()

        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = "Dashboard"

        if st.button("📁 Upload Dataset", use_container_width=True):
            st.session_state.current_page = "Upload"

        if st.button("📄 Reports", use_container_width=True):
            st.session_state.current_page = "Reports"

        if is_admin():
            if st.button("⚙️ User Admin", use_container_width=True):
                st.session_state.current_page = "Admin"

        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.current_page = "About"

        st.divider()

        if st.button("🚪 Sign Out", use_container_width=True):
            AuthService().logout()
            st.rerun()

    else:
        st.info("🔒 Authentication Required")
        st.divider()

        if st.button("🔐 Sign In", use_container_width=True):
            st.session_state.current_page = "Sign In"

        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.current_page = "About"

    st.divider()

    if st.session_state.backend_connected:
        st.success("Backend Connected")
    else:
        st.error("Backend Offline")

    st.caption(f"Version {APP_VERSION}")

# ==========================================================
# Page Router
# ==========================================================

page = st.session_state.current_page

try:
    if not is_authenticated() and page != "About":
        login_page.render()
    else:
        if page not in PAGES:
            logger.warning("Unknown frontend page: %s", page)
            st.warning("Unknown page requested.")
            page = DEFAULT_PAGE if is_authenticated() else "About"

        logger.info("Opening frontend page: %s", page)
        PAGES[page]()

except Exception as error:
    logger.exception("Frontend error: %s", error)
    st.error("An unexpected error occurred.")
    with st.expander("Technical Details"):
        st.exception(error)

# ==========================================================
# Global Footer
# ==========================================================

render_footer()