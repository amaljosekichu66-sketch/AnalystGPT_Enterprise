"""
Regression tests for L12 and I16 (audit 2026-09-29).

- L12: interrupted jobs were reset to PENDING and never ran again, every
  start reset ALL GENERATING jobs (other workers' too), transitions were
  unconditional, and a manual retry without a report stayed PENDING forever.
- I16: two routes fell back to an unscoped query when there was no user.
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.ai.job_executor import AIJobExecutor
from src.ai.models import AIJobStatus
from src.api.routes import ai as ai_routes
from src.api.routes import reports as report_routes
from src.core import config
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.identity.context import UserContext
from src.identity.exceptions import AuthenticationError


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "lease.db"
    monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", db_file)
    conn = SQLiteConnection(str(db_file))
    conn.connect()
    SchemaManager(conn).initialize_schema()
    conn.get_connection().execute("PRAGMA foreign_keys = OFF;")
    yield AIJobRepository(conn), conn
    conn.disconnect()


def _lease(conn, job_id: str) -> float | None:
    row = conn.get_connection().execute("SELECT lease_expires_at FROM ai_jobs WHERE job_id = ?", (job_id,)).fetchone()
    return None if row is None else row[0]


def test_new_jobs_get_a_pending_lease(repo) -> None:
    job_repo, conn = repo
    job_repo.create_job(job_id="j1", pipeline_run_id=1, user_id=1)
    lease = _lease(conn, "j1")
    assert lease is not None and lease > time.time() + config.AI_JOB_PENDING_TTL_SECONDS - 60


def test_claiming_sets_a_running_lease(repo) -> None:
    job_repo, conn = repo
    job_repo.create_job(job_id="j1", pipeline_run_id=1, user_id=1)
    job_repo.claim_next_pending_job()
    expected = time.time() + float(config.AI_TIMEOUT) + config.AI_JOB_LEASE_MARGIN_SECONDS
    assert abs(_lease(conn, "j1") - expected) < 30


def test_finishing_clears_the_lease(repo) -> None:
    job_repo, conn = repo
    job_repo.create_job(job_id="j1", pipeline_run_id=1, user_id=1)
    job_repo.claim_next_pending_job()
    job_repo.mark_ready("j1")
    assert _lease(conn, "j1") is None


def test_quota_check_sweeps_interrupted_jobs(repo, monkeypatch) -> None:
    from src.ai.ai_job_service import AIJobService

    job_repo, conn = repo
    for index in range(2):
        job_repo.create_job(job_id=f"stuck{index}", pipeline_run_id=index + 1, user_id=7)
    conn.get_connection().execute("UPDATE ai_jobs SET lease_expires_at = 1;")
    conn.commit()
    monkeypatch.setattr(config, "MAX_ACTIVE_AI_JOBS_PER_USER", 2)

    AIJobService(job_executor=None, connection=conn).ensure_capacity(7)

    assert job_repo.count_active_for_user(7) == 0


def test_queue_overflow_fails_the_job_instead_of_stranding_it(repo, monkeypatch) -> None:
    job_repo, _ = repo
    job_repo.create_job(job_id="overflow", pipeline_run_id=1, user_id=1)
    monkeypatch.setattr(config, "AI_MAX_QUEUED_JOBS", 1)
    executor = AIJobExecutor(max_workers=1, ai_manager=MagicMock())
    executor._queue_slots.acquire()  # the only slot is taken

    executor.submit_job("overflow", MagicMock())
    executor._executor.shutdown(wait=True)

    job = job_repo.get_by_job_id("overflow")
    assert job.status == AIJobStatus.FAILED


class TestNoUnscopedFallback:
    def test_latest_ai_job_requires_a_user(self) -> None:
        application = MagicMock()
        with pytest.raises(AuthenticationError):
            ai_routes.get_latest_ai_job(context=UserContext.anonymous(), application=application)
        application.ai_job_service.get_latest_job_for_user.assert_not_called()

    def test_reports_require_a_user(self) -> None:
        with pytest.raises(AuthenticationError):
            report_routes.get_reports(context=UserContext.anonymous(), application=MagicMock())
