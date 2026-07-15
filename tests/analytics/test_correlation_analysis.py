"""
Unit tests for the CorrelationAnalysis module.
"""

from pandas import DataFrame

from src.analytics.correlation_analysis import CorrelationAnalysis
from tests.fixtures.sample_dataset import sample_dataframe


def test_correlation_analysis_returns_dictionary():

    analyzer = CorrelationAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(result, dict)


def test_correlation_matrix_exists():

    analyzer = CorrelationAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "correlation_matrix" in result


def test_strongest_positive_exists():

    analyzer = CorrelationAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "strongest_positive" in result


def test_strongest_negative_exists():

    analyzer = CorrelationAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert "strongest_negative" in result


def test_correlation_matrix_is_dictionary():

    analyzer = CorrelationAnalysis()

    result = analyzer.analyze(sample_dataframe())

    assert isinstance(
        result["correlation_matrix"],
        dict,
    )


def test_single_numeric_column():

    dataframe = DataFrame(
        {
            "Age": [20, 30, 40],
            "Gender": ["M", "F", "M"],
        }
    )

    analyzer = CorrelationAnalysis()

    result = analyzer.analyze(dataframe)

    assert result["correlation_matrix"] == {}
    assert result["strongest_positive"] is None
    assert result["strongest_negative"] is None