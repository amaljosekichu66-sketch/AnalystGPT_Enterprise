"""
Concurrency, Idempotency, and Durability Tests for AI Job Subsystem.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance

Tests:
1. Concurrent duplicate creation (exactly 1 job created).
2. Concurrent worker claims (exactly 1 worker claims).
3. Persistent report_id association and scoping.
4. Process restart / worker crash recovery.
5. Retry identity preservation (same job_id, no duplicate rows).
6. Total failure isolation (provider failure, timeout, invalid output).
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from src.ai.models import AIFailureCategory, AIJobStatus
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.schema_manager import SchemaManager


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Create a dedicated, isolated test database for concurrency checks.
    """
    db_file = str(tmp_path / "test_concurrency.db")
    monkeypatch.setattr("src.core.config.SQLITE_DATABASE_PATH", db_file)

    conn = ConnectionFactory.create_connection()
    conn.connect()
    schema = SchemaManager(conn)
    schema.initialize_schema()

    raw_conn = conn.get_connection()
    raw_conn.execute("""
        INSERT INTO users (id, username, email, hashed_password, role, status)
        VALUES (1, 'concurrency_user', 'user@enterprise.com', 'hashed_pw', 'ANALYST', 'ACTIVE');
        """)
    raw_conn.execute("INSERT INTO pipeline_runs (id, status) VALUES (1, 'SUCCESS');")
    raw_conn.execute(
        "INSERT INTO reports (id, pipeline_run_id, user_id, report_path) VALUES (1, 1, 1, 'reports/report.txt');"
    )
    conn.commit()

    yield conn
    conn.close()


# ==========================================================
# 1. Concurrent Duplicate Job Creation
# ==========================================================


def test_concurrent_duplicate_job_creation(test_db) -> None:
    """
    Verify that N concurrent threads attempting to create an AI job for the same
    logical pipeline run result in exactly ONE database record.
    """
    thread_count = 6
    barrier = threading.Barrier(thread_count)
    results = []

    def attempt_create(index: int):
        thread_conn = ConnectionFactory.create_connection()
        thread_conn.connect()
        try:
            repo = AIJobRepository(thread_conn)
            barrier.wait()  # Synchronize threads for simultaneous execution
            job = repo.create_job(
                job_id=f"concurrent_job_{index}",
                pipeline_run_id=1,
                user_id=1,
                report_id=1,
            )
            return job
        except Exception as exc:
            return exc
        finally:
            thread_conn.close()

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(attempt_create, i) for i in range(thread_count)]
        for fut in as_completed(futures):
            results.append(fut.result())

    # Ensure no thread threw an unhandled crash
    assert all(not isinstance(r, Exception) for r in results)

    # All returned jobs must have the same pipeline_run_id and report_id
    pipeline_run_ids = {r.pipeline_run_id for r in results}
    assert pipeline_run_ids == {1}

    # Exactly ONE job ID was established in the DB
    distinct_job_ids = {r.job_id for r in results}
    assert len(distinct_job_ids) == 1

    # Verify directly against database count
    repo = AIJobRepository(test_db)
    all_jobs = repo.list_jobs_scoped(user_id=1)
    assert len(all_jobs) == 1
    assert all_jobs[0].pipeline_run_id == 1
    assert all_jobs[0].report_id == 1


# ==========================================================
# 2. Concurrent Worker Claim
# ==========================================================


def test_concurrent_worker_claim(test_db) -> None:
    """
    Verify that N concurrent workers attempting to claim the same pending job
    results in exactly ONE worker succeeding, while all others receive None.
    """
    repo = AIJobRepository(test_db)
    repo.create_job(
        job_id="claim_race_job_001",
        pipeline_run_id=1,
        user_id=1,
        report_id=1,
    )

    worker_count = 5
    barrier = threading.Barrier(worker_count)
    claimed_results = []

    def worker_claim():
        worker_conn = ConnectionFactory.create_connection()
        worker_conn.connect()
        try:
            w_repo = AIJobRepository(worker_conn)
            barrier.wait()  # Synchronize all workers to claim simultaneously
            return w_repo.claim_next_pending_job()
        finally:
            worker_conn.close()

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(worker_claim) for _ in range(worker_count)]
        for fut in as_completed(futures):
            claimed_results.append(fut.result())

    non_none_claims = [c for c in claimed_results if c is not None]
    none_claims = [c for c in claimed_results if c is None]

    assert len(non_none_claims) == 1
    assert len(none_claims) == worker_count - 1

    claimed_job = non_none_claims[0]
    assert claimed_job.job_id == "claim_race_job_001"
    assert claimed_job.status == AIJobStatus.GENERATING
    assert claimed_job.attempt_count == 1

    # In DB, status is GENERATING and cannot be claimed again
    second_claim = repo.claim_next_pending_job()
    assert second_claim is None


# ==========================================================
# 3. Persistent report_id Association & Scoping
# ==========================================================


def test_report_id_persistent_association_and_scoping(test_db) -> None:
    """
    Verify that an AIJob correctly persists and associates report_id,
    and supports lookup by report_id with tenant scoping.
    """
    repo = AIJobRepository(test_db)
    created_job = repo.create_job(
        job_id="job_with_report_123",
        pipeline_run_id=1,
        user_id=1,
        report_id=1,
    )

    assert created_job.report_id == 1

    # Lookup by report_id
    found = repo.get_by_report_id(report_id=1, user_id=1)
    assert found is not None
    assert found.job_id == "job_with_report_123"
    assert found.pipeline_run_id == 1
    assert found.user_id == 1
    assert found.report_id == 1

    # Unauthorized tenant query returns None
    unauthorized = repo.get_by_report_id(report_id=1, user_id=999)
    assert unauthorized is None


