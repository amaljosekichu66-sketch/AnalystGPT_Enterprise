"""
Unit tests for ExecutiveSummaryEngine.
"""

from __future__ import annotations

import pytest

from src.ai.executive_summary_engine import (
    ExecutiveSummaryEngine,
)
from src.llm.base_llm import BaseLLM

# ==========================================================
# Fake LLMs
# ==========================================================


class SuccessfulLLM(BaseLLM):
    """
    Returns a valid executive summary.
    """

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return "The dataset demonstrates strong overall " "quality with positive business performance."


class EmptyLLM(BaseLLM):
    """
    Returns an empty response.
    """

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return ""


class ExceptionLLM(BaseLLM):
    """
    Raises an exception.
    """

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        raise RuntimeError("LLM unavailable.")


# ==========================================================
# Fake StructuredReport and ReportingReport
# ==========================================================


class FakeStructuredReport:
    """
    Stub for StructuredReport that exactly matches what ReportSerializer uses.
    """

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
    """
    Stub for ReportingReport that provides a .report attribute containing
    a FakeStructuredReport.
    """

    def __init__(self):
        self.execution_time = 0.42
        self.export_path = "reports/report.txt"  # Not used but kept for completeness
        self.report = FakeStructuredReport()


# ==========================================================
# Tests
# ==========================================================


def test_generate_summary_success():

    engine = ExecutiveSummaryEngine(SuccessfulLLM())

    summary = engine.generate_summary(FakeReportingReport())

    assert isinstance(
        summary,
        str,
    )

    assert len(summary) > 20

    assert "business" in summary.lower()


def test_generate_summary_not_empty():

    engine = ExecutiveSummaryEngine(SuccessfulLLM())

    summary = engine.generate_summary(FakeReportingReport())

    assert summary.strip() != ""


def test_empty_response():

    engine = ExecutiveSummaryEngine(EmptyLLM())

    with pytest.raises(ValueError):

        engine.generate_summary(FakeReportingReport())


def test_llm_exception():

    engine = ExecutiveSummaryEngine(ExceptionLLM())

    with pytest.raises(RuntimeError):

        engine.generate_summary(FakeReportingReport())
