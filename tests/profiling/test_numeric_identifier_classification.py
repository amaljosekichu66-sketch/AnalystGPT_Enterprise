"""
Regression tests: a numeric record key must never become a business measure.

The defect
----------
`SemanticClassifier.classify_column` decided the numeric branch on
`pd.api.types.is_numeric_dtype` alone. It had already computed
`uniqueness_ratio` and a `cardinality_classification` of "unique" - and ignored
both.

Measured consequence on the real dataset (27,945 rows, 21 columns):

    ticket_#  ->  semantic_type=numeric_measure, analytical_role=measure,
                  uniqueness=100.0%, governance=impute_median

    ground truth: 27,945 distinct values over the range 275,443-303,422,
                  99.88% of sorted gaps equal to 1, skewness 0.000571,
                  excess kurtosis -1.199404 (the uniform signature)

which published `ticket_#: Mean = 289428.78` as a business statistic, reported
"Governed Measures : 1" for a dataset with none, offered to impute the median
of a primary key, and handed the model a skewness to narrate - producing the
claim that the data was "highly skewed" with "a heavy tail".

The rule is structural, never name-based: `ticket_#` carries no keyword that
would identify it, and hard-coding the name would leave `row_number`,
`invoice_#` and every future variant broken.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analytics.correlation_analysis import CorrelationAnalysis
from src.analytics.descriptive_statistics import DescriptiveStatistics
from src.analytics.distribution_analysis import DistributionAnalysis
from src.analytics.numerical_analysis import NumericalAnalysis
from src.profiling.data_profiler import DataProfiler
from src.profiling.models import AnalyticalRole, SemanticType
from src.profiling.semantic_classifier import SemanticClassifier


@pytest.fixture()
def classifier() -> SemanticClassifier:
    return SemanticClassifier()


def _sequential_ids(count: int = 27_945, start: int = 275_443) -> pd.Series:
    """Reproduce the measured shape of the real `ticket_#` column."""
    rng = np.random.default_rng(0)
    span = int(count * 1.00125)  # 99.88% dense, as measured
    return pd.Series(np.sort(rng.choice(np.arange(start, start + span), count, replace=False)))


# ==========================================================
# The identifier must be recognised
# ==========================================================


def test_ticket_hash_column_is_an_identifier(classifier: SemanticClassifier) -> None:
    """The exact reproduction case."""
    series = _sequential_ids()

    semantic_type, role, _, _, visual, governance = classifier.classify_column("ticket_#", series, len(series))

    assert semantic_type is SemanticType.IDENTIFIER
    assert role is AnalyticalRole.IDENTIFIER
    assert visual == "excluded"
    assert governance == "preserve_nulls"


def test_median_imputation_is_never_recommended_for_a_key(
    classifier: SemanticClassifier,
) -> None:
    """Imputing the median of a primary key is meaningless governance advice."""
    series = _sequential_ids()

    *_, governance = classifier.classify_column("ticket_#", series, len(series))

    assert governance != "impute_median"


@pytest.mark.parametrize(
    "column_name",
    ["ticket_#", "row_number", "invoice_#", "order_no", "seq", "record"],
)
def test_detection_does_not_depend_on_the_column_name(
    classifier: SemanticClassifier,
    column_name: str,
) -> None:
    """None of these names carry an ID keyword; the shape decides."""
    series = _sequential_ids(count=5_000, start=1_000)

    semantic_type, role, *_ = classifier.classify_column(column_name, series, len(series))

    assert semantic_type is SemanticType.IDENTIFIER
    assert role is AnalyticalRole.IDENTIFIER


def test_perfect_auto_increment_is_an_identifier(
    classifier: SemanticClassifier,
) -> None:
    series = pd.Series(np.arange(4_000))

    semantic_type, role, *_ = classifier.classify_column("seq", series, len(series))

    assert semantic_type is SemanticType.IDENTIFIER
    assert role is AnalyticalRole.IDENTIFIER


# ==========================================================
# Genuine measures must survive
# ==========================================================


@pytest.mark.parametrize(
    ("column_name", "builder"),
    [
        ("revenue", lambda r: pd.Series(r.lognormal(8, 1, 5_000))),
        ("units_sold", lambda r: pd.Series(r.integers(1, 50, 5_000))),
        ("salary", lambda r: pd.Series(r.integers(30_000, 200_000, 5_000))),
        ("score", lambda r: pd.Series(r.integers(0, 100, 5_000))),
        # Fully distinct, but scattered across a wide range rather than tiling
        # it. Uniqueness alone would misfire here; density is what saves it.
        (
            "price_cents",
            lambda r: pd.Series(r.choice(np.arange(1_000, 9_000_000), 5_000, replace=False)),
        ),
    ],
)
def test_genuine_measures_are_not_demoted(
    classifier: SemanticClassifier,
    column_name: str,
    builder,
) -> None:
    rng = np.random.default_rng(7)
    series = builder(rng)

    semantic_type, role, *_ = classifier.classify_column(column_name, series, len(series))

    assert role in {AnalyticalRole.MEASURE, AnalyticalRole.DEMOGRAPHIC_MEASURE}
    assert semantic_type is not SemanticType.IDENTIFIER


def test_small_distinct_integer_column_stays_a_measure(
    classifier: SemanticClassifier,
) -> None:
    """Below the distinct-value floor the evidence is too thin to demote."""
    series = pd.Series(np.arange(40))

    semantic_type, role, *_ = classifier.classify_column("age", series, len(series))

    assert semantic_type is not SemanticType.IDENTIFIER
    assert role in {AnalyticalRole.MEASURE, AnalyticalRole.DEMOGRAPHIC_MEASURE}


def test_dense_integer_range_with_repeats_stays_a_measure(
    classifier: SemanticClassifier,
) -> None:
    """Density without uniqueness is an ordinary bounded count."""
    rng = np.random.default_rng(3)
    series = pd.Series(rng.integers(0, 300, 5_000))

    semantic_type, *_ = classifier.classify_column("visits", series, len(series))

    assert semantic_type is not SemanticType.IDENTIFIER


# ==========================================================
# The consequence: no analytics layer treats it as a measure
# ==========================================================


@pytest.fixture()
def identifier_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticket_#": _sequential_ids(count=3_000, start=100_000),
            "status": ["Closed"] * 2_670 + ["Open"] * 330,
        }
    )


def test_identifier_is_excluded_from_every_numeric_analysis(
    identifier_frame: pd.DataFrame,
) -> None:
    """
    One classification change must propagate to all four analytics modules -
    that is the point of deciding semantics in a single place.
    """
    profile = DataProfiler().profile_dataset(identifier_frame)

    assert "ticket_#" not in DistributionAnalysis().analyze(identifier_frame, profile=profile)
    assert "ticket_#" not in NumericalAnalysis().analyze(identifier_frame, profile=profile)
    assert "ticket_#" not in CorrelationAnalysis().analyze(identifier_frame, profile=profile).get(
        "correlation_matrix", {}
    )

    descriptive = DescriptiveStatistics().analyze(identifier_frame, profile=profile)
    assert "ticket_#" not in descriptive.get("numeric_columns", [])
    assert descriptive.get("numeric_column_count", 0) == 0


def test_no_skewness_is_published_for_an_identifier(
    identifier_frame: pd.DataFrame,
) -> None:
    """
    No skewness reaches the prompt, so there is nothing for the model to
    misread. The validator remains as a second line of defence, but the first
    line is simply not producing the statistic.
    """
    profile = DataProfiler().profile_dataset(identifier_frame)

    distributions = DistributionAnalysis().analyze(identifier_frame, profile=profile)

    assert distributions == {}


def test_identifier_is_not_offered_as_a_chart_measure(
    identifier_frame: pd.DataFrame,
) -> None:
    """`VisualizationPlanner` selects by analytical role."""
    profile = DataProfiler().profile_dataset(identifier_frame)

    measures = profile.get_columns_by_role(AnalyticalRole.MEASURE)

    assert [column.column_name for column in measures] == []
