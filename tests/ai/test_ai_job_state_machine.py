"""
Unit tests for AI job state machine and domain models.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import pytest

from src.ai.exceptions import AIStateTransitionError
from src.ai.models import (
    AIFailureCategory,
    AIJob,
    AIJobStatus,
    VALID_TRANSITIONS,
)


def test_ai_job_status_values() -> None:
    """
    Verify AIJobStatus enum values match specification.
    """
    assert AIJobStatus.PENDING.value == "PENDING"
    assert AIJobStatus.GENERATING.value == "GENERATING"
    assert AIJobStatus.READY.value == "READY"
    assert AIJobStatus.FAILED.value == "FAILED"


def test_ai_failure_categories() -> None:
    """
    Verify AIFailureCategory enum values match specification.
    """
    assert AIFailureCategory.TIMEOUT.value == "TIMEOUT"
    assert (
        AIFailureCategory.PROVIDER_UNAVAILABLE.value
        == "PROVIDER_UNAVAILABLE"
    )
    assert AIFailureCategory.MODEL_ERROR.value == "MODEL_ERROR"
    assert AIFailureCategory.INVALID_OUTPUT.value == "INVALID_OUTPUT"
    assert AIFailureCategory.SYSTEM_ERROR.value == "SYSTEM_ERROR"


def test_valid_state_transitions() -> None:
    """
    Verify allowed state transitions per ADR-025.
    """
    job = AIJob(
        id=1,
        job_id="job_test_001",
        pipeline_run_id=10,
        status=AIJobStatus.PENDING,
    )
    assert job.can_transition_to(AIJobStatus.GENERATING) is True
    assert job.can_transition_to(AIJobStatus.READY) is False
    assert job.can_transition_to(AIJobStatus.FAILED) is False

    job.transition_to(AIJobStatus.GENERATING)
    assert job.status == AIJobStatus.GENERATING

    # From GENERATING -> READY
    assert job.can_transition_to(AIJobStatus.READY) is True
    assert job.can_transition_to(AIJobStatus.FAILED) is True
    assert job.can_transition_to(AIJobStatus.PENDING) is True

    # Transition to READY (Terminal Success)
    job.transition_to(AIJobStatus.READY)
    assert job.status == AIJobStatus.READY
    assert job.is_complete is True
    assert job.is_terminal is True
    assert job.can_transition_to(AIJobStatus.GENERATING) is False
    assert job.can_transition_to(AIJobStatus.FAILED) is False
    assert job.can_transition_to(AIJobStatus.PENDING) is False


def test_invalid_state_transition_raises_error() -> None:
    """
    Verify invalid state transition raises AIStateTransitionError.
    """
    job = AIJob(
        id=2,
        job_id="job_test_002",
        pipeline_run_id=11,
        status=AIJobStatus.READY,
    )
    with pytest.raises(AIStateTransitionError) as exc_info:
        job.transition_to(AIJobStatus.GENERATING)

    assert "Invalid transition from READY to GENERATING" in str(exc_info.value)


def test_failed_to_pending_retry_transition() -> None:
    """
    Verify FAILED state can transition to PENDING upon retry.
    """
    job = AIJob(
        id=3,
        job_id="job_test_003",
        pipeline_run_id=12,
        status=AIJobStatus.FAILED,
    )
    assert job.can_transition_to(AIJobStatus.PENDING) is True
    assert job.can_transition_to(AIJobStatus.GENERATING) is False
    assert job.can_transition_to(AIJobStatus.READY) is False

    job.transition_to(AIJobStatus.PENDING)
    assert job.status == AIJobStatus.PENDING


def test_ai_job_serialization() -> None:
    """
    Verify AIJob to_dict and from_dict roundtrip.
    """
    job = AIJob(
        id=4,
        job_id="job_test_004",
        pipeline_run_id=13,
        user_id=1,
        report_id=5,
        status=AIJobStatus.GENERATING,
        provider="ollama",
        model="gemma3:4b",
        attempt_count=1,
        max_attempts=3,
        error=None,
        failure_category=None,
        created_at="2026-08-15T12:00:00Z",
        started_at="2026-08-15T12:00:01Z",
        completed_at=None,
        updated_at="2026-08-15T12:00:01Z",
    )

    data = job.to_dict()
    assert data["job_id"] == "job_test_004"
    assert data["status"] == "GENERATING"
    assert data["attempt_count"] == 1

    reconstructed = AIJob.from_dict(data)
    assert reconstructed.job_id == job.job_id
    assert reconstructed.status == AIJobStatus.GENERATING
    assert reconstructed.user_id == 1
