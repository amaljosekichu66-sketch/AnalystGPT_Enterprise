"""
Unit tests for AIJobExecutor and background worker isolation.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.ai.ai_manager import AIManager
from src.ai.ai_report import AIReport
from src.ai.ai_result import AIResult
from src.ai.job_executor import AIJobExecutor
from src.ai.models import AIFailureCategory, AIJobStatus
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.schema_manager import SchemaManager
from src.reporting.reporting_report import ReportingReport


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """
    Provide clean isolated database schema for executor tests.
    """
    db_file = str(tmp_path / "test_ai_exec.db")
    monkeypatch.setattr("src.core.config.SQLITE_DATABASE_PATH", db_file)
    connection = ConnectionFactory.create_connection()
    connection.connect()
    schema = SchemaManager(connection)
    schema.initialize_schema()

    conn_raw = connection.get_connection()
    conn_raw.execute(
        "INSERT INTO users (id, username, email, hashed_password, role, status) VALUES (?, ?, ?, ?, ?, 'ACTIVE');",
        (1, "analyst_1", "user1@test.com", "hash", "ANALYST"),
    )
    connection.commit()

    yield connection
    connection.close()


def test_executor_successful_run(clean_db) -> None:
    """
    Verify AIJobExecutor executes successfully and transitions job to READY.
    """
    clean_db.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    clean_db.commit()

    job_repo = AIJobRepository(clean_db)
    job_repo.create_job(
        job_id="ai_exec_test_001",
        pipeline_run_id=1,
        user_id=1,
    )

    # Mock AI Manager
    mock_ai_manager = MagicMock(spec=AIManager)
    mock_report = AIReport(
        executive_summary="AI Executive Summary Test.",
        recommendations=["Action A", "Action B"],
        explanations=["Explanation 1"],
        narrative="AI Narrative Body.",
        model="gemma3:4b",
        provider="ollama",
        execution_time=0.85,
        prompt_count=1,
    )
    mock_ai_manager.generate_ai_report.return_value = AIResult(
        success=True,
        ai_report=mock_report,
        execution_time=0.85,
    )

    executor = AIJobExecutor(
        max_workers=2,
        ai_manager=mock_ai_manager,
    )

    mock_reporting_report = MagicMock(spec=ReportingReport)

    # Execute synchronously
    success = executor.execute_job_sync(
        job_id="ai_exec_test_001",
        reporting_report=mock_reporting_report,
    )

    assert success is True

    # Verify job status in DB
    updated_job = job_repo.get_by_job_id("ai_exec_test_001")
    assert updated_job is not None
    assert updated_job.status == AIJobStatus.READY
    assert updated_job.completed_at is not None
    assert updated_job.error is None

    # Verify report in DB
    report_repo = AIReportRepository(clean_db)
    saved_report = report_repo.get_by_job_id("ai_exec_test_001")
    assert saved_report is not None
    assert saved_report["executive_summary"] == "AI Executive Summary Test."
    assert saved_report["recommendations"] == ["Action A", "Action B"]

    executor.shutdown(wait=False)


def test_executor_retryable_error_handling(clean_db) -> None:
    """
    Verify retryable error triggers retry scheduling and preserves PENDING state.
    """
    clean_db.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    clean_db.commit()

    job_repo = AIJobRepository(clean_db)
    job_repo.create_job(
        job_id="ai_exec_test_002",
        pipeline_run_id=1,
        user_id=1,
        max_attempts=3,
    )

    # Mock AI Manager returning Timeout Error
    mock_ai_manager = MagicMock(spec=AIManager)
    mock_ai_manager.generate_ai_report.return_value = AIResult(
        success=False,
        error=TimeoutError("Ollama inference request timed out after 120s"),
        execution_time=120.0,
    )

    executor = AIJobExecutor(
        max_workers=1,
        ai_manager=mock_ai_manager,
    )
    mock_reporting_report = MagicMock(spec=ReportingReport)

    # First attempt (attempt_count will become 1, which is < max_attempts 3)
    with patch("threading.Timer") as mock_timer:
        mock_timer_instance = MagicMock()
        mock_timer.return_value = mock_timer_instance

        success = executor.execute_job_sync(
            job_id="ai_exec_test_002",
            reporting_report=mock_reporting_report,
        )

        assert success is False
        assert mock_timer.called

    updated_job = job_repo.get_by_job_id("ai_exec_test_002")
    assert updated_job is not None
    # Because it is scheduled for retry, status is PENDING
    assert updated_job.status == AIJobStatus.PENDING
    assert updated_job.attempt_count == 1
    assert updated_job.failure_category == "TIMEOUT"
    assert "timed out" in (updated_job.error or "")

    executor.shutdown(wait=False)


def test_executor_max_attempts_exhaustion_marks_failed(clean_db) -> None:
    """
    Verify that when attempts reach max_attempts, the job is permanently marked FAILED.
    """
    clean_db.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    clean_db.commit()

    job_repo = AIJobRepository(clean_db)
    job_repo.create_job(
        job_id="ai_exec_test_003",
        pipeline_run_id=1,
        user_id=1,
        max_attempts=1,  # Only 1 attempt allowed
    )

    mock_ai_manager = MagicMock(spec=AIManager)
    mock_ai_manager.generate_ai_report.return_value = AIResult(
        success=False,
        error=ConnectionError("Ollama connection refused"),
        execution_time=0.1,
    )

    executor = AIJobExecutor(
        max_workers=1,
        ai_manager=mock_ai_manager,
    )
    mock_reporting_report = MagicMock(spec=ReportingReport)

    success = executor.execute_job_sync(
        job_id="ai_exec_test_003",
        reporting_report=mock_reporting_report,
    )

    assert success is False

    updated_job = job_repo.get_by_job_id("ai_exec_test_003")
    assert updated_job is not None
    assert updated_job.status == AIJobStatus.FAILED
    assert updated_job.attempt_count == 1
    assert updated_job.failure_category == "PROVIDER_UNAVAILABLE"
    assert updated_job.completed_at is not None

    executor.shutdown(wait=False)


def test_executor_exception_isolation(clean_db) -> None:
    """
    Verify that unhandled exceptions during execution are isolated and do not crash the caller.
    """
    clean_db.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    clean_db.commit()

    job_repo = AIJobRepository(clean_db)
    job_repo.create_job(
        job_id="ai_exec_test_004",
        pipeline_run_id=1,
        user_id=1,
        max_attempts=1,
    )

    mock_ai_manager = MagicMock(spec=AIManager)
    mock_ai_manager.generate_ai_report.side_effect = RuntimeError("Simulated unexpected AI runtime crash")

    executor = AIJobExecutor(
        max_workers=1,
        ai_manager=mock_ai_manager,
    )
    mock_reporting_report = MagicMock(spec=ReportingReport)

    # Should not raise exception
    success = executor.execute_job_sync(
        job_id="ai_exec_test_004",
        reporting_report=mock_reporting_report,
    )

    assert success is False

    updated_job = job_repo.get_by_job_id("ai_exec_test_004")
    assert updated_job is not None
    assert updated_job.status == AIJobStatus.FAILED
    assert "Simulated unexpected AI runtime crash" in (updated_job.error or "")

    executor.shutdown(wait=False)


# ==========================================================
# Failure Classification
# ==========================================================
#
# Regression coverage for a defect that made the retry policy inert: domain
# code wraps provider errors as `RuntimeError("LLM generation failed.")`, and
# the classifier only inspected the outermost exception. Real Ollama timeouts
# were therefore classified SYSTEM_ERROR (permanent) instead of TIMEOUT
# (retryable). A full suite run showed 18 permanent SYSTEM_ERROR failures
# against a single retryable TIMEOUT.


def _classifier() -> AIJobExecutor:
    """Build an executor without touching the LLM or thread pool."""
    return AIJobExecutor.__new__(AIJobExecutor)


def test_classify_error_unwraps_chained_timeout() -> None:
    """A wrapped provider timeout must still classify as retryable TIMEOUT."""
    try:
        try:
            raise TimeoutError("timed out")
        except TimeoutError as cause:
            raise RuntimeError("LLM generation failed.") from cause
    except RuntimeError as wrapped:
        assert _classifier()._classify_error(wrapped) == AIFailureCategory.TIMEOUT


def test_classify_error_unwraps_chained_connection_failure() -> None:
    """A wrapped connection failure must classify as PROVIDER_UNAVAILABLE."""
    try:
        try:
            raise ConnectionRefusedError("connection refused")
        except ConnectionRefusedError as cause:
            raise RuntimeError("LLM generation failed.") from cause
    except RuntimeError as wrapped:
        assert _classifier()._classify_error(wrapped) == AIFailureCategory.PROVIDER_UNAVAILABLE


def test_classify_error_maps_value_error_to_model_error() -> None:
    """ValueError maps to MODEL_ERROR (previously missed via a 'valuerror' typo)."""
    assert _classifier()._classify_error(ValueError("bad payload")) == AIFailureCategory.MODEL_ERROR


def test_classify_error_maps_type_error_to_model_error() -> None:
    """TypeError maps to MODEL_ERROR."""
    assert _classifier()._classify_error(TypeError("bad type")) == AIFailureCategory.MODEL_ERROR


def test_classify_error_defaults_to_system_error() -> None:
    """An unrecognised failure with no informative cause stays SYSTEM_ERROR."""
    assert _classifier()._classify_error(RuntimeError("LLM generation failed.")) == AIFailureCategory.SYSTEM_ERROR


def test_classify_error_accepts_plain_string() -> None:
    """String errors are still supported."""
    assert _classifier()._classify_error("Request timed out") == AIFailureCategory.TIMEOUT


def test_classify_error_survives_self_referential_chain() -> None:
    """Chain walking must terminate on a cyclic __context__."""
    first = RuntimeError("first")
    second = RuntimeError("second")
    first.__context__ = second
    second.__context__ = first

    assert _classifier()._classify_error(first) == AIFailureCategory.SYSTEM_ERROR


# ==========================================================
# Shutdown Lifecycle
# ==========================================================
#
# Regression coverage for a lifecycle race: ThreadPoolExecutor.submit() raises
# RuntimeError once the pool is shut down. AIJobService.create_and_dispatch_job
# calls submit_job() directly, so a request arriving during shutdown propagated
# that RuntimeError out of the request handler, leaving the job row PENDING with
# no explanation. After shutdown the executor must accept no new work, quietly.


def test_submit_job_after_shutdown_is_refused_not_raised() -> None:
    """Submitting after shutdown must not raise; no new work is accepted."""
    executor = AIJobExecutor(max_workers=1, ai_manager=MagicMock())
    executor.shutdown(wait=True, cancel_pending=True)

    # Must not raise RuntimeError("cannot schedule new futures after shutdown").
    executor.submit_job(
        job_id="job_submitted_after_shutdown",
        reporting_report=MagicMock(spec=ReportingReport),
    )


def test_shutdown_is_idempotent() -> None:
    """Repeated shutdown calls must be safe."""
    executor = AIJobExecutor(max_workers=1, ai_manager=MagicMock())

    executor.shutdown(wait=False)
    executor.shutdown(wait=False)
    executor.shutdown(wait=True, cancel_pending=True)


def test_retry_timer_is_not_scheduled_after_shutdown() -> None:
    """A retry must never resubmit work into a drained pool."""
    executor = AIJobExecutor(max_workers=1, ai_manager=MagicMock())
    executor.shutdown(wait=True, cancel_pending=True)

    executor._schedule_retry_timer(
        delay=0.01,
        job_id="job_retry_after_shutdown",
        reporting_report=MagicMock(spec=ReportingReport),
    )

    assert executor._retry_timers == set()


def test_shutdown_cancels_outstanding_retry_timers() -> None:
    """Pending retry timers must be cancelled by shutdown."""
    executor = AIJobExecutor(max_workers=1, ai_manager=MagicMock())

    executor._schedule_retry_timer(
        delay=30.0,
        job_id="job_pending_retry",
        reporting_report=MagicMock(spec=ReportingReport),
    )
    assert len(executor._retry_timers) == 1

    executor.shutdown(wait=True, cancel_pending=True)
    assert executor._retry_timers == set()
