"""
Unit tests for AIJobRepository and AIReportRepository persistence.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import pytest

from src.ai.ai_report import AIReport
from src.ai.models import AIFailureCategory, AIJobStatus
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.schema_manager import SchemaManager


@pytest.fixture
def db_connection(tmp_path, monkeypatch):
    """
    Create an isolated database connection with schema initialized.
    """
    db_file = str(tmp_path / "test_ai_repo.db")
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
    conn_raw.execute(
        "INSERT INTO users (id, username, email, hashed_password, role, status) VALUES (?, ?, ?, ?, ?, 'ACTIVE');",
        (2, "analyst_2", "user2@test.com", "hash", "ANALYST"),
    )
    connection.commit()

    yield connection
    connection.close()


def test_create_and_get_ai_job(db_connection) -> None:
    """
    Verify creating an AI job and fetching it by job_id and pipeline_run_id.
    """
    job_repo = AIJobRepository(db_connection)

    # First insert a mock pipeline run
    db_connection.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    db_connection.commit()

    job = job_repo.create_job(
        job_id="ai_job_test_101",
        pipeline_run_id=1,
        user_id=1,
        report_id=None,
        provider="ollama",
        model="gemma3:4b",
        max_attempts=3,
    )

    assert job is not None
    assert job.job_id == "ai_job_test_101"
    assert job.pipeline_run_id == 1
    assert job.status == AIJobStatus.PENDING
    assert job.attempt_count == 0
    assert job.max_attempts == 3

    # Fetch by job_id
    fetched = job_repo.get_by_job_id("ai_job_test_101")
    assert fetched is not None
    assert fetched.job_id == "ai_job_test_101"
    assert fetched.user_id == 1

    # Fetch with user scoping
    scoped_match = job_repo.get_by_job_id("ai_job_test_101", user_id=1)
    assert scoped_match is not None

    scoped_mismatch = job_repo.get_by_job_id("ai_job_test_101", user_id=999)
    assert scoped_mismatch is None

    # Fetch by pipeline_run_id
    pipeline_match = job_repo.get_by_pipeline_run_id(1)
    assert pipeline_match is not None
    assert pipeline_match.job_id == "ai_job_test_101"


def test_ai_job_idempotent_creation(db_connection) -> None:
    """
    Verify that create_job is idempotent when called multiple times with same pipeline_run_id.
    """
    job_repo = AIJobRepository(db_connection)

    db_connection.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    db_connection.commit()

    job1 = job_repo.create_job(
        job_id="ai_job_first",
        pipeline_run_id=1,
        user_id=2,
    )

    job2 = job_repo.create_job(
        job_id="ai_job_duplicate",
        pipeline_run_id=1,
        user_id=2,
    )

    assert job1.job_id == job2.job_id
    assert job2.job_id == "ai_job_first"


def test_atomic_claim_next_pending_job(db_connection) -> None:
    """
    Verify atomic claim transitions PENDING to GENERATING and increments attempt count.
    """
    job_repo = AIJobRepository(db_connection)

    db_connection.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    db_connection.commit()

    job_repo.create_job(
        job_id="ai_job_claim_test",
        pipeline_run_id=1,
        user_id=1,
    )

    claimed = job_repo.claim_next_pending_job()
    assert claimed is not None
    assert claimed.job_id == "ai_job_claim_test"
    assert claimed.status == AIJobStatus.GENERATING
    assert claimed.attempt_count == 1
    assert claimed.started_at is not None

    # Subsequent claim should return None since no jobs are PENDING
    second_claim = job_repo.claim_next_pending_job()
    assert second_claim is None


def test_mark_ready_and_report_persistence(db_connection) -> None:
    """
    Verify transition to READY and AIReportRepository storage.
    """
    job_repo = AIJobRepository(db_connection)
    report_repo = AIReportRepository(db_connection)

    db_connection.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    db_connection.commit()

    job_repo.create_job(
        job_id="ai_job_ready_test",
        pipeline_run_id=1,
        user_id=1,
    )
    job_repo.claim_next_pending_job()

    # Mark ready
    success = job_repo.mark_ready("ai_job_ready_test")
    assert success is True

    ready_job = job_repo.get_by_job_id("ai_job_ready_test")
    assert ready_job is not None
    assert ready_job.status == AIJobStatus.READY
    assert ready_job.completed_at is not None

    # Persist report
    sample_report = AIReport(
        executive_summary="Sample executive summary text.",
        recommendations=["Rec 1", "Rec 2"],
        explanations=["Expl 1", "Expl 2"],
        narrative="Comprehensive business narrative.",
        model="gemma3:4b",
        provider="ollama",
        execution_time=1.45,
    )

    report_id = report_repo.save_ai_report(
        job_id="ai_job_ready_test",
        pipeline_run_id=1,
        ai_report=sample_report,
        user_id=1,
    )
    assert report_id is not None

    fetched_report = report_repo.get_by_job_id("ai_job_ready_test")
    assert fetched_report is not None
    assert fetched_report["executive_summary"] == "Sample executive summary text."
    assert fetched_report["recommendations"] == ["Rec 1", "Rec 2"]
    assert fetched_report["explanations"] == ["Expl 1", "Expl 2"]
    assert fetched_report["model"] == "gemma3:4b"


def test_mark_failed_and_schedule_retry(db_connection) -> None:
    """
    Verify scheduling retries and transitioning to FAILED state.
    """
    job_repo = AIJobRepository(db_connection)

    db_connection.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    db_connection.commit()

    job_repo.create_job(
        job_id="ai_job_fail_test",
        pipeline_run_id=1,
        user_id=1,
    )
    job_repo.claim_next_pending_job()

    # Schedule retry
    retry_ok = job_repo.schedule_retry(
        job_id="ai_job_fail_test",
        error="Connection timeout",
        failure_category=AIFailureCategory.TIMEOUT,
    )
    assert retry_ok is True

    retrying_job = job_repo.get_by_job_id("ai_job_fail_test")
    assert retrying_job is not None
    assert retrying_job.status == AIJobStatus.PENDING
    assert retrying_job.error == "Connection timeout"
    assert retrying_job.failure_category == "TIMEOUT"

    # Mark permanent failure
    fail_ok = job_repo.mark_failed(
        job_id="ai_job_fail_test",
        error="Permanent provider outage",
        failure_category=AIFailureCategory.PROVIDER_UNAVAILABLE,
    )
    assert fail_ok is True

    failed_job = job_repo.get_by_job_id("ai_job_fail_test")
    assert failed_job is not None
    assert failed_job.status == AIJobStatus.FAILED
    assert failed_job.error == "Permanent provider outage"
    assert failed_job.failure_category == "PROVIDER_UNAVAILABLE"
    assert failed_job.completed_at is not None
