"""
Unit tests for the CategoricalAnalysis module.
"""

from pandas import DataFrame

from src.analytics.categorical_analysis import CategoricalAnalysis
from tests.fixtures.sample_dataset import sample_dataframe


def test_categorical_analysis_returns_dictionary():

    analyzer = CategoricalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result, dict)


def test_gender_column_exists():

    analyzer = CategoricalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "Gender" in result


def test_department_column_exists():

    analyzer = CategoricalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "Department" in result


def test_expected_statistics_exist():

    analyzer = CategoricalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    gender = result["Gender"]

    expected = [
        "count",
        "missing_values",
        "unique_values",
        "top_value",
        "top_frequency",
        "value_distribution",
    ]

    for key in expected:
        assert key in gender


def test_unique_values_positive():

    analyzer = CategoricalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert result["Department"]["unique_values"] > 0


def test_value_distribution_is_dictionary():

    analyzer = CategoricalAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(
        result["Gender"]["value_distribution"],
        dict,
    )


def test_empty_categorical_dataset_returns_empty_dictionary():

    dataframe = DataFrame(
        {
            "Age": [20, 30],
            "Salary": [1000, 2000],
        }
    )

    analyzer = CategoricalAnalysis()

    result = analyzer.analyze(dataframe)

    assert result == {}