"""
Unit tests for the AnalyticsReport module.
"""

from src.analytics.analytics_report import AnalyticsReport


def test_generate_returns_dictionary():

    report = AnalyticsReport()

    result = report.generate({})

    assert isinstance(result, dict)


def test_report_contains_all_sections():

    report = AnalyticsReport()

    results = {
        "descriptive_statistics": {},
        "numerical_analysis": {},
        "categorical_analysis": {},
        "correlation_analysis": {},
        "distribution_analysis": {},
    }

    final_report = report.generate(results)

    assert "descriptive_statistics" in final_report
    assert "numerical_analysis" in final_report
    assert "categorical_analysis" in final_report
    assert "correlation_analysis" in final_report
    assert "distribution_analysis" in final_report


def test_report_preserves_results():

    report = AnalyticsReport()

    results = {
        "descriptive_statistics": {"rows": 100},
        "numerical_analysis": {"Age": {}},
        "categorical_analysis": {"Gender": {}},
        "correlation_analysis": {"matrix": {}},
        "distribution_analysis": {"Age": {}},
    }

    final_report = report.generate(results)

    assert final_report["descriptive_statistics"]["rows"] == 100