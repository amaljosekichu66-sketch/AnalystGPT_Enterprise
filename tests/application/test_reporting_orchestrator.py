"""
Tests for Reporting Orchestrator.

Sprint 14 Phase 5 — Reporting & PDF Export Stabilization.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.ai.ai_report import AIReport
from src.ai.ai_result import AIResult
from src.application.app import Application
from src.application.reporting_orchestrator import ReportingOrchestrator
from src.identity.context import UserContext
from src.identity.models import UserRole


def _get_mock_ai_result():
    return AIResult(
        success=True,
        ai_report=AIReport(
            executive_summary="AI Executive Summary",
            recommendations=["AI Recommendation 1"],
            explanations=["AI Diagnostic Explanation"],
            narrative="AI Narrative Story",
            model="gemma3:4b",
            provider="ollama",
            execution_time=0.1,
        ),
    )


@pytest.fixture
def mock_application(tmp_path):
    app = Application()
    user_ctx = UserContext(
        user_id=1,
        username="test_user",
        email="test@example.com",
        role=UserRole.ANALYST,
    )
    with patch.object(app.ai_manager, "generate_ai_report", return_value=_get_mock_ai_result()):
        app.run("sample_data/customer_data.csv", user_context=user_ctx)
    return app


def test_reporting_orchestrator_get_reports(mock_application):
    orchestrator = ReportingOrchestrator(mock_application)
    data = orchestrator.get_reports(user_id=1)

    assert data["report"] is not None
    assert data["report"]["report"]["title"] == "AnalystGPT Enterprise Report"
    assert len(data["reports"]) >= 4


def test_reporting_orchestrator_export_text_and_pdf(mock_application, tmp_path):
    orchestrator = ReportingOrchestrator(mock_application)

    text_res = orchestrator.export_text_report(user_id=1, output_path=tmp_path / "report.txt")
    assert text_res["success"] is True
    assert Path(text_res["path"]).exists()
    assert text_res["mime_type"] == "text/plain"

    pdf_res = orchestrator.export_pdf_report(user_id=1, output_path=tmp_path / "report.pdf")
    assert pdf_res["success"] is True
    assert Path(pdf_res["path"]).exists()
    assert pdf_res["mime_type"] == "application/pdf"
    with open(pdf_res["path"], "rb") as f:
        assert f.read(5).startswith(b"%PDF-")


def test_reporting_orchestrator_missing_user_report(mock_application):
    orchestrator = ReportingOrchestrator(mock_application)
    data = orchestrator.get_reports(user_id=999)
    assert data["report"] is None
    assert data["reports"] == []
