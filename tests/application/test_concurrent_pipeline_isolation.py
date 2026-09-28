"""
Regression tests for B-03 / SEC-06: concurrent pipeline execution.

The Application singleton held ONE PersistenceManager for every request. Each
run's `initialize()` replaced its connection and repositories, `shutdown()`
closed them, and the per-run ids (`_pipeline_run_id`, `_user_id`,
`_report_id`) were plain attributes. Two simultaneous runs therefore wrote
under each other's run and user ids and closed each other's SQLite
connection. Reproduced against a real uvicorn process: FK and UNIQUE
violations, "cannot commit - no transaction is active", and the API process
dying with 0xC0000005.

Determinism: a `threading.Barrier` inside the quality stage holds every run
until ALL of them have created their pipeline run and persisted their
dataset/governance rows, so the overlap is guaranteed rather than left to
scheduling luck. If runs were serialized the barrier would time out and the
test would fail loudly instead of passing vacuously.
"""

from __future__ import annotations

import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.application.app import Application
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.context import UserContext
from src.identity.models import UserCreate, UserLogin, UserRole, UserStatus
from src.identity.user_service import UserService

SAMPLE_CSV = Path("sample_data/customer_data.csv")
RUNS_PER_USER = 3
BARRIER_TIMEOUT_SECONDS = 120


