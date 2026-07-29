"""
Unit tests for PromptBuilder.
"""

from typing import Any

from src.llm.prompt_builder import PromptBuilder


# ----------------------------------------------------------------------
# Stub for StructuredReport
# ----------------------------------------------------------------------

class FakeStructuredReport:
    """StructuredReport stub used by PromptBuilder tests."""

    def __init__(self) -> None:
        self.executive_summary = (
            "Fortune 500 Enterprise Analytics Report. "
            "Revenue increased by 18% with strong growth."
        )

        self.kpis = {
            "Revenue": "+18%",
            "Profit Margin": "22%",
            "Customer Satisfaction": "92%",
        }

        self.recommendations = [
            "Increase marketing spend in Q3",
            "Optimize pricing strategy",
            "Expand to APAC region",
        ]

        self.analytics = {
            "descriptive_statistics": {
                "mean": 42,
                "std": 5,
            },
            "correlation_analysis": {
                "price_sales": -0.75,
            },
            "distribution_analysis": {
                "skew": 0.2,
            },
            "categorical_analysis": {
                "top_category": "Electronics",
            },
        }


# ----------------------------------------------------------------------
# Stub for ReportingReport
# ----------------------------------------------------------------------

class FakeReportingReport:
    """Minimal ReportingReport stub."""

    def __init__(
        self,
        execution_time: float = 0.42,
        report: Any | None = None,
    ) -> None:
        self.execution_time = execution_time
        self.export_path = "reports/report.txt"

        if report is None:
            self.report = FakeStructuredReport()
        else:
            self.report = report


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_executive_summary_prompt() -> None:
    prompt = PromptBuilder.executive_summary(
        FakeReportingReport(),
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 100
    assert "Fortune 500" in prompt
    assert "Enterprise Analytics Report" in prompt


def test_recommendation_prompt() -> None:
    prompt = PromptBuilder.recommendations(
        FakeReportingReport(),
    )

    assert "recommendations" in prompt.lower()


def test_explanation_prompt() -> None:
    prompt = PromptBuilder.explanations(
        FakeReportingReport(),
    )

    # Verify the explanation instructions are present.
    assert "explain the analytical findings" in prompt.lower()
    assert "professional business language" in prompt.lower()


def test_narrative_prompt() -> None:
    prompt = PromptBuilder.narrative(
        FakeReportingReport(),
    )

    assert "board-level" in prompt.lower()
    assert "professional executive tone" in prompt.lower()