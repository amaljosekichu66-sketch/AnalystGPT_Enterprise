"""
Unit tests for frontend UX states (loading, empty, scroll, quick actions).

AnalystGPT Enterprise
Sprint 14 Phase 1 — Frontend UX Stabilization
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from src.frontend.components.empty_state import render_empty_state
from src.frontend.components.loading_state import loading
from src.frontend.components.quick_actions import render_quick_actions
from src.frontend.components.scroll_to_top import scroll_to_top


def test_scroll_to_top_renders_html():
    """Verify scroll_to_top executes HTML component without exceptions."""
    with patch("streamlit.components.v1.html") as mock_html:
        scroll_to_top()
        mock_html.assert_called_once()
        args, kwargs = mock_html.call_args
        assert "scrollTo" in args[0]
        assert kwargs["height"] == 0
        assert kwargs["width"] == 0


def test_render_empty_state_with_button_navigation():
    """Verify render_empty_state updates current_page and reruns when button clicked."""
    with (
        patch("streamlit.session_state", {}) as mock_state,
        patch("streamlit.button", return_value=True),
        patch("streamlit.rerun") as mock_rerun,
    ):

        clicked = render_empty_state(
            title="No Data",
            message="Please upload data",
            button_label="Upload Data",
            target_page="Upload",
        )

        assert clicked is True
        assert mock_state.get("current_page") == "Upload"
        mock_rerun.assert_called_once()


def test_render_empty_state_without_button():
    """Verify render_empty_state returns False when no button label is provided."""
    clicked = render_empty_state(
        title="Empty",
        message="No data found",
        button_label=None,
    )
    assert clicked is False


def test_loading_context_manager():
    """Verify loading context manager wraps execution with st.spinner."""
    with patch("streamlit.spinner") as mock_spinner:
        with loading("Processing test..."):
            pass
        mock_spinner.assert_called_once_with("Processing test...")


def test_quick_actions_renders():
    """Verify render_quick_actions renders navigation buttons and actions."""
    with patch("streamlit.button") as mock_btn, patch("streamlit.caption"):
        mock_btn.return_value = False
        render_quick_actions()
        assert mock_btn.call_count >= 4
