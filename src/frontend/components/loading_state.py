"""
Enterprise Loading Component
============================

Reusable loading component for AnalystGPT Enterprise.

Purpose
-------
Provides a consistent loading experience across the
frontend application.

Used by
-------
- Upload Page
- Dashboard
- Reports
- Future AI Insights
- Future React Frontend

Sprint
------
Sprint 10
"""

from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


@contextmanager
def loading(
    message: str = "Loading...",
):
    """
    Display a reusable loading spinner.

    Parameters
    ----------
    message:
        Loading message displayed to the user.

    Example
    -------
    >>> with loading("Generating report..."):
    ...     generate_report()
    """

    with st.spinner(message):
        yield


def show_loading_message(
    title: str,
    description: str,
) -> None:
    """
    Display a centered loading message.

    Parameters
    ----------
    title:
        Main loading title.

    description:
        Supporting loading description.
    """

    left, centre, right = st.columns([1, 2, 1])

    with centre:

        st.markdown(
            f"""
            <div style="text-align:center; padding:30px;">
                <h2>⏳ {title}</h2>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_progress(
    progress: float,
    text: str = "Processing...",
) -> None:
    """
    Display a progress indicator.

    Parameters
    ----------
    progress:
        Progress between 0.0 and 1.0.

    text:
        Progress description.
    """

    progress = max(0.0, min(progress, 1.0))

    st.progress(progress)

    st.caption(text)