# ==========================================================
# 4. Process Restart / Worker Crash Recovery
# ==========================================================


def test_process_restart_recovery_of_stale_jobs(test_db) -> None:
    """
    Unfinished jobs whose lease has expired are failed on startup (L12).

    A job runs from an in-memory ReportingReport, so an interrupted job can
    never resume: it used to be reset to PENDING and stay there forever. And
    only EXPIRED leases count, so one process starting up leaves another
    process's in-flight job alone.
    """
    repo = AIJobRepository(test_db)

    repo.create_job(job_id="stale_generating_001", pipeline_run_id=1, user_id=1, report_id=1, max_attempts=3)
    repo.claim_next_pending_job()

    test_db.get_connection().execute("INSERT INTO pipeline_runs (id, status) VALUES (2, 'SUCCESS');")
    test_db.get_connection().execute("INSERT INTO pipeline_runs (id, status) VALUES (3, 'SUCCESS');")
    test_db.commit()
    repo.create_job(job_id="stale_pending_002", pipeline_run_id=2, user_id=1, report_id=1, max_attempts=1)
    repo.create_job(job_id="live_generating_003", pipeline_run_id=3, user_id=1, report_id=1, max_attempts=3)

    # The first two leases ran out (their process died); the third is live.
    test_db.get_connection().execute(
        "UPDATE ai_jobs SET lease_expires_at = 1 WHERE job_id IN ('stale_generating_001', 'stale_pending_002');"
    )
    test_db.get_connection().execute("UPDATE ai_jobs SET status = 'GENERATING' WHERE job_id = 'live_generating_003';")
    test_db.commit()

    recovered_count = repo.recover_stale_jobs()
    assert recovered_count == 2

    for job_id in ("stale_generating_001", "stale_pending_002"):
        job = repo.get_by_job_id(job_id)
        assert job is not None
        assert job.status == AIJobStatus.FAILED
        assert job.failure_category == AIFailureCategory.SYSTEM_ERROR.value
        assert "Interrupted" in (job.error or "")

    live = repo.get_by_job_id("live_generating_003")
    assert live is not None and live.status == AIJobStatus.GENERATING


def test_late_transitions_cannot_overwrite_a_finished_job(test_db) -> None:
    """mark_failed / schedule_retry are conditional on the current state (L12)."""
    repo = AIJobRepository(test_db)
    repo.create_job(job_id="finished_001", pipeline_run_id=1, user_id=1, report_id=1)
    repo.claim_next_pending_job()
    assert repo.mark_ready("finished_001") is True

    assert repo.mark_failed("finished_001", error="late failure") is False
    assert repo.schedule_retry("finished_001", error="late retry") is False
    assert repo.get_by_job_id("finished_001").status == AIJobStatus.READY


# ==========================================================
# 5. Retry Operates on Same Job Identity
# ==========================================================


def test_retry_operates_on_same_identity(test_db) -> None:
    """
    Verify that retrying a FAILED job operates on the exact same job_id without
    creating duplicate database rows.
    """
    repo = AIJobRepository(test_db)
    repo.create_job(
        job_id="retry_identity_001",
        pipeline_run_id=1,
        user_id=1,
        report_id=1,
    )
    repo.claim_next_pending_job()
    repo.mark_failed("retry_identity_001", error="Provider timeout", failure_category="TIMEOUT")

    # Initial failed state
    failed_job = repo.get_by_job_id("retry_identity_001")
    assert failed_job is not None
    assert failed_job.status == AIJobStatus.FAILED

    # Schedule retry
    success = repo.schedule_retry("retry_identity_001", error="Manual retry requested")
    assert success is True

    # Check that status is now PENDING and row count is still exactly 1
    retried_job = repo.get_by_job_id("retry_identity_001")
    assert retried_job is not None
    assert retried_job.status == AIJobStatus.PENDING
    assert retried_job.job_id == "retry_identity_001"

    all_jobs = repo.list_jobs_scoped(user_id=1)
    assert len(all_jobs) == 1


# ==========================================================
# 6. Failure Isolation Reconfirmation
# ==========================================================


def test_failure_isolation_reconfirmation(test_db) -> None:
    """
    Reconfirm that AI job failure transitions never impact deterministic report persistence.
    """
    job_repo = AIJobRepository(test_db)
    report_repo = AIReportRepository(test_db)

    job_repo.create_job(
        job_id="isolation_job_001",
        pipeline_run_id=1,
        user_id=1,
        report_id=1,
    )
    job_repo.claim_next_pending_job()
    job_repo.mark_failed(
        job_id="isolation_job_001",
        error="503 Service Unavailable: Ollama offline",
        failure_category=AIFailureCategory.PROVIDER_UNAVAILABLE,
    )

    # Verify no AI report was persisted for this failed job
    assert report_repo.get_by_job_id("isolation_job_001") is None

    # Verify deterministic report in `reports` table is intact
    cur = test_db.get_connection().cursor()
    cur.execute("SELECT * FROM reports WHERE id = 1;")
    deterministic_report = cur.fetchone()
    assert deterministic_report is not None

    # Verify pipeline run status remains SUCCESS
    cur.execute("SELECT status FROM pipeline_runs WHERE id = 1;")
    status_row = cur.fetchone()
    assert status_row[0] == "SUCCESS"
