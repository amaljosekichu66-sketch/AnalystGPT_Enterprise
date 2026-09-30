"""
Regression tests for M6, M7, L10 and I9 (audit 2026-09-29).

- M6: the governance preview (VIEWER-accessible) parsed and cleaned the whole
  dataset outside the per-user job slot, so parallel calls bypassed the cap.
- M7: no quota on AI jobs; the worker pool's queue was unbounded, and
  /api/pipeline and the retry route had no rate limit.
- L10: result caches grew by one PipelineResult per run, never evicted.
- I9: a user purge dropped only the latest cached report entry.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.ai.job_executor import AIJobExecutor
from src.api import rate_limit
from src.api.dependencies.application_dependency import get_application
from src.api.server import app
from src.core import config
from src.core.bounded_cache import BoundedTTLCache
from src.core.exceptions import TooManyConcurrentJobsError
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection

ANALYST = {"X-User-Id": "5151", "X-User-Name": "quota_analyst", "X-User-Role": "ANALYST"}
VERSION_ID = "0b7c1f2e-3d4a-4b5c-8d9e-0f1a2b3c4d5e"
VIEWER = {"X-User-Id": "5152", "X-User-Name": "quota_viewer", "X-User-Role": "VIEWER"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", True)
    return TestClient(app)


def test_governance_preview_holds_a_job_slot(client: TestClient, monkeypatch) -> None:
    application = get_application()
    monkeypatch.setattr(type(application), "resolve_source_version", lambda *a, **k: MagicMock())

    def refuse(_self, _context):
        raise TooManyConcurrentJobsError("busy")

    monkeypatch.setattr(type(application), "job_slot", refuse)
    monkeypatch.setattr(type(application), "load_source_dataframe", MagicMock(side_effect=AssertionError("parsed")))

    res = client.post(
        "/api/governance/preview",
        headers=VIEWER,
        json={"dataset_version_id": "v1", "cleaning_config": {"missing_value_policy": "drop_rows"}},
    )

    assert res.status_code == 429


class TestAIJobQuota:
    def test_pipeline_is_refused_while_the_ai_queue_is_full(self, client: TestClient, monkeypatch) -> None:
        application = get_application()
        monkeypatch.setattr(type(application), "resolve_source_version", lambda *a, **k: MagicMock())
        monkeypatch.setattr(config, "MAX_ACTIVE_AI_JOBS_PER_USER", 2)
        monkeypatch.setattr(AIJobRepository, "count_active_for_user", lambda self, user_id: 2)
        monkeypatch.setattr(type(application), "_execute", MagicMock(side_effect=AssertionError("pipeline ran")))

        res = client.post("/api/pipeline", headers=ANALYST, json={"dataset_version_id": VERSION_ID})

        assert res.status_code == 429

    def test_manual_retry_respects_the_quota(self, monkeypatch) -> None:
        service = get_application().ai_job_service
        job = MagicMock(status=MagicMock(), user_id=5151)
        from src.ai.models import AIJobStatus

        job.status = AIJobStatus.FAILED
        monkeypatch.setattr(AIJobRepository, "get_by_job_id", lambda self, job_id, user_id=None: job)
        monkeypatch.setattr(config, "MAX_ACTIVE_AI_JOBS_PER_USER", 2)
        monkeypatch.setattr(AIJobRepository, "count_active_for_user", lambda self, user_id: 5)
        schedule = MagicMock()
        monkeypatch.setattr(AIJobRepository, "schedule_retry", schedule)

        with pytest.raises(TooManyConcurrentJobsError):
            service.retry_job("job-1", user_id=5151)
        schedule.assert_not_called()

    def test_default_quota_is_small(self) -> None:
        import os

        # The suite raises it (tests/conftest.py); the shipped default is 2.
        assert os.environ.get("MAX_ACTIVE_AI_JOBS_PER_USER") == "1000"
        assert 'MAX_ACTIVE_AI_JOBS_PER_USER", "2")' in (
            Path(__file__).resolve().parents[2] / "src" / "core" / "config.py"
        ).read_text(encoding="utf-8")

    def test_active_jobs_are_counted_per_user(self, tmp_path: Path) -> None:
        conn = SQLiteConnection(str(tmp_path / "jobs.db"))
        conn.connect()
        SchemaManager(conn).initialize_schema()
        # Jobs reference pipeline runs; this test only counts statuses.
        conn.get_connection().execute("PRAGMA foreign_keys = OFF;")
        repo = AIJobRepository(conn)
        for index, user_id in enumerate((1, 1, 2)):
            repo.create_job(
                job_id=f"job-{index}",
                pipeline_run_id=index + 1,
                user_id=user_id,
                report_id=None,
                provider="ollama",
                model="m",
                max_attempts=1,
            )

        assert repo.count_active_for_user(1) == 2
        assert repo.count_active_for_user(2) == 1
        assert repo.count_active_for_user(3) == 0
        conn.disconnect()


def test_executor_queue_is_bounded(monkeypatch) -> None:
    monkeypatch.setattr(config, "AI_MAX_QUEUED_JOBS", 1)
    executor = AIJobExecutor(max_workers=1, ai_manager=MagicMock())
    release = threading.Event()
    started: list[str] = []

    def block(job_id, _report):
        started.append(job_id)
        release.wait(5)

    monkeypatch.setattr(executor, "execute_job_sync", block)
    try:
        executor.submit_job("first", MagicMock())
        executor.submit_job("second", MagicMock())
        time.sleep(0.2)
        release.set()
        executor._executor.shutdown(wait=True)
    finally:
        release.set()

    assert started == ["first"]


class TestRateLimits:
    @pytest.fixture(autouse=True)
    def enabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(config, "AUTH_RATE_LIMIT_ENABLED", True)
        rate_limit.limiter.reset()
        yield
        rate_limit.limiter.reset()

    def test_pipeline_is_rate_limited(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(config, "PIPELINE_RATE_LIMIT", "1/60")
        client.post("/api/pipeline", headers=ANALYST, json={"dataset_version_id": VERSION_ID})
        assert client.post("/api/pipeline", headers=ANALYST, json={"dataset_version_id": VERSION_ID}).status_code == 429

    def test_ai_retry_is_rate_limited(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(config, "AI_RETRY_RATE_LIMIT", "1/60")
        client.post("/api/ai/jobs/nope/retry", headers=ANALYST)
        assert client.post("/api/ai/jobs/nope/retry", headers=ANALYST).status_code == 429


class TestBoundedTTLCache:
    def test_oldest_entry_is_evicted(self) -> None:
        cache: BoundedTTLCache[str, int] = BoundedTTLCache(max_entries=2, ttl_seconds=60)
        cache["a"], cache["b"], cache["c"] = 1, 2, 3
        assert list(cache) == ["b", "c"]

    def test_rewrite_refreshes_recency(self) -> None:
        cache: BoundedTTLCache[str, int] = BoundedTTLCache(max_entries=2, ttl_seconds=60)
        cache["a"], cache["b"] = 1, 2
        cache["a"] = 10
        cache["c"] = 3
        assert list(cache) == ["a", "c"]

    def test_entries_expire(self) -> None:
        now = [0.0]
        cache: BoundedTTLCache[str, int] = BoundedTTLCache(max_entries=10, ttl_seconds=5, clock=lambda: now[0])
        cache["a"] = 1
        now[0] = 6.0
        assert cache.get("a") is None and len(cache) == 0

    def test_application_caches_are_bounded(self) -> None:
        application = get_application()
        assert isinstance(application._report_pipeline_results, BoundedTTLCache)
        assert isinstance(application._dataset_results, BoundedTTLCache)


def test_purge_drops_every_cached_report_of_the_user(monkeypatch) -> None:
    from src.persistence import user_data_purge

    monkeypatch.setattr(user_data_purge.UserDataPurger, "purge", lambda self, user_id, expected_username=None: {})
    application = get_application()
    older, latest, other = MagicMock(), MagicMock(), MagicMock()
    application.set_result_for_user(9001, older, report_id=90011)
    application.set_result_for_user(9001, latest, report_id=90012)
    application.set_result_for_user(9002, other, report_id=90021)

    application.purge_user_data(9001, "gone")

    assert application.get_result_by_report_id(90011) is None
    assert application.get_result_by_report_id(90012) is None
    assert application.get_result_by_report_id(90021) is other
