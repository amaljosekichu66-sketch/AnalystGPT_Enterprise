"""
Unit tests for frontend views rendering (AI Insights, Dashboard, Reports, About).

AnalystGPT Enterprise
Sprint 14 Phase 1 — Frontend UX Stabilization
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import streamlit as st

from src.frontend.views import (
    about_page,
    ai_insights_page,
    dashboard_page,
    report_page,
)


@pytest.fixture
def sample_dashboard_data():
    return {
        "dataset_loaded": True,
        "filename": "test.csv",
        "rows": 100,
        "columns": 5,
        "memory": 0.5,
        "missing": 2,
        "duplicates": 0,
        "numeric_columns": 3,
        "categorical_columns": 2,
        "execution_time": 1.2,
        "output_path": "reports/report.txt",
        "dataframe": pd.DataFrame({"col1": [1, 2, 3], "col2": ["A", "B", "C"]}),
        "backend_report": {"report": {"status": "SUCCESS"}},
        "ai_report": {
            "executive_summary": "Test executive summary.",
            "recommendations": ["Rec 1", "Rec 2"],
            "explanations": ["Exp 1"],
            "narrative": "Test narrative.",
            "model": "qwen3:8b",
            "provider": "ollama",
            "execution_time": 0.45,
        },
        "source": "api",
    }


def test_ai_insights_page_empty_state():
    """Verify AI Insights view renders empty state when no dataset is loaded."""
    with (
        patch("src.frontend.views.ai_insights_page.get_dashboard_data") as mock_data,
        patch("src.frontend.views.ai_insights_page.scroll_to_top") as mock_scroll,
        patch("src.frontend.views.ai_insights_page.render_empty_state") as mock_empty,
    ):
        mock_data.return_value = {"dataset_loaded": False}

        ai_insights_page.render()

        mock_scroll.assert_called_once()
        mock_empty.assert_called_once()
        args, kwargs = mock_empty.call_args
        assert kwargs["title"] == "No Dataset Available"


def test_ai_insights_page_with_insights(sample_dashboard_data):
    """Verify AI Insights view renders insights when ai_report is present."""
    with (
        patch("src.frontend.views.ai_insights_page.get_dashboard_data", return_value=sample_dashboard_data),
        patch("src.frontend.views.ai_insights_page.scroll_to_top") as mock_scroll,
        patch("src.frontend.views.ai_insights_page.render_ai_insights") as mock_render_insights,
    ):

        ai_insights_page.render()

        mock_scroll.assert_called_once()
        mock_render_insights.assert_called_once_with(sample_dashboard_data["ai_report"])


def test_dashboard_page_empty_state():
    """Verify Dashboard view renders empty state when no dataset is loaded."""
    with (
        patch("src.frontend.views.dashboard_page.get_dashboard_data") as mock_data,
        patch("src.frontend.views.dashboard_page.scroll_to_top") as mock_scroll,
        patch("src.frontend.views.dashboard_page.render_empty_state") as mock_empty,
    ):
        mock_data.return_value = {"dataset_loaded": False}

        dashboard_page.render()

        mock_scroll.assert_called_once()
        mock_empty.assert_called_once()
        args, kwargs = mock_empty.call_args
        assert kwargs["title"] == "No Dataset Loaded"


def test_dashboard_page_hierarchy(sample_dashboard_data):
    """Verify Dashboard view renders KPI cards, pipeline status, and data tabs without embedded AI insights."""
    with (
        patch("src.frontend.views.dashboard_page.get_dashboard_data", return_value=sample_dashboard_data),
        patch("src.frontend.views.dashboard_page.scroll_to_top") as mock_scroll,
        patch("src.frontend.views.dashboard_page.render_kpi_cards") as mock_kpis,
        patch("src.frontend.views.dashboard_page.render_pipeline_status") as mock_pipe,
        patch("src.frontend.views.dashboard_page.render_dashboard_summary") as mock_sum,
        patch("src.frontend.views.dashboard_page.render_quick_actions") as mock_qa,
    ):

        dashboard_page.render()

        mock_scroll.assert_called_once()
        mock_kpis.assert_called_once_with(sample_dashboard_data)
        mock_pipe.assert_called_once_with(sample_dashboard_data)
        mock_sum.assert_called_once_with(sample_dashboard_data)
        mock_qa.assert_called_once()


def test_report_page_empty_state():
    """Verify Reports view renders empty state when no dataset is loaded."""
    with (
        patch("src.frontend.views.report_page.get_report_data") as mock_data,
        patch("src.frontend.views.report_page.scroll_to_top") as mock_scroll,
        patch("src.frontend.views.report_page.render_empty_state") as mock_empty,
    ):
        mock_data.return_value = {"dataset_loaded": False}

        report_page.render()

        mock_scroll.assert_called_once()
        mock_empty.assert_called_once()


def test_about_page_render():
    """Verify About view calls scroll_to_top and renders about card."""
    with (
        patch("src.frontend.views.about_page.scroll_to_top") as mock_scroll,
        patch("src.frontend.views.about_page.render_about_card") as mock_card,
    ):
        about_page.render()
        mock_scroll.assert_called_once()
        mock_card.assert_called_once()
