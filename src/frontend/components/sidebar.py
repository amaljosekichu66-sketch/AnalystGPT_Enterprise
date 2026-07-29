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
    DASHBOARD_PAGE,
    REPORTS_PAGE,
    UPLOAD_PAGE,
)

from src.frontend.services.session_manager import (
    has_dataset,
)


def render_sidebar() -> str:
    """
    Render the application sidebar.

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

    selected_page = st.sidebar.radio(
        "Navigation",
        (
            DASHBOARD_PAGE,
            UPLOAD_PAGE,
            REPORTS_PAGE,
            ABOUT_PAGE,
        ),
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