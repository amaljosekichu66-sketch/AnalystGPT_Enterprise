"""
Deterministic natural-language interpretation of distribution statistics.

Responsibilities
----------------
- Translate skewness and kurtosis into mathematically correct prose.
- Keep the wording consistent with the labels produced by DistributionAnalysis.
- Flag numeric columns whose distribution is characteristic of an identifier.

Rationale
---------
The statistics themselves were already correct; only their natural-language
interpretation was wrong. A generated report described `ticket_#` (skewness
0.0006, excess kurtosis -1.1994) as "highly skewed", claimed the values were
"concentrated on one side", and read the negative kurtosis as "a heavy tail" -
while the deterministic layer had already labelled the same column
"Approximately Symmetric" and "Light-tailed".

Producing the sentence deterministically, and handing it to the model as the
authoritative wording, removes the model's need to invent one.

Conventions (verified against pandas 3.0.5)
-------------------------------------------
- `Series.skew()` is the adjusted Fisher-Pearson standardised moment
  coefficient (G1). 0 means symmetric; positive means a longer right tail;
  negative means a longer left tail.
- `Series.kurt()` is FISHER (EXCESS) kurtosis, so a normal distribution
  scores 0, NOT 3. Negative means lighter tails / flatter peak than normal
  (platykurtic); positive means heavier tails (leptokurtic).
- Kurtosis describes tail weight and peakedness. It is NOT a measure of
  asymmetry and must never be cited as evidence of skew.
"""

from __future__ import annotations

from typing import Any

# ==========================================================
# Thresholds
# ==========================================================
#
# Deliberately identical to DistributionAnalysis.analyze() so the label and
# the sentence describing it can never disagree.

SKEW_SYMMETRIC_THRESHOLD = 0.5
SKEW_MODERATE_THRESHOLD = 1.0

KURTOSIS_LIGHT_THRESHOLD = -1.0
KURTOSIS_HEAVY_THRESHOLD = 1.0

# A continuous uniform distribution has skewness 0 and excess kurtosis -1.2
# exactly. Sequential identifiers approximate this closely.
_UNIFORM_SKEW_TOLERANCE = 0.1
_UNIFORM_KURTOSIS_CENTRE = -1.2
_UNIFORM_KURTOSIS_TOLERANCE = 0.15


# ==========================================================
# Skewness
# ==========================================================


def interpret_skewness(skewness: float) -> str:
    """
    Describe a skewness value correctly.

    Parameters
    ----------
    skewness:
        Adjusted Fisher-Pearson standardised moment coefficient (G1).

    Returns
    -------
    str
        A statement that matches the sign and magnitude of the input.
    """
    magnitude = abs(skewness)

    if magnitude < SKEW_SYMMETRIC_THRESHOLD:
        return (
            f"skewness {skewness:.4f} indicates an approximately symmetric "
            "distribution; values are spread evenly around the centre rather "
            "than concentrated on either side"
        )

    direction = "right (higher values)" if skewness > 0 else "left (lower values)"
    strength = "moderately" if magnitude < SKEW_MODERATE_THRESHOLD else "strongly"

    return (
        f"skewness {skewness:.4f} indicates a {strength} asymmetric "
        f"distribution with a longer tail towards the {direction}"
    )


# ==========================================================
# Kurtosis
# ==========================================================


def interpret_kurtosis(kurtosis: float) -> str:
    """
    Describe an excess (Fisher) kurtosis value correctly.

    Parameters
    ----------
    kurtosis:
        Excess kurtosis, where a normal distribution scores 0.

    Returns
    -------
    str
        A statement about tail weight only - never about asymmetry.
    """
    if kurtosis < KURTOSIS_LIGHT_THRESHOLD:
        return (
            f"excess kurtosis {kurtosis:.4f} (normal = 0) indicates lighter "
            "tails and a flatter peak than a normal distribution "
            "(platykurtic); extreme values are less common than normal, not "
            "more common"
        )

    if kurtosis <= KURTOSIS_HEAVY_THRESHOLD:
        return (
            f"excess kurtosis {kurtosis:.4f} (normal = 0) indicates tail "
            "weight close to a normal distribution (mesokurtic)"
        )

    return (
        f"excess kurtosis {kurtosis:.4f} (normal = 0) indicates heavier tails "
        "and a sharper peak than a normal distribution (leptokurtic); extreme "
        "values occur more often than normal"
    )


# ==========================================================
# Identifier detection
# ==========================================================


def looks_like_identifier(skewness: float, kurtosis: float) -> bool:
    """
    Return True when a column's shape matches a uniform/sequential series.

    A continuous uniform distribution has skewness 0 and excess kurtosis -1.2.
    Sequential identifiers (ticket numbers, row indices, auto-increment keys)
    approximate this closely. Such columns are numeric by dtype but carry no
    business meaning, so their descriptive statistics should not be narrated
    as though they described a business measure.
    """
    return (
        abs(skewness) < _UNIFORM_SKEW_TOLERANCE
        and abs(kurtosis - _UNIFORM_KURTOSIS_CENTRE) < _UNIFORM_KURTOSIS_TOLERANCE
    )


# ==========================================================
# Column & report level interpretation
# ==========================================================


def interpret_column(column: str, stats: dict[str, Any]) -> str | None:
    """
    Build the authoritative interpretation sentence for one numeric column.

    Parameters
    ----------
    column:
        Column name.
    stats:
        One entry from `analytics["distribution_analysis"]`.

    Returns
    -------
    str | None
        The interpretation, or None when skewness/kurtosis are unavailable.
    """
    if not isinstance(stats, dict):
        return None

    skewness = stats.get("skewness")
    kurtosis = stats.get("kurtosis")

    if not isinstance(skewness, (int, float)) or not isinstance(kurtosis, (int, float)):
        return None

    parts = [
        f"{column}: {interpret_skewness(float(skewness))}",
        interpret_kurtosis(float(kurtosis)),
    ]

    if looks_like_identifier(float(skewness), float(kurtosis)):
        parts.append(
            "this shape is characteristic of a uniform or sequential series, "
            "typical of an identifier column; treat its descriptive statistics "
            "as structural rather than as a business measure"
        )

    return ". ".join(parts) + "."


def interpret_distributions(
    distribution_analysis: dict[str, Any] | None,
) -> list[str]:
    """
    Build authoritative interpretation sentences for every numeric column.

    Parameters
    ----------
    distribution_analysis:
        The `distribution_analysis` block of the analytics report.

    Returns
    -------
    list[str]
        One statement per interpretable column; empty when nothing applies.
    """
    if not distribution_analysis or not isinstance(distribution_analysis, dict):
        return []

    statements: list[str] = []

    for column, stats in distribution_analysis.items():
        statement = interpret_column(str(column), stats)
        if statement is not None:
            statements.append(statement)

    return statements
