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

from src.frontend.components.safe_text import html_text


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
