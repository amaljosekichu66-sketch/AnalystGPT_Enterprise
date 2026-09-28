"""
Regression tests for AI Evidence Grounding and Categorical Serialization Remediation.

Sprint 14 Remediation — AI Grounding & Categorical Precision.

Verifies:
1. Distinct category cardinality (e.g. unique_values=7) is explicitly labeled as cardinality and distinguished from percentage frequency.
2. Top value percentage (e.g. 35.7%) is explicitly calculated and labeled as percentage.
3. Top value count (e.g. 528) is explicitly preserved as exact integer record count.
4. "Most frequent category" is not converted to "dominant" unless majority is proven.
5. PromptBuilder includes explicit anti-conflation and non-dominant category guidelines.
"""

from typing import Any

from src.llm.prompt_builder import PromptBuilder
from src.llm.report_serializer import ReportSerializer


class FakeStructuredReport:
    """Mock structured report containing realistic categorical analytics."""

    def __init__(
        self,
        analytics: dict[str, Any] | None = None,
        kpis: dict[str, Any] | None = None,
    ) -> None:
        self.executive_summary = "Deterministic summary baseline."
        self.kpis = kpis or {"Rows": 1480, "Columns": 13}
        self.recommendations = ["Review lead status distribution"]
        self.analytics = analytics or {
            "descriptive_statistics": {"total_rows": 1480, "total_columns": 13},
            "categorical_analysis": {
                "review_status": {
                    "count": 1480,
                    "missing_values": 0,
                    "unique_values": 7,
                    "top_value": "No Evidence Submitted",
                    "top_frequency": 528,
                    "value_distribution": {
                        "No Evidence Submitted": 528,
                        "Evidence Needs To Be Checked": 338,
                        "Full Evidence": 335,
                        "Facebook Screenshot Only": 141,
                        "Valid Subscription Evidence": 70,
                    },
                },
                "state": {
                    "count": 1480,
                    "missing_values": 0,
                    "unique_values": 102,
                    "top_value": "Tx",
                    "top_frequency": 58,
                    "value_distribution": {
                        "Tx": 58,
                        "Ny": 49,
                        "Ca": 49,
                        "Pa": 47,
                        "New York": 36,
                    },
                },
                "city": {
                    "count": 1480,
                    "missing_values": 0,
                    "unique_values": 1085,
                    "top_value": "Holtsville",
                    "top_frequency": 16,
                    "value_distribution": {
                        "Holtsville": 16,
                        "New Brunswick": 12,
                    },
                },
            },
        }


class FakeReportingReport:
    """Mock ReportingReport wrapping structured report."""

    def __init__(self, report: Any | None = None) -> None:
        self.execution_time = 0.05
        self.report = report or FakeStructuredReport()


def test_cardinality_is_explicitly_labeled_not_percentage() -> None:
    """
    Test 1: unique_values=7 must be explicitly labeled as distinct category count/cardinality,
    NEVER formatted as '7%' or bare '7'.
    """
    report = FakeReportingReport()
    serialized = ReportSerializer.serialize(report)

    # Cardinality must be explicitly labeled
    assert "distinct_category_count: 7 (distinct categories / cardinality count, NOT percentage)" in serialized
    assert "distinct_category_count: 102 (distinct categories / cardinality count, NOT percentage)" in serialized
    assert "distinct_category_count: 1085 (distinct categories / cardinality count, NOT percentage)" in serialized


def test_top_value_count_and_percentage_preserved() -> None:
    """
    Test 2 & 3: top_value_count=528 and top_value_percentage=35.7% are explicitly derived and serialized.
    """
    report = FakeReportingReport()
    serialized = ReportSerializer.serialize(report)

    # review_status top category: 528 records (35.7%)
    assert 'value: "No Evidence Submitted"' in serialized
    assert "count: 528 records" in serialized
    assert "percentage: 35.7%" in serialized

    # state top category: 58 records (3.9%)
    assert 'value: "Tx"' in serialized
    assert "count: 58 records" in serialized
    assert "percentage: 3.9%" in serialized

    # city top category: 16 records (1.1%)
    assert 'value: "Holtsville"' in serialized
    assert "count: 16 records" in serialized
    assert "percentage: 1.1%" in serialized


def test_category_distribution_breakdown_shares() -> None:
    """
    Test that category distribution includes exact record counts and percentage shares.
    """
    report = FakeReportingReport()
    serialized = ReportSerializer.serialize(report)

    assert '"No Evidence Submitted": 528 records | 35.7%' in serialized
    assert '"Evidence Needs To Be Checked": 338 records | 22.8%' in serialized
    assert '"Tx": 58 records | 3.9%' in serialized
    assert '"Holtsville": 16 records | 1.1%' in serialized


def test_prompt_builder_includes_grounding_rules() -> None:
    """
    Test 4 & 5: PromptBuilder full_report includes explicit anti-conflation and non-dominant category guidelines.
    """
    report = FakeReportingReport()
    prompt = PromptBuilder.full_report(report)

    assert "CARDINALITY VS PERCENTAGE FREQUENCY (CRITICAL)" in prompt
    assert (
        "Never confuse distinct category count / cardinality (e.g. '7 unique categories') with percentage frequency"
        in prompt
    )
    assert "GROUNDED CATEGORICAL TERMINOLOGY (NO FALSE DOMINANCE)" in prompt
    assert "Do NOT describe a top category as 'dominant'" in prompt
    assert "the most frequent category with X records (Y%)" in prompt
