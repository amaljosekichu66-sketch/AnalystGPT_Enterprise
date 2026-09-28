"""
Unit tests for ExplanationEngine.
"""

from __future__ import annotations

import pytest

from src.ai.explanation_engine import ExplanationEngine
from src.llm.base_llm import BaseLLM

# ==========================================================
# Fake LLMs
# ==========================================================


class SuccessfulLLM(BaseLLM):
    """
    Returns multiple explanations.
    """

    @property
    def model(self) -> str:
        return "fake-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return "Explanation A\n" "Explanation B\n" "Explanation C"


class EmptyLLM(BaseLLM):
    """
    Returns an empty response.
    """

    @property
    def model(self) -> str:
        return "fake-model"

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
        return "fake-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        raise RuntimeError("LLM unavailable.")


# ==========================================================
# Fake ReportingReport (with required attributes)
# ==========================================================


class FakeStructuredReport:
    def __init__(self):
        self.executive_summary = "Test summary"
        self.kpis = {"Rows": 10}
        self.recommendations = ["Do something"]
        self.analytics = {
            "descriptive_statistics": {"mean": 5},
            "correlation_analysis": {},
            "distribution_analysis": {},
            "categorical_analysis": {},
        }


class FakeReportingReport:
    def __init__(self):
        self.report = FakeStructuredReport()
        self.execution_time = 0.1234  # Required by ReportSerializer
        self.export_path = "reports/test.txt"


# ==========================================================
# Tests
# ==========================================================


def test_generate_explanations_success():
    """
    Verify explanations are generated correctly.
    """

    engine = ExplanationEngine(SuccessfulLLM())

    report = FakeReportingReport()

    explanations = engine.generate_explanations(report)

    assert isinstance(
        explanations,
        list,
    )

    assert len(explanations) == 3

    assert explanations[0] == "Explanation A"

    assert explanations[1] == "Explanation B"

    assert explanations[2] == "Explanation C"


def test_explanations_are_strings():
    """
    Every explanation should be a string.
    """

    engine = ExplanationEngine(SuccessfulLLM())

    report = FakeReportingReport()

    explanations = engine.generate_explanations(report)

    assert all(isinstance(item, str) for item in explanations)


def test_empty_response():
    """
    Empty LLM responses should raise ValueError.
    """

    engine = ExplanationEngine(EmptyLLM())

    report = FakeReportingReport()

    with pytest.raises(ValueError):

        engine.generate_explanations(report)


def test_llm_exception():
    """
    LLM exceptions should propagate.
    """

    engine = ExplanationEngine(ExceptionLLM())

    report = FakeReportingReport()

    with pytest.raises(RuntimeError):

        engine.generate_explanations(report)
