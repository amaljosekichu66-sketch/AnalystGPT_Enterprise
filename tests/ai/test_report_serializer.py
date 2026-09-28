"""
Unit tests for ReportSerializer.
"""

from typing import Any, Mapping

from src.llm.report_serializer import ReportSerializer

# ----------------------------------------------------------------------
# Minimal stubs for ReportingReport and StructuredReport
# ----------------------------------------------------------------------


class FakeStructuredReport:
    """Pretend version of StructuredReport with the fields the serializer uses."""

    def __init__(
        self,
        executive_summary: str = "Test summary.",
        kpis: Mapping[str, Any] | None = None,
        recommendations: list[str] | None = None,
        analytics: Mapping[str, Any] | None = None,
    ) -> None:
        self.executive_summary = executive_summary

        if kpis is None:
            self.kpis = {
                "Revenue": "1.2M",
                "Growth": "18%",
            }
        else:
            self.kpis = kpis

        if recommendations is None:
            self.recommendations = [
                "Increase marketing spend",
                "Optimize pricing",
            ]
        else:
            self.recommendations = recommendations

        if analytics is None:
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
        else:
            self.analytics = analytics


class FakeReportingReport:
    """Pretend version of ReportingReport with the needed attributes."""

    def __init__(
        self,
        execution_time: float = 1.2345,
        report: Any = None,
    ) -> None:
        self.execution_time = execution_time

        if report is None:
            self.report = FakeStructuredReport()
        else:
            self.report = report


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------


def test_none_report() -> None:
    """Serializing None returns a standard message."""
    text = ReportSerializer.serialize(None)
    assert text == "No reporting data available."


def test_execution_time() -> None:
    """Execution time is included in the output."""
    report = FakeReportingReport(execution_time=5.6789)
    text = ReportSerializer.serialize(report)
    assert "Execution Time : 5.6789 seconds" in text


def test_executive_summary() -> None:
    """Executive summary appears in the output."""
    summary = "This is a test executive summary."
    structured = FakeStructuredReport(executive_summary=summary)
    report = FakeReportingReport(report=structured)
    text = ReportSerializer.serialize(report)
    assert "EXECUTIVE SUMMARY" in text
    assert summary in text


def test_kpis() -> None:
    """KPIs are formatted as a mapping section."""
    kpis = {"Revenue": "1.2M", "Growth": "18%", "Margin": "22%"}
    structured = FakeStructuredReport(kpis=kpis)
    report = FakeReportingReport(report=structured)
    text = ReportSerializer.serialize(report)
    assert "KPIS" in text
    assert "- Revenue: 1.2M" in text
    assert "- Growth: 18%" in text
    assert "- Margin: 22%" in text


def test_recommendations() -> None:
    """Recommendations are listed as bullet points."""
    recs = ["Rec 1", "Rec 2", "Rec 3"]
    structured = FakeStructuredReport(recommendations=recs)
    report = FakeReportingReport(report=structured)
    text = ReportSerializer.serialize(report)
    assert "RECOMMENDATIONS" in text
    assert "- Rec 1" in text
    assert "- Rec 2" in text
    assert "- Rec 3" in text


def test_analytics_sections() -> None:
    """All four analytics subsections are included."""
    analytics = {
        "descriptive_statistics": {"mean": 42, "std": 5},
        "correlation_analysis": {"price_sales": -0.75},
        "distribution_analysis": {"skew": 0.2},
        "categorical_analysis": {"top_category": "Electronics"},
    }
    structured = FakeStructuredReport(analytics=analytics)
    report = FakeReportingReport(report=structured)
    text = ReportSerializer.serialize(report)

    assert "DESCRIPTIVE STATISTICS" in text
    assert "- mean: 42" in text
    assert "CORRELATION ANALYSIS" in text
    assert "- price_sales: -0.75" in text
    assert "DISTRIBUTION ANALYSIS" in text
    assert "- skew: 0.2" in text
    assert "CATEGORICAL ANALYSIS" in text
    assert "- top_category: Electronics" in text


def test_truncation_of_long_section() -> None:
    """Very long summaries are truncated to MAX_SECTION_LENGTH."""
    long_summary = "x" * 1000

    structured = FakeStructuredReport(
        executive_summary=long_summary,
    )

    report = FakeReportingReport(
        report=structured,
    )

    text = ReportSerializer.serialize(report)

    # The full summary should never appear.
    assert long_summary not in text

    # The beginning should still be present.
    assert "x" * 100 in text


def test_output_is_string() -> None:
    """The serializer always returns a string."""
    text = ReportSerializer.serialize(FakeReportingReport())
    assert isinstance(text, str)


def test_output_not_empty() -> None:
    """The output has some content."""
    text = ReportSerializer.serialize(FakeReportingReport())
    assert len(text) > 100
    assert text.strip() != ""


def test_missing_analytics_key_skips_section() -> None:
    """If an analytics key is missing, its section is omitted."""
    analytics = {
        "descriptive_statistics": {"mean": 42},
        # correlation_analysis missing
        "distribution_analysis": {"skew": 0.2},
        "categorical_analysis": {"top_category": "Electronics"},
    }
    structured = FakeStructuredReport(analytics=analytics)
    report = FakeReportingReport(report=structured)
    text = ReportSerializer.serialize(report)

    assert "DESCRIPTIVE STATISTICS" in text
    assert "CORRELATION ANALYSIS" not in text
    assert "DISTRIBUTION ANALYSIS" in text
    assert "CATEGORICAL ANALYSIS" in text


def test_empty_kpis_or_recommendations_are_skipped() -> None:
    """Empty lists/dicts for KPIs or recommendations produce no section."""
    structured = FakeStructuredReport(
        kpis={},
        recommendations=[],
    )
    report = FakeReportingReport(report=structured)
    text = ReportSerializer.serialize(report)

    assert "KPIS" not in text
    assert "RECOMMENDATIONS" not in text
