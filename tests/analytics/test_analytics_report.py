"""
Unit tests for the AnalyticsReport module.
"""

from src.analytics.analytics_report import AnalyticsReport


def build_report():

    return AnalyticsReport(
        report={
            "descriptive_statistics": {},
            "numerical_analysis": {},
            "categorical_analysis": {},
            "correlation_analysis": {},
            "distribution_analysis": {},
        },
        execution_time=1.25,
    )


def test_returns_analytics_report():

    report = build_report()

    assert isinstance(
        report,
        AnalyticsReport,
    )


def test_report_contains_all_sections():

    report = build_report()

    expected = [
        "descriptive_statistics",
        "numerical_analysis",
        "categorical_analysis",
        "correlation_analysis",
        "distribution_analysis",
    ]

    for section in expected:
        assert section in report.report


def test_to_dict_preserves_results():

    report = build_report()

    report_dict = report.to_dict()

    assert report_dict["report"] == report.report

    assert report_dict["execution_time"] == 1.25