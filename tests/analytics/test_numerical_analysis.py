"""
Unit tests for the NumericalAnalysis module.
"""

from pandas import DataFrame

from src.analytics.numerical_analysis import NumericalAnalysis
from tests.fixtures.sample_dataset import sample_dataframe


def test_numerical_analysis_returns_dictionary():
    """
    Verify that the analyzer returns a dictionary.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result, dict)


def test_age_column_exists():
    """
    Verify the Age column is analyzed.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "Age" in result


def test_salary_column_exists():
    """
    Verify the Salary column is analyzed.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "Salary" in result


def test_bonus_column_exists():
    """
    Verify the Bonus column is analyzed.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "Bonus" in result


def test_statistics_exist_for_age():
    """
    Verify all expected statistics exist.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    age = result["Age"]

    expected_keys = [
        "count",
        "mean",
        "median",
        "mode",
        "minimum",
        "maximum",
        "range",
        "variance",
        "standard_deviation",
        "first_quartile",
        "third_quartile",
        "interquartile_range",
    ]

    for key in expected_keys:
        assert key in age


def test_mean_is_numeric():
    """
    Verify mean is numeric.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result["Age"]["mean"], float)


def test_median_is_numeric():
    """
    Verify median is numeric.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result["Age"]["median"], float)


def test_count_is_integer():
    """
    Verify count is integer.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result["Age"]["count"], int)


def test_range_is_positive():
    """
    Verify range is positive.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert result["Salary"]["range"] > 0


def test_interquartile_range_is_non_negative():
    """
    Verify IQR is non-negative.
    """

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert result["Age"]["interquartile_range"] >= 0


def test_empty_numeric_dataset_returns_empty_dictionary():
    """
    Verify an empty dictionary is returned when no numerical columns exist.
    """

    dataframe = DataFrame(
        {
            "Department": ["IT", "HR"],
            "Gender": ["M", "F"],
        }
    )

    analyzer = NumericalAnalysis()

    result = analyzer.analyze(dataframe)

    assert result == {}