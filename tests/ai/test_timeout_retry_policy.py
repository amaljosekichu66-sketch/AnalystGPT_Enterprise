"""
Regression tests for retry behaviour when inference exceeds the budget.

The problem
-----------
Every TIMEOUT was retryable, up to `max_attempts`. On this deployment - CPU
inference, prompt evaluation around 24 tokens/second - a report that does not
fit the budget never fits the budget: the retry runs the same prompt, on the
same hardware, against the same `AI_TIMEOUT`, and is cut off at the same point.

The measured cost of a systematic timeout under the old default was three
attempts at up to 120s each before the job failed anyway - roughly six minutes
of CPU spent proving the same thing three times, while the user waited.

The distinction that matters is not "did it time out" but "how much of the
budget did it use". A request cut off at the full budget was still making
progress and needed more time. A request that failed after a few seconds hit
something transient and is genuinely worth retrying.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.ai.job_executor import AIJobExecutor
from src.ai.models import AIFailureCategory
from src.core import config


@pytest.fixture()
def executor() -> AIJobExecutor:
    instance = AIJobExecutor(max_workers=1, ai_manager=MagicMock())
    yield instance
    instance.shutdown(wait=False, cancel_pending=True)


def _job(attempt_count: int = 1, max_attempts: int = 3) -> MagicMock:
    job = MagicMock()
    job.job_id = "ai_job_test"
    job.attempt_count = attempt_count
    job.max_attempts = max_attempts
    return job


def _timeout_error() -> Exception:
    """A wrapped provider timeout, as the domain layer actually raises it."""
    import httpx

    try:
        try:
            raise httpx.ReadTimeout("read timed out")
        except httpx.ReadTimeout as cause:
            raise RuntimeError("LLM generation failed.") from cause
    except RuntimeError as error:
        return error


# ==========================================================
# Classification of the timeout itself
# ==========================================================


def test_budget_exhausting_timeout_is_systematic(executor: AIJobExecutor) -> None:
    assert executor._timeout_is_systematic(AIFailureCategory.TIMEOUT, config.AI_TIMEOUT)


def test_early_timeout_is_not_systematic(executor: AIJobExecutor) -> None:
    """A fast failure can be transient; it stays retryable."""
    assert not executor._timeout_is_systematic(AIFailureCategory.TIMEOUT, 3.0)


def test_unknown_duration_preserves_retry_behaviour(
    executor: AIJobExecutor,
) -> None:
    """Without evidence, behave as before rather than guessing."""
    assert not executor._timeout_is_systematic(AIFailureCategory.TIMEOUT, None)


def test_other_categories_are_unaffected(executor: AIJobExecutor) -> None:
    for category in (
        AIFailureCategory.PROVIDER_UNAVAILABLE,
        AIFailureCategory.MODEL_ERROR,
        AIFailureCategory.SYSTEM_ERROR,
    ):
        assert not executor._timeout_is_systematic(category, config.AI_TIMEOUT)


# ==========================================================
# The resulting job transition
# ==========================================================


def test_systematic_timeout_fails_permanently_without_retrying(
    executor: AIJobExecutor,
) -> None:
    """The retry storm: three full inference attempts, same outcome."""
    repository = MagicMock()

    executor._handle_failure(
        job=_job(attempt_count=1),
        error=_timeout_error(),
        reporting_report=None,
        job_repo=repository,
        attempt_seconds=config.AI_TIMEOUT,
    )

    repository.schedule_retry.assert_not_called()
    repository.mark_failed.assert_called_once()
    assert executor._retry_timers == set()


def test_permanent_timeout_message_explains_the_cause(
    executor: AIJobExecutor,
) -> None:
    """The operator needs to know which lever to pull."""
    repository = MagicMock()

    executor._handle_failure(
        job=_job(attempt_count=1),
        error=_timeout_error(),
        reporting_report=None,
        job_repo=repository,
        attempt_seconds=config.AI_TIMEOUT,
    )

    message = repository.mark_failed.call_args.kwargs["error"]

    assert "AI_TIMEOUT" in message
    assert "capacity limit" in message
    assert repository.mark_failed.call_args.kwargs["failure_category"] is (AIFailureCategory.TIMEOUT)


def test_transient_timeout_is_still_retried(executor: AIJobExecutor) -> None:
    """The fix must not disable retries for genuinely transient failures."""
    repository = MagicMock()

    executor._handle_failure(
        job=_job(attempt_count=1),
        error=_timeout_error(),
        reporting_report=None,
        job_repo=repository,
        attempt_seconds=2.0,
    )

    repository.schedule_retry.assert_called_once()
    repository.mark_failed.assert_not_called()

    for timer in list(executor._retry_timers):
        timer.cancel()


def test_provider_unavailable_is_still_retried(executor: AIJobExecutor) -> None:
    """A server that is down now may be up in a few seconds."""
    import httpx

    repository = MagicMock()

    try:
        try:
            raise httpx.ConnectError("connection refused")
        except httpx.ConnectError as cause:
            raise RuntimeError("LLM generation failed.") from cause
    except RuntimeError as error:
        executor._handle_failure(
            job=_job(attempt_count=1),
            error=error,
            reporting_report=None,
            job_repo=repository,
            attempt_seconds=config.AI_TIMEOUT,
        )

    repository.schedule_retry.assert_called_once()

    for timer in list(executor._retry_timers):
        timer.cancel()


def test_exhausted_attempts_still_fail_permanently(
    executor: AIJobExecutor,
) -> None:
    repository = MagicMock()

    executor._handle_failure(
        job=_job(attempt_count=3, max_attempts=3),
        error=_timeout_error(),
        reporting_report=None,
        job_repo=repository,
        attempt_seconds=2.0,
    )

    repository.mark_failed.assert_called_once()


# ==========================================================
# The budget itself
# ==========================================================


def test_production_timeout_covers_measured_inference_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Measured on this deployment, end to end through the production path: a
    cold full report generation took 340.2s, and two live generations hit the
    previous 300s budget (one raising ReadTimeout at 302.0s). Prompt-eval
    throughput varies 15-24 tok/s with machine load, so the budget needs
    margin rather than a tight fit.

    `AI_TIMEOUT` must be removed from the environment first: `tests/conftest.py`
    clamps it to the 15s unit-test ceiling, which is the run this test executes
    in. The assertion is about the value a *production* process would read.
    """
    import importlib

    monkeypatch.delenv("AI_TIMEOUT", raising=False)

    try:
        assert importlib.reload(config).AI_TIMEOUT >= 400.0
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_unit_test_runs_remain_clamped() -> None:
    """
    The production default must not leak into ordinary test runs: a 300s
    budget would let a stray live call block the suite for five minutes.
    """
    from tests.conftest import UNIT_TEST_AI_TIMEOUT_CEILING

    assert config.AI_TIMEOUT <= UNIT_TEST_AI_TIMEOUT_CEILING
