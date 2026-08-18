"""
Sidebar component for AnalystGPT Enterprise.
"""

from __future__ import annotations

import streamlit as st

from src.core.constants import (
    APP_VERSION,
)
from src.frontend.config.settings import (
    ABOUT_PAGE,
    ADMIN_PAGE,
    AI_INSIGHTS_PAGE,
    DASHBOARD_PAGE,
    REPORTS_PAGE,
    SIGN_IN_PAGE,
    UPLOAD_PAGE,
)
from src.frontend.services.auth_service import AuthService
from src.frontend.services.session_manager import (
    get_current_user,
    get_user_role,
    has_dataset,
    is_admin,
    is_authenticated,
)


def render_sidebar() -> str:
    """
    Render the application sidebar with identity and role-aware navigation.

    Returns
    -------
    str
        Selected page.
    """

    st.sidebar.title(
        "📊 AnalystGPT"
    )

    st.sidebar.caption(
        "Enterprise Analytics Platform"
    )

    st.sidebar.divider()

    if is_authenticated():
        user = get_current_user() or {}
        username = user.get("username", "Authenticated User")
        role = get_user_role() or "USER"

        st.sidebar.markdown(f"**Signed in as:** `{username}`")
        st.sidebar.caption(f"Role: **{role}**")

        st.sidebar.divider()

        nav_options = [
            DASHBOARD_PAGE,
            UPLOAD_PAGE,
            REPORTS_PAGE,
            AI_INSIGHTS_PAGE,
        ]
        if is_admin():
            nav_options.append(ADMIN_PAGE)
        nav_options.append(ABOUT_PAGE)

        selected_page = st.sidebar.radio(
            "Navigation",
            nav_options,
        )

        st.sidebar.divider()

        if st.sidebar.button("🚪 Sign Out", use_container_width=True):
            AuthService().logout()
            st.rerun()

    else:
        st.sidebar.info("🔒 Authentication Required")
        selected_page = st.sidebar.radio(
            "Navigation",
            (SIGN_IN_PAGE, ABOUT_PAGE),
        )

    st.sidebar.divider()

    if has_dataset():
        st.sidebar.success(
            "Dataset Loaded"
        )
    else:
        st.sidebar.info(
            "No Dataset Loaded"
        )

    st.sidebar.caption(
        f"Version {APP_VERSION}"
    )

    return selected_page