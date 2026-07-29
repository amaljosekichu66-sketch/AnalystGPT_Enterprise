"""
Unit tests for RecommendationEngine.
"""

from __future__ import annotations

import pytest

from src.ai.recommendation_engine import (
    RecommendationEngine,
)
from src.llm.base_llm import BaseLLM


# ==========================================================
# Fake LLMs
# ==========================================================

class SuccessfulLLM(BaseLLM):
    """
    Returns recommendations.
    """

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return """
Improve data completeness.
Increase customer retention.
Monitor revenue monthly.
Reduce duplicate records.
Improve regional marketing.
"""


class EmptyLLM(BaseLLM):

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return ""


class ExceptionLLM(BaseLLM):

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        raise RuntimeError(
            "LLM failure."
        )


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
        self.execution_time = 0.5
        self.export_path = "reports/report.txt"   # Not used but kept for completeness
        self.report = FakeStructuredReport()


# ==========================================================
# Tests
# ==========================================================

def test_generate_recommendations_success():

    engine = RecommendationEngine(
        SuccessfulLLM()
    )

    recommendations = (
        engine.generate_recommendations(
            FakeReportingReport()
        )
    )

    assert isinstance(
        recommendations,
        list,
    )

    assert len(recommendations) > 0


def test_recommendations_are_strings():

    engine = RecommendationEngine(
        SuccessfulLLM()
    )

    recommendations = (
        engine.generate_recommendations(
            FakeReportingReport()
        )
    )

    assert all(
        isinstance(item, str)
        for item in recommendations
    )


def test_empty_response():

    engine = RecommendationEngine(
        EmptyLLM()
    )

    with pytest.raises(
        ValueError
    ):

        engine.generate_recommendations(
            FakeReportingReport()
        )


def test_llm_exception():

    engine = RecommendationEngine(
        ExceptionLLM()
    )

    with pytest.raises(
        RuntimeError
    ):

        engine.generate_recommendations(
            FakeReportingReport()
        )