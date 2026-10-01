"""
AnalystGPT Enterprise

Enterprise Streamlit Frontend Entry Point

Sprint 11
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is in sys.path when launched directly via `streamlit run`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st  # noqa: E402

from src.core.constants import (  # noqa: E402
    APP_NAME,
    APP_VERSION,
)
from src.core.logger import logger  # noqa: E402
from src.frontend.components.footer import (  # noqa: E402
    render_footer,
)
from src.frontend.pages import DEFAULT_PAGE, PAGES  # noqa: E402
from src.frontend.services.auth_service import AuthService  # noqa: E402
from src.frontend.services.session_manager import (  # noqa: E402
    get_current_user,
    get_user_role,
    is_admin,
    is_authenticated,
)

# ==========================================================
# Constants & Page Routing
# ==========================================================

APP_TITLE = APP_NAME


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


def _backend_connected(max_age_seconds: float = 30.0) -> bool:
    """
    Whether GET /api/health answers, re-checked at most every 30 s (P2-08).

    The sidebar used to say "Backend Connected" unconditionally.
    """
    import time

    from src.frontend.services.api_client import APIClient

    now = time.monotonic()
    checked_at = st.session_state.get("_backend_checked_at", 0.0)
    if now - checked_at < max_age_seconds and "backend_connected" in st.session_state:
        return bool(st.session_state.backend_connected)
    try:
        with APIClient(timeout=3.0) as client:
            client.health()
        connected = True
    except Exception:
        connected = False
    st.session_state.backend_connected = connected
    st.session_state["_backend_checked_at"] = now
    return connected


# ==========================================================
# Sidebar
# ==========================================================

if is_authenticated():
    # Picks up role changes and revoked sessions (I2); cheap, at most every 5 min.
    AuthService().revalidate_session()

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

        if st.button("🧠 AI Insights", use_container_width=True):
            st.session_state.current_page = "AI Insights"

        if is_admin():
            if st.button("⚙️ User Admin", use_container_width=True):
                st.session_state.current_page = "Admin"

        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.current_page = "About"

        st.divider()

        if st.button("🚪 Sign Out", use_container_width=True):
            AuthService().logout()
            st.rerun()

        with st.expander("Account security"):
            with st.form("change_password_form", clear_on_submit=True):
                current_password = st.text_input("Current password", type="password")
                new_password = st.text_input("New password", type="password")
                if st.form_submit_button("Change password", use_container_width=True):
                    changed, change_error = AuthService().change_password(current_password, new_password)
                    if changed:
                        st.session_state.current_page = "Sign In"
                        st.rerun()
                    else:
                        st.error(change_error)

            if st.button("Sign out everywhere", use_container_width=True):
                signed_out, signout_error = AuthService().logout_everywhere()
                if signed_out:
                    st.rerun()
                else:
                    st.error(signout_error)

    else:
        st.info("🔒 Authentication Required")
        st.divider()

        if st.button("🔐 Sign In", use_container_width=True):
            st.session_state.current_page = "Sign In"

        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.current_page = "About"

    st.divider()

    if _backend_connected():
        st.success("Backend Connected")
    else:
        st.error("Backend Offline — pages show what is available and retry automatically.")

    st.caption(f"Version {APP_VERSION}")

# ==========================================================
# Page Router
# ==========================================================

page = st.session_state.current_page

try:
    if not is_authenticated() and page != "About":
        PAGES["Sign In"]()
    else:
        if page not in PAGES:
            logger.warning("Unknown frontend page: %s", page)
            st.warning("Unknown page requested.")
            page = DEFAULT_PAGE if is_authenticated() else "About"

        logger.info("Opening frontend page: %s", page)
        PAGES[page]()

except Exception as error:
    # Tracebacks stay in the server log (L7): st.exception showed them to
    # every visitor, with file paths and code.
    logger.exception("Frontend error: %s", error)
    st.error("An unexpected error occurred. Please try again; if it persists, contact an administrator.")

# ==========================================================
# Global Footer
# ==========================================================

render_footer()
