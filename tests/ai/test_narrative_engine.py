"""
Unit tests for NarrativeEngine.
"""

from __future__ import annotations

import pytest

from src.ai.narrative_engine import NarrativeEngine
from src.llm.base_llm import BaseLLM

# ==========================================================
# Fake LLMs
# ==========================================================


class SuccessfulLLM(BaseLLM):
    """
    Returns a narrative.
    """

    @property
    def model(self) -> str:
        return "fake-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return (
            "Overall business performance remained stable. "
            "Data quality was high, enabling reliable analytics. "
            "Revenue increased while customer retention improved."
        )


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


def test_generate_narrative_success():
    """
    Verify narrative generation succeeds.
    """

    engine = NarrativeEngine(SuccessfulLLM())

    report = FakeReportingReport()

    narrative = engine.generate_narrative(report)

    assert isinstance(
        narrative,
        str,
    )

    assert len(narrative) > 50


def test_narrative_not_empty():
    """
    Narrative should not be empty.
    """

    engine = NarrativeEngine(SuccessfulLLM())

    report = FakeReportingReport()

    narrative = engine.generate_narrative(report)

    assert narrative.strip() != ""


def test_empty_response():
    """
    Empty LLM responses should raise ValueError.
    """

    engine = NarrativeEngine(EmptyLLM())

    report = FakeReportingReport()

    with pytest.raises(ValueError):

        engine.generate_narrative(report)


def test_llm_exception():
    """
    LLM exceptions should propagate.
    """

    engine = NarrativeEngine(ExceptionLLM())

    report = FakeReportingReport()

    with pytest.raises(RuntimeError):

        engine.generate_narrative(report)
