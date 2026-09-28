"""
Regression tests for validation of AI insight text against deterministic facts.

Each case mirrors a statement that a real generated report actually produced
against analytics whose measured values contradict it.
"""

from __future__ import annotations

import pytest

from src.ai.insight_validator import validate_insight_text

# Analytics matching the observed dataset: one sequential identifier column,
# approximately symmetric and light-tailed.
SYMMETRIC_LIGHT_TAILED = {
    "distribution_analysis": {
        "ticket_#": {
            "skewness": 0.0006,
            "kurtosis": -1.1994,
            "distribution_shape": "Approximately Symmetric",
            "tail_type": "Light-tailed",
        }
    },
    "categorical_analysis": {
        "status": {"top_value": "Closed", "top_frequency": 24862},
        "channel": {"top_value": "Email", "top_frequency": 20875},
    },
}


# ==========================================================
# Statistical contradictions
# ==========================================================


def test_flags_highly_skewed_claim_on_symmetric_data() -> None:
    text = (
        "The descriptive statistics reveal a highly skewed distribution for the "
        "'ticket_#' variable, with a skewness of 0.0006."
    )

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert any("strongly skewed" in f for f in findings)


def test_flags_one_sided_concentration_claim_on_symmetric_data() -> None:
    text = "This shows the majority of tickets are concentrated on one side of the distribution."

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert any("concentrated on one side" in f for f in findings)


def test_flags_heavy_tail_claim_on_light_tailed_data() -> None:
    text = "The kurtosis of -1.1994 indicates a heavy tail towards lower values."

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert any("heavy tails" in f for f in findings)


def test_flags_kurtosis_cited_as_evidence_of_asymmetry() -> None:
    text = "The kurtosis of -1.1994 further confirms this asymmetry."

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert any("tail weight only" in f for f in findings)


def test_correct_interpretation_produces_no_statistical_findings() -> None:
    text = (
        "ticket_# is approximately symmetric (skewness 0.0006) with lighter "
        "tails than a normal distribution (excess kurtosis -1.1994). Closed "
        "accounts for 24,862 records."
    )

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert findings == []


def test_genuine_skew_is_not_flagged() -> None:
    """A real right-skewed, heavy-tailed column must not trigger findings."""
    analytics = {"distribution_analysis": {"revenue": {"skewness": 2.0231, "kurtosis": 6.139}}}
    text = "Revenue is highly skewed with a heavy tail towards higher values."

    findings = validate_insight_text(text, analytics)

    assert findings == []


# ==========================================================
# Unsupported business conclusions
# ==========================================================


def test_flags_effectiveness_claim_without_performance_metric() -> None:
    text = "Email is the most effective channel, highlighting its effectiveness."

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert any("prevalence, not performance" in f for f in findings)


def test_flags_operational_efficiency_claim_from_a_share_of_records() -> None:
    text = "89% of tickets are Closed, suggesting strong operational efficiency."

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert any("prevalence, not performance" in f for f in findings)


def test_effectiveness_claim_allowed_when_a_performance_metric_exists() -> None:
    analytics = {
        "distribution_analysis": {},
        "descriptive_statistics": {"resolution_time": {"mean": 4.2}},
    }
    text = "Email shows the strongest effectiveness on resolution time."

    findings = validate_insight_text(text, analytics)

    assert findings == []


def test_flags_causal_language() -> None:
    text = "The high Closed rate causes improved client satisfaction."

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert any("observational" in f for f in findings)


def test_descriptive_prevalence_wording_is_accepted() -> None:
    text = (
        "Email is the most frequently recorded channel, accounting for 74.7% "
        "of records. Closed is the most frequent status."
    )

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert findings == []


# ==========================================================
# Robustness
# ==========================================================


def test_empty_text_and_missing_analytics_are_safe() -> None:
    assert validate_insight_text("", SYMMETRIC_LIGHT_TAILED) == []
    assert validate_insight_text("   ", None) == []
    assert validate_insight_text("Some text.", None) == []
    assert validate_insight_text("Some text.", {}) == []


def test_malformed_analytics_do_not_raise() -> None:
    assert validate_insight_text("text", {"distribution_analysis": "bad"}) == []
    assert validate_insight_text("text", {"distribution_analysis": {"a": None}}) == []


def test_kurtosis_and_skew_mentioned_together_correctly_is_not_flagged() -> None:
    """
    Co-occurrence alone is not a defect.

    This sentence names both statistics and reads both correctly; only kurtosis
    presented as *evidence* of asymmetry is an error.
    """
    text = (
        "Skewness of 0.0006 shows an approximately symmetric distribution, "
        "while excess kurtosis of -1.1994 shows lighter tails than normal."
    )

    findings = validate_insight_text(text, SYMMETRIC_LIGHT_TAILED)

    assert findings == []


# ==========================================================
# Asserted correlations where none was computed
# ==========================================================
#
# Found during the final acceptance audit. A real generation against the
# 27,945-row dataset produced, four times over:
#
#     "The dataset reveals a strong correlation between 'F/U Quest. Submitted'
#      and 'Closed' status"
#
# while the deterministic layer had supplied:
#
#     CORRELATION ANALYSIS
#     - correlation_matrix: Empty.
#     - strongest_positive: None
#     - strongest_negative: None
#
# The dataset has zero governed numerical measures, so no coefficient exists
# for any pair. The claim drove a recommendation ("Explore the correlation
# between ... to refine customer follow-up procedures") and the validator
# returned zero findings.
#
# This is the one claim the deterministic layer can contradict outright, which
# makes it the same shape as the existing skew and kurtosis checks.


