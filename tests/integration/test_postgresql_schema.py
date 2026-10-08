"""
B-06: schema initialization against a REAL PostgreSQL engine.

Reproduced on PostgreSQL 16 before the fix: on a fresh database
`initialize_schema()` raised `relation "users" does not exist` and left 0 of
11 tables, and every retry failed the same way. The column migrations tried
`ALTER TABLE ... ADD COLUMN` on columns that had just been created and
recovered with `rollback()` (discarding every CREATE TABLE before it, since
PostgreSQL DDL is transactional) or with a bare `pass` (leaving the
transaction aborted).

Requires a throwaway PostgreSQL. Deselected by default (`integration`) and
skipped unless TEST_POSTGRES_HOST / _PORT / _DB / _USER / _PASSWORD are set.
Every test works inside its own freshly created schema and drops only that
schema, so pointing this at a shared server cannot touch existing data.

    docker run -d --name agpt-pg -e POSTGRES_PASSWORD=... -p 127.0.0.1:55432:5432 postgres:16-alpine
    TEST_POSTGRES_HOST=127.0.0.1 TEST_POSTGRES_PORT=55432 ... pytest -m integration tests/integration/test_postgresql_schema.py
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

pytestmark = pytest.mark.integration

psycopg = pytest.importorskip("psycopg")

from src.database.postgresql_connection import PostgreSQLConnection  # noqa: E402
from src.database.schema_manager import SchemaManager  # noqa: E402

EXPECTED_TABLES = {
    "users",
    "pipeline_runs",
    "datasets",
    "quality_reports",
    "analytics_reports",
    "reports",
    "ai_jobs",
    "ai_reports",
    "dataset_versions",
    "cleaning_configs",
    "cleaning_executions",
    "revoked_tokens",
    "audit_events",
    "login_failures",
    "cleaning_policy_proposals",
    "schema_version",
}

_ENV = {key: os.getenv(f"TEST_POSTGRES_{key}") for key in ("HOST", "PORT", "DB", "USER", "PASSWORD")}

if not all(_ENV.values()):
    pytest.skip("TEST_POSTGRES_* not set; no throwaway PostgreSQL available", allow_module_level=True)


def _raw_connect():
    return psycopg.connect(
        host=_ENV["HOST"],
        port=int(_ENV["PORT"]),
        dbname=_ENV["DB"],
        user=_ENV["USER"],
        password=_ENV["PASSWORD"],
        autocommit=True,
    )


@pytest.fixture
def schema() -> Iterator[str]:
    name = f"agpt_it_{uuid.uuid4().hex[:10]}"
    with _raw_connect() as conn:
        conn.execute(f"CREATE SCHEMA {name}")
    yield name
    with _raw_connect() as conn:
        conn.execute(f"DROP SCHEMA IF EXISTS {name} CASCADE")


def _connection(schema: str) -> PostgreSQLConnection:
    conn = PostgreSQLConnection(
        host=_ENV["HOST"],
        port=int(_ENV["PORT"]),
        database=_ENV["DB"],
        user=_ENV["USER"],
        password=_ENV["PASSWORD"],
    )
    conn.connect()
    # Session-level (not SET LOCAL), committed so a later rollback keeps it.
    conn.get_connection().execute(f"SET search_path TO {schema}")
    conn.commit()
    return conn


def _tables(schema: str) -> set[str]:
    with _raw_connect() as conn:
        rows = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = %s", (schema,)).fetchall()
    return {r[0] for r in rows}


def _columns(schema: str, table: str) -> set[str]:
    with _raw_connect() as conn:
        rows = conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s",
            (schema, table),
        ).fetchall()
    return {r[0] for r in rows}


def test_fresh_database_gets_every_table(schema: str) -> None:
    conn = _connection(schema)
    try:
        SchemaManager(conn).initialize_schema()
    finally:
        conn.disconnect()

    assert _tables(schema) == EXPECTED_TABLES


def test_initialization_is_idempotent(schema: str) -> None:
    for _ in range(3):
        conn = _connection(schema)
        try:
            SchemaManager(conn).initialize_schema()
        finally:
            conn.disconnect()

    assert _tables(schema) == EXPECTED_TABLES


def test_failure_mid_initialization_rolls_back_completely_and_retry_recovers(schema: str) -> None:
    """Exercise the failure path: an error part-way through must leave no partial schema."""

    class FailingCursor:
        def __init__(self, inner, fail_on: str) -> None:
            self._inner = inner
            self._fail_on = fail_on

        def execute(self, query, *args, **kwargs):
            if self._fail_on in query:
                raise RuntimeError("injected failure during schema initialization")
            return self._inner.execute(query, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._inner, name)

    conn = _connection(schema)
    real = conn.get_connection()

    class FailingConnection:
        def cursor(self):
            return FailingCursor(real.cursor(), fail_on="idx_cleaning_executions_source")

        def __getattr__(self, name):
            return getattr(real, name)

    conn.get_connection = lambda: FailingConnection()  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="injected failure"):
            SchemaManager(conn).initialize_schema()
    finally:
        real.close()

    # Transactional DDL: nothing from the failed attempt survives.
    assert _tables(schema) == set()

    conn = _connection(schema)
    try:
        SchemaManager(conn).initialize_schema()
    finally:
        conn.disconnect()
    assert _tables(schema) == EXPECTED_TABLES


def test_legacy_tables_are_migrated(schema: str) -> None:
    """A pre-Sprint-13 database without user_id columns gets them added."""
    with _raw_connect() as raw:
        raw.execute(f"SET search_path TO {schema}")
        raw.execute("CREATE TABLE pipeline_runs (id SERIAL PRIMARY KEY, status TEXT NOT NULL)")
        raw.execute("CREATE TABLE datasets (id SERIAL PRIMARY KEY, pipeline_run_id INTEGER, dataset_name TEXT)")
    assert "user_id" not in _columns(schema, "pipeline_runs")

    conn = _connection(schema)
    try:
        SchemaManager(conn).initialize_schema()
    finally:
        conn.disconnect()

    assert "user_id" in _columns(schema, "pipeline_runs")
    assert "user_id" in _columns(schema, "datasets")
    assert EXPECTED_TABLES <= _tables(schema)
