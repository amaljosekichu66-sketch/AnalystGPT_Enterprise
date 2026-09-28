"""
Unit tests for frontend navigation and role-aware routing.

AnalystGPT Enterprise
Sprint 14 Phase 1 — Frontend UX Stabilization
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from src.frontend.components.sidebar import render_sidebar
from src.frontend.config.settings import (
    ABOUT_PAGE,
    ADMIN_PAGE,
    AI_INSIGHTS_PAGE,
    DASHBOARD_PAGE,
    REPORTS_PAGE,
    SIGN_IN_PAGE,
    UPLOAD_PAGE,
)
from src.frontend.streamlit_app import PAGES


def test_pages_router_contains_all_views():
    """Verify all views including AI Insights are registered in PAGES dictionary."""
    expected_pages = {
        "Dashboard",
        "Upload",
        "Reports",
        "AI Insights",
        "Admin",
        "About",
        "Sign In",
    }
    assert set(PAGES.keys()) == expected_pages


def test_page_constants_defined():
    """Verify navigation constants are properly defined in settings."""
    assert DASHBOARD_PAGE == "Dashboard"
    assert UPLOAD_PAGE == "Upload"
    assert REPORTS_PAGE == "Reports"
    assert AI_INSIGHTS_PAGE == "AI Insights"
    assert ADMIN_PAGE == "Admin"
    assert ABOUT_PAGE == "About"
    assert SIGN_IN_PAGE == "Sign In"


@patch("src.frontend.components.sidebar.is_authenticated")
@patch("src.frontend.components.sidebar.is_admin")
@patch("src.frontend.components.sidebar.get_current_user")
@patch("src.frontend.components.sidebar.get_user_role")
@patch("src.frontend.components.sidebar.has_dataset")
def test_sidebar_authenticated_analyst_options(
    mock_has_dataset,
    mock_get_role,
    mock_get_user,
    mock_is_admin,
    mock_is_auth,
):
    """Verify sidebar hides Admin page for non-admin authenticated users."""
    mock_is_auth.return_value = True
    mock_is_admin.return_value = False
    mock_get_user.return_value = {"username": "analyst1"}
    mock_get_role.return_value = "ANALYST"
    mock_has_dataset.return_value = True

    with patch("streamlit.sidebar.radio") as mock_radio, patch("streamlit.sidebar.button") as mock_btn:
        mock_radio.return_value = "Dashboard"
        mock_btn.return_value = False

        selected = render_sidebar()

        assert selected == "Dashboard"
        # Verify navigation options passed to radio
        args, kwargs = mock_radio.call_args
        nav_options = args[1]
        assert DASHBOARD_PAGE in nav_options
        assert UPLOAD_PAGE in nav_options
        assert REPORTS_PAGE in nav_options
        assert AI_INSIGHTS_PAGE in nav_options
        assert ABOUT_PAGE in nav_options
        assert ADMIN_PAGE not in nav_options


@patch("src.frontend.components.sidebar.is_authenticated")
@patch("src.frontend.components.sidebar.is_admin")
@patch("src.frontend.components.sidebar.get_current_user")
@patch("src.frontend.components.sidebar.get_user_role")
@patch("src.frontend.components.sidebar.has_dataset")
def test_sidebar_authenticated_admin_options(
    mock_has_dataset,
    mock_get_role,
    mock_get_user,
    mock_is_admin,
    mock_is_auth,
):
    """Verify sidebar exposes Admin page for admin authenticated users."""
    mock_is_auth.return_value = True
    mock_is_admin.return_value = True
    mock_get_user.return_value = {"username": "admin1"}
    mock_get_role.return_value = "ADMIN"
    mock_has_dataset.return_value = False

    with patch("streamlit.sidebar.radio") as mock_radio, patch("streamlit.sidebar.button") as mock_btn:
        mock_radio.return_value = "Admin"
        mock_btn.return_value = False

        selected = render_sidebar()

        assert selected == "Admin"
        args, kwargs = mock_radio.call_args
        nav_options = args[1]
        assert DASHBOARD_PAGE in nav_options
        assert UPLOAD_PAGE in nav_options
        assert REPORTS_PAGE in nav_options
        assert AI_INSIGHTS_PAGE in nav_options
        assert ADMIN_PAGE in nav_options
        assert ABOUT_PAGE in nav_options


@patch("src.frontend.components.sidebar.is_authenticated")
def test_sidebar_unauthenticated_options(mock_is_auth):
    """Verify sidebar presents only Sign In and About to unauthenticated users."""
    mock_is_auth.return_value = False

    with patch("streamlit.sidebar.radio") as mock_radio:
        mock_radio.return_value = "Sign In"

        selected = render_sidebar()

        assert selected == "Sign In"
        args, kwargs = mock_radio.call_args
        nav_options = args[1]
        assert SIGN_IN_PAGE in nav_options
        assert ABOUT_PAGE in nav_options
        assert DASHBOARD_PAGE not in nav_options
        assert AI_INSIGHTS_PAGE not in nav_options
        assert ADMIN_PAGE not in nav_options
