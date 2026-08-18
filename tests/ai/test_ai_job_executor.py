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
    clean_db.get_connection().execute(
        "INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');"
    )
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
    clean_db.get_connection().execute(
        "INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');"
    )
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
    clean_db.get_connection().execute(
        "INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');"
    )
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
    clean_db.get_connection().execute(
        "INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');"
    )
    clean_db.commit()

    job_repo = AIJobRepository(clean_db)
    job_repo.create_job(
        job_id="ai_exec_test_004",
        pipeline_run_id=1,
        user_id=1,
        max_attempts=1,
    )

    mock_ai_manager = MagicMock(spec=AIManager)
    mock_ai_manager.generate_ai_report.side_effect = RuntimeError(
        "Simulated unexpected AI runtime crash"
    )

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
