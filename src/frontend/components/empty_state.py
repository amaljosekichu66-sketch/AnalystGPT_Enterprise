"""
Enterprise Empty State Component

Reusable across all frontend pages.

Sprint 11
"""

from __future__ import annotations

import streamlit as st


def render_empty_state(
    title: str,
    message: str,
    icon: str = "📂",
    button_label: str | None = None,
) -> bool:
    """
    Render a reusable enterprise empty state.

    Returns
    -------
    bool
        True when the optional button is clicked.
    """

    st.markdown("<br>", unsafe_allow_html=True)

    _, centre, _ = st.columns(
        [1, 2, 1],
    )

    clicked = False

    with centre:

        st.markdown(
            f"<h1 style='text-align:center'>{icon}</h1>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<h2 style='text-align:center'>{title}</h2>",
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                "<p style='text-align:center;"
                "color:grey;'>"
                f"{message}"
                "</p>"
            ),
            unsafe_allow_html=True,
        )

        if button_label:

            clicked = st.button(
                button_label,
                width="stretch",
            )

            #
            # Enterprise navigation
            #

            if clicked:

                st.session_state[
                    "current_page"
                ] = "Upload"

                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    return clicked