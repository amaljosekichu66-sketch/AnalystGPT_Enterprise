"""
Regression tests for deterministic interpretation of distribution statistics.

Context
-------
A generated report described `ticket_#` (skewness 0.0006, excess kurtosis
-1.1994) as "highly skewed" with values "concentrated on one side", and read the
negative kurtosis as "a heavy tail towards lower values". Both readings are
wrong, and both contradicted labels the deterministic layer had already
produced ("Approximately Symmetric", "Light-tailed").

The statistics were correct. These tests pin the interpretation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analytics.statistical_interpretation import (
    interpret_column,
    interpret_distributions,
    interpret_kurtosis,
    interpret_skewness,
    looks_like_identifier,
)

# ==========================================================
# Convention verification
# ==========================================================


def test_pandas_kurt_is_fisher_excess_not_pearson() -> None:
    """
    pandas .kurt() scores a normal distribution at 0, not 3.

    Every interpretation in this module depends on that convention.
    """
    normal = pd.Series(np.random.default_rng(0).normal(size=200_000))
    assert abs(float(normal.kurt())) < 0.1


def test_uniform_series_has_excess_kurtosis_near_minus_one_point_two() -> None:
    """A sequential identifier approximates a uniform distribution."""
    sequential = pd.Series(np.linspace(275_443, 303_422, 27_945))

    assert float(sequential.skew()) == pytest.approx(0.0, abs=1e-6)
    assert float(sequential.kurt()) == pytest.approx(-1.2, abs=1e-3)


# ==========================================================
# Skewness
# ==========================================================


def test_near_zero_skewness_is_symmetric_not_skewed() -> None:
    text = interpret_skewness(0.0006)

    assert "approximately symmetric" in text
    assert "skewed" not in text
    assert "concentrated" not in text.replace("rather than concentrated", "")


def test_positive_skewness_reports_right_tail() -> None:
    text = interpret_skewness(2.0231)

    assert "right (higher values)" in text
    assert "left" not in text


def test_negative_skewness_reports_left_tail() -> None:
    text = interpret_skewness(-2.0231)

    assert "left (lower values)" in text
    assert "right" not in text


def test_moderate_and_strong_skew_are_distinguished() -> None:
    assert "moderately" in interpret_skewness(0.7)
    assert "strongly" in interpret_skewness(1.9)


# ==========================================================
# Kurtosis
# ==========================================================


def test_negative_excess_kurtosis_is_light_tailed_never_heavy() -> None:
    text = interpret_kurtosis(-1.1994)

    assert "lighter tails" in text
    assert "platykurtic" in text
    assert "heavier" not in text
    assert "heavy" not in text


def test_positive_excess_kurtosis_is_heavy_tailed() -> None:
    text = interpret_kurtosis(6.139)

    assert "heavier tails" in text
    assert "leptokurtic" in text


def test_near_zero_excess_kurtosis_is_mesokurtic() -> None:
    assert "mesokurtic" in interpret_kurtosis(0.05)


def test_kurtosis_interpretation_never_mentions_asymmetry() -> None:
    """Kurtosis measures tail weight; it is not evidence of skew."""
    for value in (-3.0, -1.1994, 0.0, 0.5, 6.139):
        text = interpret_kurtosis(value).lower()
        assert "asymmetr" not in text
        assert "skew" not in text


# ==========================================================
# Identifier detection
# ==========================================================


def test_sequential_identifier_shape_is_detected() -> None:
    assert looks_like_identifier(0.0006, -1.1994) is True


def test_genuine_measure_is_not_flagged_as_identifier() -> None:
    assert looks_like_identifier(2.0231, 6.139) is False
    assert looks_like_identifier(0.01, 0.02) is False


def test_identifier_column_carries_a_structural_caveat() -> None:
    text = interpret_column("ticket_#", {"skewness": 0.0006, "kurtosis": -1.1994})

    assert text is not None
    assert "identifier column" in text
    assert "structural" in text


# ==========================================================
# Column / report level
# ==========================================================


def test_interpret_column_requires_both_statistics() -> None:
    assert interpret_column("x", {"skewness": 0.1}) is None
    assert interpret_column("x", {"kurtosis": 0.1}) is None
    assert interpret_column("x", {}) is None
    assert interpret_column("x", "not a mapping") is None


def test_interpret_distributions_handles_empty_input() -> None:
    assert interpret_distributions(None) == []
    assert interpret_distributions({}) == []


def test_interpret_distributions_covers_every_column() -> None:
    statements = interpret_distributions(
        {
            "ticket_#": {"skewness": 0.0006, "kurtosis": -1.1994},
            "revenue": {"skewness": 2.0231, "kurtosis": 6.139},
        }
    )

    assert len(statements) == 2
    assert any(s.startswith("ticket_#") for s in statements)
    assert any(s.startswith("revenue") for s in statements)


def test_interpretation_agrees_with_distribution_analysis_labels() -> None:
    """
    The sentence and the label must never disagree.

    Both layers share the same thresholds; this pins that they stay aligned.
    """
    from src.analytics.distribution_analysis import DistributionAnalysis

    frame = pd.DataFrame({"ticket_#": np.linspace(275_443, 303_422, 27_945)})
    result = DistributionAnalysis().analyze(frame)

    stats = result["ticket_#"]
    assert stats["distribution_shape"] == "Approximately Symmetric"
    assert stats["tail_type"] == "Light-tailed"

    sentence = interpret_column("ticket_#", stats)
    assert sentence is not None
    assert "approximately symmetric" in sentence
    assert "lighter tails" in sentence
