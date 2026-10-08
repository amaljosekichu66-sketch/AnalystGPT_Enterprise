"""
P2-16 / P2-21: concurrency against a REAL PostgreSQL engine.

B-03 (concurrent pipeline isolation) was proven on SQLite only, and every
persistence session ran the full DDL, ALTER TABLE included, which takes
ACCESS EXCLUSIVE locks on PostgreSQL. These tests run the same overlap on
PostgreSQL 16:

- many processes' worth of simultaneous schema initialisation on a fresh
  database (the advisory lock serialises the one real migration);
- 2 users x 3 pipeline runs held together by a barrier, then every row's
  ownership checked.

Requires a throwaway PostgreSQL (see test_postgresql_schema.py). Each test
creates and drops its own database. CI runs these in the `postgres` job.
"""

from __future__ import annotations

import os
import threading
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

psycopg = pytest.importorskip("psycopg")

from src.application.app import Application  # noqa: E402
from src.core import config  # noqa: E402
from src.database.connection_factory import ConnectionFactory  # noqa: E402
from src.database.repositories.user_repository import UserRepository  # noqa: E402
from src.database.schema_manager import SCHEMA_VERSION, SchemaManager  # noqa: E402
from src.identity.context import UserContext  # noqa: E402
from src.identity.models import UserCreate, UserRole, UserStatus  # noqa: E402
from src.identity.user_service import UserService  # noqa: E402

_ENV = {key: os.getenv(f"TEST_POSTGRES_{key}") for key in ("HOST", "PORT", "DB", "USER", "PASSWORD")}

if not all(_ENV.values()):
    pytest.skip("TEST_POSTGRES_* not set; no throwaway PostgreSQL available", allow_module_level=True)

SAMPLE_CSV = Path("sample_data/customer_data.csv")
RUNS_PER_USER = 3


def _admin_connect(dbname: str):
    return psycopg.connect(
        host=_ENV["HOST"],
        port=int(_ENV["PORT"]),
        dbname=dbname,
        user=_ENV["USER"],
        password=_ENV["PASSWORD"],
        autocommit=True,
    )


@pytest.fixture
def pg_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """A fresh database the whole application points at for one test."""
    name = f"agpt_conc_{uuid.uuid4().hex[:10]}"
    with _admin_connect(_ENV["DB"]) as conn:
        conn.execute(f'CREATE DATABASE "{name}"')
    monkeypatch.setattr(config, "DATABASE_ENGINE", "postgresql")
    monkeypatch.setattr(config, "POSTGRES_HOST", _ENV["HOST"])
    monkeypatch.setattr(config, "POSTGRES_PORT", int(_ENV["PORT"]))
    monkeypatch.setattr(config, "POSTGRES_DATABASE", name)
    monkeypatch.setattr(config, "POSTGRES_USER", _ENV["USER"])
    monkeypatch.setattr(config, "POSTGRES_PASSWORD", _ENV["PASSWORD"])
    monkeypatch.setattr(config, "ARTIFACT_STORE_DIRECTORY", tmp_path / "artifacts")
    monkeypatch.setattr(config, "REPORT_OUTPUT_DIRECTORY", tmp_path / "reports")
    monkeypatch.setattr(config, "MAX_CONCURRENT_JOBS_PER_USER", RUNS_PER_USER)
    (tmp_path / "reports").mkdir()
    yield name
    with _admin_connect(_ENV["DB"]) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def _query(dbname: str, sql: str, params: tuple = ()) -> list[tuple]:
    with _admin_connect(dbname) as conn:
        return [tuple(r) for r in conn.execute(sql, params).fetchall()]


def test_simultaneous_schema_initialisation_on_a_fresh_database(pg_database: str) -> None:
    parties = 8
    barrier = threading.Barrier(parties, timeout=60)

    def initialise(_):
        conn = ConnectionFactory.create_connection()
        conn.connect()
        try:
            barrier.wait()
            SchemaManager(conn).initialize_schema()
            return SchemaManager(conn).current_version()
        finally:
            conn.disconnect()

    with ThreadPoolExecutor(max_workers=parties) as pool:
        versions = list(pool.map(initialise, range(parties)))

    assert versions == [SCHEMA_VERSION] * parties
    assert _query(pg_database, "SELECT COUNT(*) FROM schema_version") == [(1,)]


def _create_users(count: int) -> list[UserContext]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    contexts = []
    for i in range(count):
        name = f"pgconc_{i}_{uuid.uuid4().hex[:6]}"
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


def test_concurrent_pipeline_runs_are_isolated(pg_database: str, monkeypatch: pytest.MonkeyPatch) -> None:
    users = _create_users(2)
    application = Application()
    jobs = []
    for user in users:
        for _ in range(RUNS_PER_USER):
            version = application.register_upload(SAMPLE_CSV.read_bytes(), "customer_data.csv", user)
            jobs.append((user, version.version_id))

    barrier = threading.Barrier(len(jobs), timeout=120)
    original = Application._assess_quality

    def synchronized(self, dataframe):
        barrier.wait()
        return original(self, dataframe)

    monkeypatch.setattr(Application, "_assess_quality", synchronized)

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        results = list(pool.map(lambda job: application.run_dataset_version(job[1], user_context=job[0]), jobs))

    assert not barrier.broken
    assert all(r.success for r in results), [str(r.error) for r in results if not r.success]
    assert len({r.pipeline_run_id for r in results}) == len(jobs)

    for result, (user, _) in zip(results, jobs):
        run_id = result.pipeline_run_id
        assert _query(pg_database, "SELECT status, user_id FROM pipeline_runs WHERE id = %s", (run_id,)) == [
            ("SUCCESS", user.user_id)
        ]
        for table in ("datasets", "reports", "ai_jobs", "cleaning_executions"):
            owners = {
                r[0] for r in _query(pg_database, f"SELECT user_id FROM {table} WHERE pipeline_run_id = %s", (run_id,))
            }
            assert owners == {user.user_id}, (table, run_id, owners)
    assert _query(pg_database, "SELECT COUNT(*) FROM pipeline_runs WHERE user_id IS NULL") == [(0,)]
