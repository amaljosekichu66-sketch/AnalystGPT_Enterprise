"""
Regression tests for P2-01, P2-02 and P2-20 (Sprint 15 readiness gate).

- P2-01: a manual retry never ran the job again (no ReportingReport).
- P2-02: interrupted jobs were never resumed; there was no cancel; recovery
  ran before the schema existed on a fresh database.
- P2-20: AIJobService opened a connection on every call and never closed it.
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.ai.ai_job_service import AIJobService
from src.ai.exceptions import AIStateTransitionError
from src.ai.job_executor import AIJobExecutor
from src.ai.models import AIJobStatus
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.schema_manager import SchemaManager
from src.reporting.reporting_report import ReportingReport
from src.reporting.structured_report import StructuredReport

TERMINAL = {AIJobStatus.READY, AIJobStatus.FAILED, AIJobStatus.CANCELLED}


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "jobs.db")
    monkeypatch.setattr(config, "MAX_ACTIVE_AI_JOBS_PER_USER", 100)
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    conn.get_connection().execute("INSERT INTO pipeline_runs (id, status) VALUES (1, 'SUCCESS');")
    conn.commit()
    yield conn
    conn.disconnect()


def _report() -> ReportingReport:
    return ReportingReport(StructuredReport("t", "summary", {"rows": 3}, {}, ["do x"]), "", 0.1)


def _executor() -> AIJobExecutor:
    manager = MagicMock()
    manager.generate_ai_report.return_value = MagicMock(success=False, ai_report=None, error="model said no")
    return AIJobExecutor(max_workers=1, ai_manager=manager)


def _wait_terminal(repo: AIJobRepository, job_id: str, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = repo.get_by_job_id(job_id)
        if job is not None and job.status in TERMINAL:
            return job
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish: {repo.get_by_job_id(job_id)}")


def test_jobs_persist_their_input(db) -> None:
    service = AIJobService()
    job = service.create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=1)
    payload = AIJobRepository(db).get_report_payload(job.job_id)
    assert payload and ReportingReport.from_payload(payload).report.executive_summary == "summary"


def test_manual_retry_runs_the_job_again(db) -> None:
    repo = AIJobRepository(db)
    service = AIJobService()
    job = service.create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=3)
    repo.claim_next_pending_job()
    repo.mark_failed(job.job_id, error="timeout", failure_category="TIMEOUT")

    executor = _executor()
    try:
        AIJobService(job_executor=executor).retry_job(job.job_id)
        finished = _wait_terminal(repo, job.job_id)
    finally:
        executor._executor.shutdown(wait=True)

    assert finished.status in TERMINAL
    assert finished.attempt_count == 2  # it really ran again


def test_restart_resumes_interrupted_jobs(db) -> None:
    repo = AIJobRepository(db)
    job = AIJobService().create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=3)
    repo.claim_next_pending_job()  # GENERATING when the process "died"

    executor = _executor()
    try:
        recovered = AIJobService(job_executor=executor).recover_stale_jobs(ignore_lease=True)
        finished = _wait_terminal(repo, job.job_id)
    finally:
        executor._executor.shutdown(wait=True)

    assert recovered == 1
    assert finished.status in TERMINAL and finished.attempt_count == 2


def test_interrupted_job_without_attempts_left_fails_retryably(db) -> None:
    repo = AIJobRepository(db)
    job = AIJobService().create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=1)
    repo.claim_next_pending_job()

    AIJobService().recover_stale_jobs(ignore_lease=True)

    failed = repo.get_by_job_id(job.job_id)
    assert failed.status == AIJobStatus.FAILED
    assert failed.failure_category == "SYSTEM_ERROR"


class TestCancel:
    def test_pending_job_can_be_cancelled_and_retried(self, db) -> None:
        service = AIJobService()
        job = service.create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=3)

        assert service.cancel_job(job.job_id).status == AIJobStatus.CANCELLED
        assert service.retry_job(job.job_id).status == AIJobStatus.PENDING

    def test_finished_job_cannot_be_cancelled(self, db) -> None:
        repo = AIJobRepository(db)
        service = AIJobService()
        job = service.create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=1)
        repo.claim_next_pending_job()
        repo.mark_ready(job.job_id)

        with pytest.raises(AIStateTransitionError):
            service.cancel_job(job.job_id)

    def test_result_of_a_job_cancelled_mid_generation_is_discarded(self, db) -> None:
        repo = AIJobRepository(db)
        job = AIJobService().create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=1)

        def generate(*_a, **_k):
            repo.cancel(job.job_id)  # the owner cancels while the model is busy
            return MagicMock(success=True, ai_report=MagicMock())

        manager = MagicMock()
        manager.generate_ai_report.side_effect = generate
        executor = AIJobExecutor(max_workers=1, ai_manager=manager)
        try:
            assert executor.execute_job_sync(job.job_id, _report()) is False
        finally:
            executor._executor.shutdown(wait=True)

        assert repo.get_by_job_id(job.job_id).status == AIJobStatus.CANCELLED


def test_recovery_on_a_fresh_database_creates_the_schema(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "fresh.db")
    assert AIJobService().recover_stale_jobs() == 0


def test_every_connection_the_service_opens_is_closed(db, monkeypatch) -> None:
    opened, closed = [], []
    real_create = ConnectionFactory.create_connection

    def tracking():
        conn = real_create()
        real_connect, real_disconnect = conn.connect, conn.disconnect
        conn.connect = lambda: (opened.append(1), real_connect())[1]
        conn.disconnect = lambda: (closed.append(1), real_disconnect())[1]
        return conn

    monkeypatch.setattr(ConnectionFactory, "create_connection", staticmethod(tracking))
    service = AIJobService()
    job = service.create_and_dispatch_job(pipeline_run_id=1, reporting_report=_report(), max_attempts=2)
    service.get_job(job.job_id)
    service.get_job_with_report(job.job_id)
    service.get_latest_job_for_user(None)
    service.ensure_capacity(1)
    service.cancel_job(job.job_id)

    assert opened and len(opened) == len(closed)
