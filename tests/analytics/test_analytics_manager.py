"""
Unit tests for the AnalyticsManager module.
"""

from src.analytics.analytics_manager import AnalyticsManager
from src.analytics.analytics_report import AnalyticsReport
from tests.fixtures.sample_dataset import sample_dataframe


def test_analytics_manager_returns_report():

    manager = AnalyticsManager()

    result = manager.analyze(sample_dataframe())

    assert isinstance(result, AnalyticsReport)


def test_all_sections_exist():

    manager = AnalyticsManager()

    result = manager.analyze(sample_dataframe())

    expected_sections = [
        "descriptive_statistics",
        "numerical_analysis",
        "categorical_analysis",
        "correlation_analysis",
        "distribution_analysis",
    ]

    for section in expected_sections:
        assert section in result.report


def test_descriptive_statistics_not_empty():

    manager = AnalyticsManager()

    result = manager.analyze(sample_dataframe())

    assert result.report["descriptive_statistics"] != {}


def test_numerical_analysis_not_empty():

    manager = AnalyticsManager()

    result = manager.analyze(sample_dataframe())

    assert result.report["numerical_analysis"] != {}


def test_categorical_analysis_not_empty():

    manager = AnalyticsManager()

    result = manager.analyze(sample_dataframe())

    assert result.report["categorical_analysis"] != {}


def test_correlation_analysis_not_empty():

    manager = AnalyticsManager()

    result = manager.analyze(sample_dataframe())

    assert result.report["correlation_analysis"] != {}


def test_distribution_analysis_not_empty():

    manager = AnalyticsManager()

    result = manager.analyze(sample_dataframe())

    assert result.report["distribution_analysis"] != {}