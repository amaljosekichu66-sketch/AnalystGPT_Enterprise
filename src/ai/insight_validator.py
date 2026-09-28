"""
Lightweight validation of generated AI insight text against deterministic facts.

Responsibilities
----------------
- Detect statements that contradict the computed distribution statistics.
- Detect conclusions that observational data cannot support.

Design notes
------------
This is a safety net, not the primary defence. Numerical integrity is enforced
structurally first: `ReportSerializer` hands the model the authoritative reading
of every distribution, and `PromptBuilder` states the rules explicitly. This
module catches the residual cases.

Findings are reported, not raised. A single generation on local CPU inference
costs minutes, so failing a report outright over a wording defect would trade a
flawed report for no report at all. Findings are surfaced on the report's
`limitations` list - which is already persisted and displayed - so a reader sees
exactly which statements were challenged.

Checks are deliberately narrow. Each one compares the text against a computed
value, so a finding means a real contradiction rather than an unlucky keyword.
"""

from __future__ import annotations

import re
from typing import Any

from src.analytics.statistical_interpretation import (
    KURTOSIS_HEAVY_THRESHOLD,
    SKEW_SYMMETRIC_THRESHOLD,
)

# ==========================================================
# Patterns
# ==========================================================

# Claims of pronounced skew.
_SKEW_CLAIM = re.compile(
    r"\b(?:highly|heavily|strongly|significantly|severely)[\s-]+skewed\b",
    re.IGNORECASE,
)

# Claims that values pile up on one side.
_ONE_SIDED_CLAIM = re.compile(
    r"\bconcentrated (?:on|towards|toward) (?:one|a single|the (?:lower|upper|left|right))\b",
    re.IGNORECASE,
)

# Claims of heavy tails.
_HEAVY_TAIL_CLAIM = re.compile(
    r"\b(?:heavy|heavier|fat|fatter)[\s-]+tail(?:s|ed)?\b",
    re.IGNORECASE,
)

# Kurtosis cited as EVIDENCE of asymmetry.
#
# Mere co-occurrence is not enough: "approximately symmetric (skewness 0.0006)
# with lighter tails (excess kurtosis -1.1994)" is a correct sentence that
# mentions both. The defect is kurtosis being presented as demonstrating skew,
# so an explicit evidential verb is required between the two terms.
#
# Applied per sentence, so `.` is safe here and - unlike a [^.!?] class - does
# not break on decimals such as "-1.1994".
_KURTOSIS_EVIDENCES_ASYMMETRY = re.compile(
    r"\bkurtosis\b.{0,120}?"
    r"\b(?:confirm\w*|indicat\w*|show\w*|demonstrat\w*|evidenc\w*|"
    r"suggest\w*|reflect\w*|reveal\w*|prov\w*|support\w*|underscor\w*)\b"
    r".{0,60}?\b(?:asymmetr\w*|skew\w*)\b",
    re.IGNORECASE,
)

# Unsupported performance conclusions drawn from a share of records.
#
# The bare adjective was added after a live generation slipped through with
# "The AI classification confidence is high at 89.2%, indicating effective
# initial categorization of tickets." A confidence score is the model's own
# certainty, not a measure of whether the categorisation was correct, so that
# is a performance claim with no performance metric behind it.
#
# Matching "effective" alone would be far too eager ("effective date",
# "cost-effective pricing tier"), so an assertive frame is required: something
# must be *stated or implied to be* effective. The whole check is still gated
# on the analytics containing no performance metric.
_EFFECTIVENESS_CLAIM = re.compile(
    r"\b(?:most effective|effectiveness|highly effective|"
    r"operational efficiency|strong efficiency|better performing|"
    r"outperform\w*)\b"
    # `\w*` not `\w+` on the stems that are already whole words, so bare
    # "show", "confirm", "suggest" and "reflect" match too.
    r"|\b(?:indicat\w+|suggest\w*|show\w*|demonstrat\w+|reflect\w*|"
    r"confirm\w*|prov\w+|evidenc\w+|is|are|was|were|remains?|appears?)\s+"
    r"(?:\w+\s+){0,3}effective\b"
    # "effective <date>" and "effective immediately" are commencement wording,
    # not a performance claim.
    r"(?!\s+(?:date|dates|immediately|from|as of|on\s+\d))",
    re.IGNORECASE,
)

