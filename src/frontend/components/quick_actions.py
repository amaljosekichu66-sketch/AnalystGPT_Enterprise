"""
Quick Actions Component

Provides common dashboard actions.

Sprint 11
"""

from __future__ import annotations

import streamlit as st

from src.frontend.services.dashboard_service import (
    clear_dashboard_cache,
)
from src.frontend.services.report_service import (
    clear_reports_cache,
)
from src.frontend.services.session_manager import (
    clear_dataset,
)


def render_quick_actions() -> None:
    """
    Render dashboard quick actions.
    """

    st.subheader("⚡ Quick Actions")

    left, right = st.columns(
        2,
        gap="medium",
    )

    # ==========================================================
    # Navigation
    # ==========================================================

    with left:

        if st.button(
            "📁 Upload Dataset",
            width="stretch",
            type="primary",
        ):

            st.session_state["current_page"] = "Upload"

            st.rerun()

        if st.button(
            "📄 Reports Centre",
            width="stretch",
        ):

            st.session_state["current_page"] = "Reports"

            st.rerun()

        if st.button(
            "🧠 AI Insights",
            width="stretch",
        ):

            st.session_state["current_page"] = "AI Insights"

            st.rerun()

    # ==========================================================
    # Session Actions
    # ==========================================================

    with right:

        if st.button(
            "🔄 Refresh Dashboard",
            width="stretch",
        ):

            clear_dashboard_cache()
            clear_reports_cache()
            st.cache_data.clear()

            st.rerun()

        if st.button(
            "🧹 Clear Session",
            width="stretch",
        ):

            #
            # Preserve navigation state
            #

            current_page = st.session_state.get(
                "current_page",
                "Dashboard",
            )

            #
            # Clear only application data
            #

            clear_dataset()

            #
            # Clear Streamlit cache
            #

            st.cache_data.clear()

            #
            # Restore current page
            #

            st.session_state["current_page"] = current_page

            st.success("Session cleared successfully.")

            st.rerun()

    # ==========================================================
    # Information
    # ==========================================================

    st.caption(
        "Quick actions provide shortcuts to common "
        "workflow operations. Navigation is handled "
        "through Streamlit session state while "
        "business operations remain in the "
        "Application Layer."
    )