@pytest.fixture
def throwaway_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fresh SQLite file and artifact store used only by this test."""
    db_path = tmp_path / "concurrency.db"
    monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", db_path)
    monkeypatch.setattr(config, "ARTIFACT_STORE_DIRECTORY", tmp_path / "artifacts")
    monkeypatch.setattr(config, "REPORT_OUTPUT_DIRECTORY", tmp_path / "reports")
    (tmp_path / "reports").mkdir()
    return db_path


def _create_users(count: int = 2) -> list[UserContext]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    repo = UserRepository(conn)
    service = UserService(user_repository=repo)
    contexts = []
    for i in range(count):
        name = f"conc_{i}_{uuid.uuid4().hex[:6]}"
        user = service.register_user(
            UserCreate(username=name, email=f"{name}@example.com", password="Password123!", role=UserRole.ANALYST)
        )
        contexts.append(
            UserContext(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=UserRole.ANALYST,
                status=UserStatus.ACTIVE,
                is_authenticated=True,
            )
        )
    conn.disconnect()
    return contexts


def _force_overlap(monkeypatch: pytest.MonkeyPatch, parties: int) -> threading.Barrier:
    barrier = threading.Barrier(parties, timeout=BARRIER_TIMEOUT_SECONDS)
    original = Application._assess_quality

    def synchronized(self, dataframe):
        barrier.wait()
        return original(self, dataframe)

    monkeypatch.setattr(Application, "_assess_quality", synchronized)
    return barrier


def _assert_database_consistent(db_path: Path, expected: dict[int, int]) -> None:
    """`expected` maps pipeline_run_id -> the user id that requested it."""
    db = sqlite3.connect(db_path)
    try:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        db.execute("PRAGMA foreign_keys = ON")
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

        for run_id, user_id in expected.items():
            status, owner = db.execute("SELECT status, user_id FROM pipeline_runs WHERE id = ?", (run_id,)).fetchone()
            assert status == "SUCCESS"
            assert owner == user_id, f"run {run_id} owned by {owner}, requested by {user_id}"

            for table in ("datasets", "reports"):
                owners = {r[0] for r in db.execute(f"SELECT user_id FROM {table} WHERE pipeline_run_id = ?", (run_id,))}
                assert owners == {user_id}, f"{table} for run {run_id}: owners {owners}, expected {user_id}"

            jobs = db.execute("SELECT user_id FROM ai_jobs WHERE pipeline_run_id = ?", (run_id,)).fetchall()
            assert len(jobs) == 1 and jobs[0][0] == user_id

            execution = db.execute(
                "SELECT source_version_id, cleaned_version_id FROM cleaning_executions WHERE pipeline_run_id = ?",
                (run_id,),
            ).fetchall()
            assert len(execution) == 1
            for version_id in execution[0]:
                (version_owner,) = db.execute(
                    "SELECT user_id FROM dataset_versions WHERE version_id = ?", (version_id,)
                ).fetchone()
                assert version_owner == user_id

        assert db.execute("SELECT COUNT(*) FROM pipeline_runs WHERE user_id IS NULL").fetchone()[0] == 0
    finally:
        db.close()


def test_concurrent_runs_are_isolated_in_process(throwaway_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    users = _create_users(2)
    application = Application()
    jobs = []
    for user in users:
        for _ in range(RUNS_PER_USER):
            version = application.register_upload(SAMPLE_CSV.read_bytes(), "customer_data.csv", user)
            jobs.append((user, version.version_id))

    barrier = _force_overlap(monkeypatch, len(jobs))

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        results = list(pool.map(lambda job: application.run_dataset_version(job[1], user_context=job[0]), jobs))

    assert not barrier.broken
    assert all(r.success for r in results), [str(r.error) for r in results if not r.success]
    run_ids = [r.pipeline_run_id for r in results]
    assert len(set(run_ids)) == len(jobs)
    assert [r.dataset_version_id for r in results] == [dataset_id for _, dataset_id in jobs]
    _assert_database_consistent(throwaway_db, {r.pipeline_run_id: user.user_id for r, (user, _) in zip(results, jobs)})

    # The cached, read-only view of each result belongs to its requester only.
    for (user, dataset_id), result in zip(jobs, results):
        assert application.get_result_for_dataset(dataset_id, user) is result


def test_concurrent_http_requests_are_isolated(throwaway_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Same property through the real routes: 2 users, simultaneous POST /api/pipeline."""
    from src.api.dependencies import application_dependency
    from src.api.dependencies.auth_dependencies import set_user_service_instance
    from src.api.server import app

    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    application = Application()
    monkeypatch.setattr(application_dependency, "_application", application)

    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    set_user_service_instance(service)
    try:
        headers = {}
        user_ids = {}
        for key in ("alice", "bob"):
            name = f"conc_http_{key}_{uuid.uuid4().hex[:6]}"
            user = service.register_user(
                UserCreate(username=name, email=f"{name}@example.com", password="Password123!", role=UserRole.ANALYST)
            )
            _, token, _ = service.login(UserLogin(username=name, password="Password123!"))
            headers[key] = {"Authorization": f"Bearer {token}"}
            user_ids[key] = user.id

        client = TestClient(app)
        jobs = []
        for key in headers:
            for _ in range(RUNS_PER_USER):
                upload = client.post(
                    "/api/datasets",
                    files={"file": ("customer_data.csv", SAMPLE_CSV.read_bytes())},
                    headers=headers[key],
                )
                assert upload.status_code == 201, upload.text
                jobs.append((key, upload.json()["dataset_version_id"]))

        barrier = _force_overlap(monkeypatch, len(jobs))

        def fire(job):
            key, dataset_id = job
            # No `with`: entering a TestClient runs lifespan shutdown on exit,
            # which would stop the shared AI executor under the other threads.
            return TestClient(app).post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=headers[key])

        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            responses = list(pool.map(fire, jobs))
    finally:
        set_user_service_instance(None)
        conn.disconnect()

    assert not barrier.broken
    assert [r.status_code for r in responses] == [200] * len(jobs)
    assert all(r.json()["success"] is True for r in responses), [r.json().get("error") for r in responses]

    db = sqlite3.connect(throwaway_db)
    try:
        expected = {}
        for (key, dataset_id), response in zip(jobs, responses):
            assert response.json()["dataset_version_id"] == dataset_id
            (run_id,) = db.execute(
                "SELECT pipeline_run_id FROM cleaning_executions WHERE source_version_id = ?", (dataset_id,)
            ).fetchone()
            expected[run_id] = user_ids[key]
    finally:
        db.close()
    assert len(expected) == len(jobs)
    _assert_database_consistent(throwaway_db, expected)
