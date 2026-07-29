"""
Unit tests for AIManager.

These tests verify the AI insight engine integration using the unified
report generator. The AIManager uses UnifiedReportEngine internally.

LLMFactory.create() is mocked via an autouse fixture to avoid external
dependencies and keep the tests isolated.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.ai.ai_manager import AIManager
from src.ai.ai_report import AIReport
from src.ai.unified_report_engine import AISections


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture
def fake_llm():
    """Return a fake LLM instance with a model attribute."""
    llm = MagicMock()
    llm.model = "test-model"
    return llm


@pytest.fixture(autouse=True)
def mock_llm_factory(fake_llm):
    """
    Automatically patch LLMFactory.create so that every test gets a fake LLM.
    This avoids repeating the mock setup in each test.
    """
    with patch("src.ai.ai_manager.LLMFactory.create") as mock_factory:
        mock_factory.return_value = fake_llm
        yield mock_factory


# ==========================================================
# Fake ReportingReport (matches ReportSerializer expectations)
# ==========================================================

class FakeStructuredReport:
    """Stub for StructuredReport with attributes used by the serializer."""

    def __init__(self):
        self.executive_summary = "Sample executive summary."
        self.kpis = {"Revenue": "1.2M", "Growth": "18%"}
        self.recommendations = ["Increase marketing spend", "Optimize pricing"]
        self.analytics = {
            "descriptive_statistics": {"mean": 42, "std": 5},
            "correlation_analysis": {"price_sales": -0.75},
            "distribution_analysis": {"skew": 0.2},
            "categorical_analysis": {"top_category": "Electronics"},
        }


class FakeReportingReport:
    """Stub for ReportingReport that exposes a .report attribute."""

    def __init__(self):
        self.execution_time = 0.50
        self.export_path = "reports/report.txt"
        self.report = FakeStructuredReport()


# ==========================================================
# Helper: create real AISections objects
# ==========================================================

def create_sections(**overrides) -> AISections:
    """
    Return a real AISections instance with default or overridden values.
    """
    defaults = {
        "executive_summary": "Executive summary.",
        "recommendations": ["Recommendation 1", "Recommendation 2"],
        "explanations": ["Explanation 1", "Explanation 2"],
        "narrative": "Business narrative.",
    }
    defaults.update(overrides)
    return AISections(**defaults)


# ==========================================================
# Tests
# ==========================================================

@patch("src.ai.ai_manager.UnifiedReportEngine.generate")
def test_generate_ai_report_success(mock_generate):
    """
    Test successful AI report generation.
    """
    report = FakeReportingReport()
    mock_generate.return_value = create_sections()

    manager = AIManager()
    result = manager.generate_ai_report(report)

    mock_generate.assert_called_once_with(report)

    assert result.success is True
    assert isinstance(result.ai_report, AIReport)
    assert result.ai_report.executive_summary == "Executive summary."
    assert result.ai_report.recommendations == ["Recommendation 1", "Recommendation 2"]
    assert result.ai_report.explanations == ["Explanation 1", "Explanation 2"]
    assert result.ai_report.narrative == "Business narrative."
    assert result.error is None
    assert result.execution_time > 0
    assert result.ai_report.prompt_count == 1
    assert result.ai_report.model == "test-model"


@patch("src.ai.ai_manager.UnifiedReportEngine.generate")
def test_generate_ai_report_failure(mock_generate):
    """
    Test that AIManager captures exceptions from the engine.
    """
    report = FakeReportingReport()
    mock_generate.side_effect = RuntimeError("LLM unavailable.")

    manager = AIManager()
    result = manager.generate_ai_report(report)

    mock_generate.assert_called_once_with(report)

    assert result.success is False
    assert result.ai_report is None
    assert isinstance(result.error, RuntimeError)
    assert str(result.error) == "LLM unavailable."
    assert result.execution_time > 0


@patch("src.ai.ai_manager.UnifiedReportEngine.generate")
def test_ai_report_metadata(mock_generate):
    """
    Test that AIReport contains metadata and prompt_count is 1.
    """
    report = FakeReportingReport()
    mock_generate.return_value = create_sections()

    manager = AIManager()
    result = manager.generate_ai_report(report)

    mock_generate.assert_called_once_with(report)

    ai_report = result.ai_report
    assert ai_report is not None

    # Verify provider and model are non‑empty strings
    assert isinstance(ai_report.provider, str)
    assert ai_report.provider
    assert isinstance(ai_report.model, str)
    assert ai_report.model == "test-model"

    assert ai_report.execution_time > 0
    assert ai_report.prompt_count == 1
    assert isinstance(ai_report.generated_at, datetime)


@patch("src.ai.ai_manager.UnifiedReportEngine.generate")
def test_execution_time(mock_generate):
    """
    Test that execution time is captured.
    """
    report = FakeReportingReport()
    mock_generate.return_value = create_sections()

    manager = AIManager()
    result = manager.generate_ai_report(report)

    mock_generate.assert_called_once_with(report)

    assert result.execution_time > 0


@patch("src.ai.ai_manager.UnifiedReportEngine.generate")
def test_generate_ai_report_with_none_report(mock_generate):
    """
    Test that passing None returns a failure result without calling the engine.
    """
    manager = AIManager()
    result = manager.generate_ai_report(None)

    assert result.success is False
    assert result.ai_report is None
    assert isinstance(result.error, ValueError)
    assert "reporting_report cannot be None" in str(result.error)
    assert result.execution_time >= 0

    # Ensure the engine's generate method was never called
    mock_generate.assert_not_called()


@patch("src.ai.ai_manager.UnifiedReportEngine.generate")
def test_invalid_sections_type(mock_generate):
    """
    Test that AIManager raises a TypeError if the engine does not return AISections.
    """
    report = FakeReportingReport()
    mock_generate.return_value = {"executive_summary": "Oops"}

    manager = AIManager()
    result = manager.generate_ai_report(report)

    # The engine was called (it returned something, but wrong type)
    mock_generate.assert_called_once_with(report)

    assert result.success is False
    assert result.ai_report is None
    assert isinstance(result.error, TypeError)
    assert "UnifiedReportEngine must return AISections" in str(result.error)


@patch("src.ai.ai_manager.UnifiedReportEngine.generate")
def test_missing_section_raises_value_error(mock_generate):
    """
    Test that a missing (None) section raises ValueError.
    """
    report = FakeReportingReport()
    # Create sections with executive_summary=None directly (dataclass is frozen)
    sections = create_sections(executive_summary=None)
    mock_generate.return_value = sections

    manager = AIManager()
    result = manager.generate_ai_report(report)

    # The engine was called (it returned AISections, but one field is None)
    mock_generate.assert_called_once_with(report)

    assert result.success is False
    assert result.ai_report is None
    assert isinstance(result.error, ValueError)
    assert "Section 'executive_summary' is None" in str(result.error)