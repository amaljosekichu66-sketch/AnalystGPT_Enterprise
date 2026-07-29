"""
Enterprise Footer Component

Reusable footer displayed across AnalystGPT Enterprise.
"""

from __future__ import annotations

import streamlit as st

from src.core.constants import (
    APP_NAME,
    APP_VERSION,
)


TECH_STACK = (
    "Python • Streamlit • FastAPI • PostgreSQL • "
    "SQLite • Pandas • Plotly • Power BI • Ollama"
)


def render_footer() -> None:
    """
    Render the enterprise footer.
    """

    st.divider()

    left, centre, right = st.columns(
        [2, 3, 2],
    )

    with left:

        st.caption(APP_NAME)

        st.caption(
            f"Version {APP_VERSION}"
        )

    with centre:

        st.caption(
            TECH_STACK
        )

    with right:

        st.caption(
            "MIT License"
        )

        st.caption(
            "© 2026 Amal Jose"
        )