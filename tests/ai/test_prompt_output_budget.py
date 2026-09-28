"""
Regression tests: the prompt must not ask for more output than it can emit.

The defect
----------
The prompt requested up to 200 + ~100 + 300 + 500 = 1,100 words across its four
sections, roughly 1,460 tokens. `AI_MAX_TOKENS` defaults to 1,024. The model
was instructed to write about 40% more than it was permitted to produce.

Evidence in a real generated report (`ai_reports.id=49`): the NARRATIVE ends

    "...highlights an area for potential improvement in lead qualification
     and initial outreach"

with no closing punctuation - generation stopped when the budget ran out. When
the cut lands slightly earlier a whole heading is lost, `_parse_sections`
raises "Missing required AI sections", and the job spends another full
inference attempt - minutes of CPU on this deployment - retrying into the same
wall.

The two numbers live in different modules, so nothing previously connected
them. These tests do.
"""

from __future__ import annotations

import importlib

import pytest

from src.llm import prompt_builder
from src.llm.prompt_builder import PromptBuilder


@pytest.fixture()
def production_config(monkeypatch: pytest.MonkeyPatch):
    """
    Config as a production process reads it.

    `tests/conftest.py` clamps AI_TIMEOUT for unit runs; the token budget is
    untouched, but the reload has to start from a clean environment.
    """
    from src.core import config

    monkeypatch.delenv("AI_TIMEOUT", raising=False)
    monkeypatch.delenv("AI_MAX_TOKENS", raising=False)
    reloaded = importlib.reload(config)
    yield reloaded
    monkeypatch.undo()
    importlib.reload(config)


# ==========================================================
# The invariant
# ==========================================================


def test_requested_output_fits_the_token_budget(production_config) -> None:
    """The headline invariant, asserted directly."""
    estimated = prompt_builder.estimated_output_tokens()
    ceiling = production_config.AI_MAX_TOKENS * prompt_builder.OUTPUT_BUDGET_HEADROOM

    assert estimated <= ceiling, (
        f"The prompt asks for ~{estimated} tokens of prose but AI_MAX_TOKENS "
        f"is {production_config.AI_MAX_TOKENS}. Generation will be cut off "
        "mid-section. Lower the per-section word limits or raise AI_MAX_TOKENS."
    )


def test_budget_leaves_headroom_for_structure(production_config) -> None:
    """Headings and list markers consume tokens the word counts ignore."""
    assert prompt_builder.OUTPUT_BUDGET_HEADROOM < 1.0
    assert prompt_builder.estimated_output_tokens() < production_config.AI_MAX_TOKENS


def test_total_requested_words_sums_every_section() -> None:
    expected = (
        prompt_builder.MAX_EXECUTIVE_SUMMARY_WORDS
        + prompt_builder.MAX_RECOMMENDATIONS * prompt_builder.MAX_WORDS_PER_RECOMMENDATION
        + prompt_builder.MAX_EXPLANATIONS_WORDS
        + prompt_builder.MAX_NARRATIVE_WORDS
    )

    assert prompt_builder.total_requested_words() == expected


# ==========================================================
# The limits must actually reach the prompt
# ==========================================================


class _StubStructuredReport:
    executive_summary = "Deterministic baseline summary."
    kpis = {"Rows": 100}
    recommendations = ["Review the findings."]
    analytics = {
        "descriptive_statistics": {"total_rows": 100, "numeric_column_count": 1},
        "numerical_analysis": {"revenue": {"mean": 42.0, "median": 41.0}},
    }


class _StubReportingReport:
    report = _StubStructuredReport()
    execution_time = 1.0


def _prompt() -> str:
    return PromptBuilder.full_report(_StubReportingReport())


def test_section_limits_are_interpolated_not_hard_coded() -> None:
    """A limit that only lives in prose cannot be kept consistent."""
    prompt = _prompt()

    assert f"Maximum {prompt_builder.MAX_EXECUTIVE_SUMMARY_WORDS} words" in prompt
    assert f"Maximum {prompt_builder.MAX_EXPLANATIONS_WORDS} words" in prompt
    assert f"Maximum {prompt_builder.MAX_NARRATIVE_WORDS} words" in prompt
    assert f"Maximum {prompt_builder.MAX_RECOMMENDATIONS} recommendations" in prompt


def test_prompt_states_the_combined_ceiling() -> None:
    """The model is told the total, not just the per-section maxima."""
    assert f"{prompt_builder.total_requested_words()} words" in _prompt()


def test_superseded_limits_are_gone() -> None:
    """The old values must not survive anywhere in the prompt text."""
    prompt = _prompt()

    assert "Maximum 500 words" not in prompt
    assert "Maximum 300 words" not in prompt
    assert "Target 250–400 words" not in prompt


# ==========================================================
# The integrity rules must survive the trim
# ==========================================================


@pytest.mark.parametrize(
    "rule",
    [
        "PREVALENCE IS NOT PERFORMANCE",
        "NO CAUSAL CLAIMS",
        "STATISTICAL INTERPRETATION",
        "CARDINALITY VS PERCENTAGE FREQUENCY",
        "UNTRUSTED DATA DELIMITER",
        "EVIDENCE LEVELS",
    ],
)
def test_analytical_integrity_rules_are_retained(rule: str) -> None:
    """
    Shortening the output budget must not cost a single constraint. These are
    the rules that keep the model explaining facts rather than inventing them.
    """
    assert rule in _prompt()


def test_authoritative_interpretation_is_still_binding() -> None:
    prompt = _prompt()

    assert "DO NOT CONTRADICT" in prompt
    assert "EXCESS kurtosis" in prompt