_NO_CORRELATION = {
    "correlation_analysis": {
        "correlation_matrix": {},
        "strongest_positive": None,
        "strongest_negative": None,
    },
    "distribution_analysis": {},
    "descriptive_statistics": {"numeric_column_count": 0},
}

_WITH_CORRELATION = {
    "correlation_analysis": {
        "correlation_matrix": {
            "salary": {"salary": 1.0, "bonus": 0.9712},
            "bonus": {"salary": 0.9712, "bonus": 1.0},
        },
        "strongest_positive": {
            "column_1": "salary",
            "column_2": "bonus",
            "correlation": 0.9712,
        },
        "strongest_negative": None,
    },
    "distribution_analysis": {},
    "descriptive_statistics": {"numeric_column_count": 2},
}


def test_flags_the_observed_fabricated_correlation() -> None:
    """The verbatim claim from the acceptance-audit generation."""
    text = (
        "The dataset reveals a strong correlation between "
        '"F/U Quest. Submitted" and "Closed" status, highlighting a key '
        "customer journey stage."
    )

    findings = validate_insight_text(text, _NO_CORRELATION)

    assert any("correlation" in f.lower() for f in findings)


@pytest.mark.parametrize(
    "text",
    [
        "A strong correlation exists between channel and status.",
        "There is a significant relationship between lead status and closure.",
        "Ticket age correlates strongly with escalation.",
        "We observe a clear association between tone and escalation.",
        "A positive correlation between follow-up and resolution is evident.",
    ],
)
def test_flags_any_asserted_relationship_without_evidence(text: str) -> None:
    assert validate_insight_text(text, _NO_CORRELATION)


def test_genuine_correlation_is_not_flagged() -> None:
    """A computed coefficient makes the same sentence legitimate."""
    text = "A strong correlation exists between salary and bonus (0.9712)."

    findings = validate_insight_text(text, _WITH_CORRELATION)

    assert not any("correlation analysis computed none" in f for f in findings)


@pytest.mark.parametrize(
    "text",
    [
        "Correlation analysis was not applicable as fewer than two numerical measure columns were present.",
        "Observational records describe correlation and distribution; causal conclusions require validation.",
        "Correlation does not imply causation.",
    ],
)
def test_mentioning_correlation_is_not_asserting_one(text: str) -> None:
    """Describing the absence of a correlation must pass."""
    assert not validate_insight_text(text, _NO_CORRELATION)


def test_single_measure_self_correlation_is_not_evidence() -> None:
    """A 1.0 diagonal entry is not a relationship between two fields."""
    analytics = {"correlation_analysis": {"correlation_matrix": {"revenue": {"revenue": 1.0}}}}

    assert validate_insight_text("A strong correlation exists between revenue and cost.", analytics)


def test_missing_correlation_section_does_not_raise() -> None:
    assert isinstance(validate_insight_text("A strong correlation exists.", {}), list)


# ==========================================================
# Wording that slipped past the first pass
# ==========================================================
#
# Two claims in the acceptance-audit generation were unsupported but matched no
# pattern:
#
#   "The AI classification confidence is high at 89.2%, indicating effective
#    initial categorization of tickets."
#
#       A confidence score is the model's own certainty, not a measure of
#       whether the categorisation was right. No metric measures correctness.
#
#   "suggesting that diligent follow-up contributes significantly to
#    successful outcomes"
#
#       A causal assertion drawn from co-occurrence, in everything but the
#       verb "causes".
#
# Both patterns are deliberately narrow, because "effective" and "contributes"
# have common innocent uses that must keep passing.


@pytest.mark.parametrize(
    "text",
    [
        "The AI classification confidence is high at 89.2%, indicating effective initial categorization of tickets.",
        "The results show effective triage across channels.",
        "Routing appears effective.",
    ],
)
def test_flags_asserted_effectiveness_without_a_metric(text: str) -> None:
    assert validate_insight_text(text, _NO_CORRELATION)


@pytest.mark.parametrize(
    "text",
    [
        "suggesting that diligent follow-up contributes significantly to successful outcomes",
        "Follow-up contributes to resolution.",
        "Ticket volume is a driver of delay.",
        "The backlog is attributable to staffing levels.",
        "Channel choice is responsible for the observed outcomes.",
    ],
)
def test_flags_softened_causal_language(text: str) -> None:
    assert validate_insight_text(text, _NO_CORRELATION)


@pytest.mark.parametrize(
    "text",
    [
        # Commencement wording, not performance.
        "The effective date of the policy is 1 January.",
        "Coverage is effective immediately.",
        "The policy is effective from 2026.",
        # Neither asserts that something *is* effective.
        "Consider a cost-effective pricing tier.",
        "Recommend steps to make outreach more effective.",
        # Noun, and a neutral transitive reading.
        "Contributions to the dataset were reviewed.",
        "The report contributes context to the analysis.",
        # Plain prevalence, correctly worded.
        "Closed accounts for 89.0% of records.",
        "Email is the most frequently recorded channel with 20,875 records (74.7%).",
        "Most tickets are recorded as Closed.",
    ],
)
def test_innocent_wording_is_not_flagged(text: str) -> None:
    assert not validate_insight_text(text, _NO_CORRELATION)


def test_effectiveness_still_allowed_with_a_performance_metric() -> None:
    """The gate is the metric, not the wording."""
    analytics = dict(_NO_CORRELATION)
    analytics["numerical_analysis"] = {"resolution_time": {"mean": 4.2}}

    findings = validate_insight_text("The results show effective triage across channels.", analytics)

    assert not any("effectiveness or efficiency" in f for f in findings)