# Explicit causal language.
#
# "contributes to" was added for the same reason: a live generation produced
# "suggesting that diligent follow-up contributes significantly to successful
# outcomes" from a co-occurrence, which is a causal assertion in everything but
# the verb "causes".
_CAUSAL_CLAIM = re.compile(
    r"\b(?:causes?|caused by|causing|leads to|led to|results in|" r"drives|driving|due to the fact that)\b"
    # Verb forms only, and only an adverb may sit between the verb and "to".
    # This catches "contributes significantly to <outcome>" while leaving the
    # noun ("contributions to the dataset") and the neutral transitive reading
    # ("contributes context to the analysis") alone.
    r"|\bcontribut(?:e|es|ed|ing)\s+(?:\w+ly\s+)?to\b"
    r"|\b(?:driver|drivers) of\b"
    r"|\battributable to\b"
    r"|\bresponsible for\b",
    re.IGNORECASE,
)

# Asserted relationships between fields.
#
# Correlation is the one claim the deterministic layer can contradict outright:
# `CorrelationAnalysis` either computed a coefficient or it did not. When it
# reported an empty matrix, any statement asserting a relationship was invented
# by the model.
#
# Worded to catch an assertion, not a mention. "Correlation analysis was not
# applicable" and "correlation does not imply causation" must pass; "a strong
# correlation between X and Y" must not.
_CORRELATION_CLAIM = re.compile(
    r"\b(?:strong|significant|clear|notable|high|positive|negative|direct|inverse)\s+"
    r"(?:correlation|association|relationship)\b"
    r"|\b(?:correlation|association|relationship)\s+(?:exists?|between)\b"
    r"|\b(?:correlates?|correlated)\s+(?:strongly|significantly|positively|negatively|with)\b",
    re.IGNORECASE,
)

# Metrics that would legitimately support a performance conclusion.
_PERFORMANCE_METRIC_HINTS = (
    "resolution_time",
    "resolution time",
    "handling_time",
    "handle_time",
    "response_time",
    "response time",
    "satisfaction",
    "csat",
    "nps",
    "conversion",
    "revenue",
    "cost",
    "sla",
    "duration",
)


# ==========================================================
# Helpers
# ==========================================================


def _split_sentences(text: str) -> list[str]:
    """Split text into rough sentences for co-occurrence checks."""
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def _distribution_values(
    analytics: dict[str, Any] | None,
) -> tuple[list[float], list[float]]:
    """Extract every skewness and excess-kurtosis value from the analytics."""
    skews: list[float] = []
    kurts: list[float] = []

    if not isinstance(analytics, dict):
        return skews, kurts

    distributions = analytics.get("distribution_analysis")
    if not isinstance(distributions, dict):
        return skews, kurts

    for stats in distributions.values():
        if not isinstance(stats, dict):
            continue
        skew = stats.get("skewness")
        kurt = stats.get("kurtosis")
        if isinstance(skew, (int, float)):
            skews.append(float(skew))
        if isinstance(kurt, (int, float)):
            kurts.append(float(kurt))

    return skews, kurts


def _has_computed_correlation(analytics: dict[str, Any] | None) -> bool:
    """
    Return True when the analytics actually contain a correlation coefficient.

    `CorrelationAnalysis` runs only when at least two governed numerical
    measures exist. With fewer, it returns an empty matrix and null strongest
    pairs - which is a positive statement that no relationship was measured,
    not merely missing data.

    The matrix is keyed column -> column, so a single measure still yields a
    1.0 self-correlation. Only off-diagonal pairs count as evidence.
    """
    if not isinstance(analytics, dict):
        return False

    correlation = analytics.get("correlation_analysis")
    if not isinstance(correlation, dict):
        return False

    for key in ("strongest_positive", "strongest_negative"):
        if isinstance(correlation.get(key), dict):
            return True

    matrix = correlation.get("correlation_matrix")
    if not isinstance(matrix, dict):
        return False

    for row_name, row in matrix.items():
        if not isinstance(row, dict):
            continue
        if any(column != row_name for column in row):
            return True

    return False


