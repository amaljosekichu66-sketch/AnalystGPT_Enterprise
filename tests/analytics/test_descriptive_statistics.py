"""
Unit tests for the DescriptiveStatistics module.
"""

from src.analytics.descriptive_statistics import DescriptiveStatistics
from tests.fixtures.sample_dataset import sample_dataframe


def test_descriptive_statistics_returns_dictionary():
    """
    Verify that the analyzer returns a dictionary.
    """

    analyzer = DescriptiveStatistics()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result, dict)


def test_total_rows():
    """
    Verify the total row count.
    """

    analyzer = DescriptiveStatistics()

    result = analyzer.analyze(sample_dataframe())

    assert result["total_rows"] == 6


def test_total_columns():
    """
    Verify the total column count.
    """

    analyzer = DescriptiveStatistics()

    result = analyzer.analyze(sample_dataframe())

    assert result["total_columns"] == 7


def test_numeric_columns_detected():
    """
    Verify numerical columns are detected.
    """

    analyzer = DescriptiveStatistics()

    result = analyzer.analyze(sample_dataframe())

    expected = ["Age", "Salary", "Bonus"]

    assert result["numeric_columns"] == expected


def test_categorical_columns_detected():
    """
    Verify categorical columns are detected.
    """

    analyzer = DescriptiveStatistics()

    result = analyzer.analyze(sample_dataframe())

    expected = ["Gender", "Department", "Active"]

    assert result["categorical_columns"] == expected


def test_datetime_columns_detected():
    """
    Verify datetime columns are detected.
    """

    analyzer = DescriptiveStatistics()

    result = analyzer.analyze(sample_dataframe())

    expected = ["Joining_Date"]

    assert result["datetime_columns"] == expected


def test_memory_usage_exists():
    """
    Verify memory usage is calculated.
    """

    analyzer = DescriptiveStatistics()

    result = analyzer.analyze(sample_dataframe())

    assert "memory_usage_mb" in result

    assert isinstance(
        result["memory_usage_mb"],
        float,
    )

    assert result["memory_usage_mb"] >= 0