"""
Enterprise Footer Component
===========================

Reusable footer displayed across AnalystGPT Enterprise.

Purpose
-------
Provides consistent application branding,
version information and technology stack.

Sprint
------
Sprint 10
"""

from __future__ import annotations

import streamlit as st


APP_NAME = "AnalystGPT Enterprise"
VERSION = "v10.0.0"
LICENSE = "MIT License"

TECH_STACK = (
    "Python • Streamlit • FastAPI • PostgreSQL • SQLite • Pandas"
)


def render_footer() -> None:
    """
    Render the application footer.
    """

    st.divider()

    left, centre, right = st.columns(
        [2, 2, 2]
    )

    with left:

        st.caption(APP_NAME)

        st.caption(VERSION)

    with centre:

        st.caption(TECH_STACK)

    with right:

        st.caption(LICENSE)

        st.caption("© 2026 Amal Jose")