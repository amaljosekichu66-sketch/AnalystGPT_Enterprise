"""
Unit tests for the DistributionAnalysis module.
"""

from pandas import DataFrame

from src.analytics.distribution_analysis import DistributionAnalysis
from tests.fixtures.sample_dataset import sample_dataframe


def test_distribution_analysis_returns_dictionary():

    analyzer = DistributionAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result, dict)


def test_age_column_exists():

    analyzer = DistributionAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "Age" in result


def test_expected_statistics_exist():

    analyzer = DistributionAnalysis()

    result = analyzer.analyze(sample_dataframe())

    expected = [
        "skewness",
        "kurtosis",
        "distribution_shape",
        "tail_type",
        "lower_outlier_bound",
        "upper_outlier_bound",
        "outlier_count",
        "outlier_percentage",
    ]

    for key in expected:
        assert key in result["Age"]


def test_outlier_percentage_is_numeric():

    analyzer = DistributionAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(
        result["Age"]["outlier_percentage"],
        float,
    )


def test_outlier_count_is_integer():

    analyzer = DistributionAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(
        result["Age"]["outlier_count"],
        int,
    )


def test_empty_numeric_dataset_returns_empty_dictionary():

    dataframe = DataFrame(
        {
            "Department": ["IT", "HR"],
        }
    )

    analyzer = DistributionAnalysis()

    result = analyzer.analyze(dataframe)

    assert result == {}