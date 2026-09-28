"""
Regression tests: the context window must hold the prompt AND the response.

The defect
----------
Measured against this deployment with the model's own tokenizer, on the real
21-column dataset:

    production prompt      4,653 tokens
    AI_MAX_TOKENS          1,024 tokens
    required               5,677 tokens
    AI_CONTEXT_WINDOW      4,096 tokens   -> short by 1,581

The prompt alone overflowed by 557 tokens. llama.cpp handles an overflow by
discarding the OLDEST tokens - the head of the prompt, which is where the
ROLE, the OBJECTIVE and the ANALYTICAL INTEGRITY RULES live. So the
anti-hallucination constraints were being evicted before the model read them,
and the remaining room was not enough to finish the response.

The visible symptom was a live generation failing with

    Missing required AI sections: NARRATIVE.
    Found headings: ['EXECUTIVE SUMMARY', 'RECOMMENDATIONS', 'EXPLANATIONS'].
    Response length: 1543 characters.

which reads like a model failure and is actually a budget failure. Nothing in
the system said so: the overflow is silent at the Ollama layer.
"""

from __future__ import annotations

import importlib
import logging

import pytest

from src.core import config
from src.llm import prompt_builder


@pytest.fixture()
def production_config(monkeypatch: pytest.MonkeyPatch):
    """Config as a production process reads it."""
    for name in ("AI_TIMEOUT", "AI_CONTEXT_WINDOW", "AI_MAX_TOKENS"):
        monkeypatch.delenv(name, raising=False)
    reloaded = importlib.reload(config)
    yield reloaded
    monkeypatch.undo()
    importlib.reload(config)


#: Measured with the model's tokenizer on the real dataset.
MEASURED_PRODUCTION_PROMPT_TOKENS = 4_653


# ==========================================================
# The budget invariant
# ==========================================================


def test_context_window_fits_a_real_prompt_plus_the_response(
    production_config,
) -> None:
    required = MEASURED_PRODUCTION_PROMPT_TOKENS + production_config.AI_MAX_TOKENS

    assert production_config.AI_CONTEXT_WINDOW >= required, (
        f"AI_CONTEXT_WINDOW={production_config.AI_CONTEXT_WINDOW} cannot hold a "
        f"measured {MEASURED_PRODUCTION_PROMPT_TOKENS}-token prompt plus "
        f"{production_config.AI_MAX_TOKENS} generated tokens. The prompt head - "
        "the analytical integrity rules - would be silently discarded."
    )


def test_context_window_exceeds_the_prompt_alone(production_config) -> None:
    """The narrower failure: instructions evicted before generation starts."""
    assert production_config.AI_CONTEXT_WINDOW > MEASURED_PRODUCTION_PROMPT_TOKENS


def test_output_budget_and_context_window_are_consistent(
    production_config,
) -> None:
    """The two AI budgets must agree with each other and with the prompt."""
    prose_tokens = prompt_builder.estimated_output_tokens()

    assert prose_tokens <= production_config.AI_MAX_TOKENS
    assert MEASURED_PRODUCTION_PROMPT_TOKENS + production_config.AI_MAX_TOKENS <= production_config.AI_CONTEXT_WINDOW


# ==========================================================
# The overflow must be reported, not silent
# ==========================================================


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    """An OllamaClient without touching a live server."""
    from src.llm.ollama_client import OllamaClient

    monkeypatch.setattr("src.llm.ollama_client.Client", lambda **kwargs: object())
    return OllamaClient()


def test_overflow_is_logged_as_an_error(
    client,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr("src.core.config.AI_CONTEXT_WINDOW", 4096)
    monkeypatch.setattr("src.core.config.AI_MAX_TOKENS", 1024)

    with caplog.at_level(logging.ERROR):
        client._warn_if_context_window_too_small("x" * 17_923)

    assert "CONTEXT WINDOW OVERFLOW" in caplog.text
    assert "AI_CONTEXT_WINDOW" in caplog.text


def test_overflow_message_recommends_a_sufficient_value(
    client,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The operator should not have to compute the fix themselves."""
    monkeypatch.setattr("src.core.config.AI_CONTEXT_WINDOW", 4096)
    monkeypatch.setattr("src.core.config.AI_MAX_TOKENS", 1024)

    with caplog.at_level(logging.ERROR):
        client._warn_if_context_window_too_small("x" * 17_923)

    assert "at least 8192" in caplog.text


def test_no_error_when_the_budget_is_sufficient(
    client,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr("src.core.config.AI_CONTEXT_WINDOW", 8192)
    monkeypatch.setattr("src.core.config.AI_MAX_TOKENS", 1024)

    with caplog.at_level(logging.ERROR):
        client._warn_if_context_window_too_small("x" * 17_923)

    assert "OVERFLOW" not in caplog.text


def test_guard_never_raises(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    A degraded report beats no report, so the guard reports and continues.
    """
    monkeypatch.setattr("src.core.config.AI_CONTEXT_WINDOW", 512)
    monkeypatch.setattr("src.core.config.AI_MAX_TOKENS", 4096)

    client._warn_if_context_window_too_small("x" * 100_000)


def test_token_estimate_matches_the_measured_ratio(client) -> None:
    """
    17,923 characters tokenised to 4,653 tokens on this deployment. The
    estimate must stay close, and must not under-report the size.
    """
    from src.llm.ollama_client import OllamaClient

    estimated = int(17_923 / OllamaClient._CHARS_PER_TOKEN)

    assert estimated >= MEASURED_PRODUCTION_PROMPT_TOKENS
    assert estimated <= MEASURED_PRODUCTION_PROMPT_TOKENS * 1.15


# ==========================================================
# The output budget must also be guarded
# ==========================================================
#
# Found during the final acceptance audit. The context window bounds
# prompt + response; `AI_MAX_TOKENS` bounds the response alone, and nothing
# checked it against the prose the prompt requests.
#
# Measured live with AI_MAX_TOKENS=600 on the real production prompt:
#
#     prompt requests   680 words (~904 tokens)
#     eval_count        600   (exactly the limit)
#     done_reason       "length"
#     response          ended without sentence punctuation
#
# The application never inspects `done_reason`, so this was silent. When the
# cut lands before the last heading it resurfaces as "Missing required AI
# sections", which blames the model for a budget mismatch.


def test_output_budget_guard_fires_when_max_tokens_is_too_small(
    client,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr("src.core.config.AI_MAX_TOKENS", 600)

    with caplog.at_level(logging.ERROR):
        client._warn_if_output_budget_too_small()

    assert "OUTPUT BUDGET TOO SMALL" in caplog.text
    assert "done_reason='length'" in caplog.text


def test_output_budget_guard_recommends_a_sufficient_value(
    client,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr("src.core.config.AI_MAX_TOKENS", 600)

    with caplog.at_level(logging.ERROR):
        client._warn_if_output_budget_too_small()

    recommended = int(prompt_builder.estimated_output_tokens() / prompt_builder.OUTPUT_BUDGET_HEADROOM) + 1
    assert str(recommended) in caplog.text
    assert recommended >= prompt_builder.estimated_output_tokens()


def test_output_budget_guard_silent_at_the_shipped_default(
    client,
    production_config,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The default must not emit a spurious error on every generation."""
    with caplog.at_level(logging.ERROR):
        client._warn_if_output_budget_too_small()

    assert "OUTPUT BUDGET" not in caplog.text


def test_output_budget_guard_never_raises(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.core.config.AI_MAX_TOKENS", 1)

    client._warn_if_output_budget_too_small()
