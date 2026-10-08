"""
Unit tests for frontend navigation and role-aware routing.

AnalystGPT Enterprise
Sprint 14 Phase 1 — Frontend UX Stabilization
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from src.frontend.pages import PAGES


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
