"""
Quick actions component for AnalystGPT Enterprise.
"""

from __future__ import annotations

import streamlit as st


def render_quick_actions() -> None:
    """
    Render enterprise dashboard quick actions.
    """

    st.subheader("⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📁 Upload Dataset",
            use_container_width=True,
            type="primary",
        ):
            st.info(
                "Navigate to the Upload page using the "
                "sidebar to upload another dataset."
            )

        if st.button(
            "📄 View Reports",
            use_container_width=True,
        ):
            st.info(
                "Open the Reports page from the sidebar "
                "to preview generated reports."
            )

    with col2:

        if st.button(
            "🔄 Refresh Dashboard",
            use_container_width=True,
        ):
            st.rerun()

        if st.button(
            "🧹 Clear Session",
            use_container_width=True,
        ):
            st.session_state.clear()
            st.success("Session cleared successfully.")
            st.rerun()

    st.caption(
        "Quick Actions provide shortcuts to common "
        "operations. Additional workflow automation "
        "will be introduced in Sprint 11."
    )