def _has_performance_metric(analytics: dict[str, Any] | None) -> bool:
    """Return True when the analytics contain a metric measuring performance."""
    if not isinstance(analytics, dict):
        return False

    blob = " ".join(str(k).lower() for k in _iter_metric_names(analytics))
    return any(hint in blob for hint in _PERFORMANCE_METRIC_HINTS)


def _iter_metric_names(obj: Any, depth: int = 0) -> list[str]:
    """Collect mapping keys up to a bounded depth."""
    names: list[str] = []
    if depth > 3 or not isinstance(obj, dict):
        return names

    for key, value in obj.items():
        names.append(str(key))
        names.extend(_iter_metric_names(value, depth=depth + 1))

    return names


# ==========================================================
# Validation
# ==========================================================


def validate_insight_text(
    text: str,
    analytics: dict[str, Any] | None,
) -> list[str]:
    """
    Compare generated insight text against the deterministic analytics.

    Parameters
    ----------
    text:
        The generated narrative, summary, recommendations and explanations.
    analytics:
        The analytics report used to build the prompt.

    Returns
    -------
    list[str]
        Human-readable findings; empty when nothing contradicts the data.
    """
    if not text or not text.strip():
        return []

    findings: list[str] = []
    skews, kurts = _distribution_values(analytics)

    # 1. Claimed skew where every measured column is symmetric.
    if skews and all(abs(s) < SKEW_SYMMETRIC_THRESHOLD for s in skews):
        if _SKEW_CLAIM.search(text):
            findings.append(
                "Generated text described the data as strongly skewed, but every "
                f"measured skewness value is within +/-{SKEW_SYMMETRIC_THRESHOLD} "
                "(approximately symmetric). Treat that description as unreliable."
            )
        if _ONE_SIDED_CLAIM.search(text):
            findings.append(
                "Generated text claimed values are concentrated on one side, but "
                "the measured skewness indicates an approximately symmetric "
                "distribution. Treat that description as unreliable."
            )

    # 2. Claimed heavy tails where every measured column is light-tailed.
    if kurts and all(k <= KURTOSIS_HEAVY_THRESHOLD for k in kurts):
        if _HEAVY_TAIL_CLAIM.search(text):
            findings.append(
                "Generated text described heavy tails, but no measured excess "
                f"kurtosis exceeds {KURTOSIS_HEAVY_THRESHOLD} (normal = 0). "
                "Negative excess kurtosis means lighter tails than normal. "
                "Treat that description as unreliable."
            )

    # 3. Kurtosis presented as evidence of asymmetry (always a category error).
    for sentence in _split_sentences(text):
        if _KURTOSIS_EVIDENCES_ASYMMETRY.search(sentence):
            findings.append(
                "Generated text cited kurtosis as evidence of skew or asymmetry. "
                "Kurtosis measures tail weight only and cannot evidence asymmetry."
            )
            break

    # 4. A relationship asserted where none was computed.
    if _CORRELATION_CLAIM.search(text) and not _has_computed_correlation(analytics):
        findings.append(
            "Generated text asserted a correlation or relationship between "
            "fields, but the correlation analysis computed none (the matrix is "
            "empty, which happens when the dataset has fewer than two governed "
            "numerical measures). Treat that relationship as unsupported."
        )

    # 5. Performance conclusions without a metric that measures performance.
    if _EFFECTIVENESS_CLAIM.search(text) and not _has_performance_metric(analytics):
        findings.append(
            "Generated text asserted effectiveness or efficiency, but the "
            "analytics contain no performance metric (resolution time, cost, "
            "satisfaction or comparable). Share of records shows prevalence, "
            "not performance."
        )

    # 6. Causal language on observational data.
    if _CAUSAL_CLAIM.search(text):
        findings.append(
            "Generated text used causal language. This dataset is "
            "observational, so relationships are associations, not causes."
        )

    return findings
