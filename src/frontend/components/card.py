"""
Enterprise Card Component

Reusable container used throughout
AnalystGPT Enterprise.

Sprint 10
"""

from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


@contextmanager
def render_card(
    title: str | None = None,
):
    """
    Render a reusable enterprise card.
    """

    with st.container(border=True):

        if title:

            st.subheader(title)

        yield
