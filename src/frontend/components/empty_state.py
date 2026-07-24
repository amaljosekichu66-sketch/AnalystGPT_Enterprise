"""
Enterprise Empty State Component

Reusable across all frontend pages.

Sprint 10
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

    Parameters
    ----------
    title:
        Empty-state title.

    message:
        Supporting message.

    icon:
        Emoji icon.

    button_label:
        Optional button.

    Returns
    -------
    bool
        True when optional button is clicked.
    """

    st.markdown("<br>", unsafe_allow_html=True)

    left, centre, right = st.columns([1, 2, 1])

    clicked = False

    with centre:

        st.markdown(
            f"<h1 style='text-align:center'>{icon}</h1>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<h3 style='text-align:center'>{title}</h3>",
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

        if button_label is not None:

            clicked = st.button(
                button_label,
                use_container_width=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    return clicked