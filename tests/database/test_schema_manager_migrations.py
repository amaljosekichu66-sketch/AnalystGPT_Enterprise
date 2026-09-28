"""
Default-suite guards for B-06 (schema initialization transaction handling).

The real-engine proof lives in tests/integration/test_postgresql_schema.py
(requires a throwaway PostgreSQL). These tests run everywhere and pin the
properties that made PostgreSQL initialization fail:

- no statement is EXPECTED to fail (a failed statement aborts a PostgreSQL
  transaction, and the old recovery rolled back every CREATE TABLE);
- the whole schema is one transaction: exactly one commit, no rollback on
  the success path;
- column migrations still work on legacy SQLite databases.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection


class _RecordingPostgresConnection:
    """Accepts every statement and records what SchemaManager asks of it."""

    def __init__(self) -> None:
        self.statements: list[str] = []
        self.commits = 0
        self.rollbacks = 0

    # DatabaseConnection surface used by SchemaManager
    def database_type(self) -> str:
        return "postgresql"

    def get_connection(self):
        return self

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    # psycopg-like cursor surface
    def cursor(self):
        return self

    def execute(self, query, *args, **kwargs):
        self.statements.append(" ".join(query.split()))

    def fetchall(self):
        raise AssertionError("PostgreSQL path must not need introspection round-trips")

    def close(self) -> None:
        pass


def test_postgresql_schema_is_one_transaction_with_no_expected_failures() -> None:
    conn = _RecordingPostgresConnection()

    SchemaManager(conn).initialize_schema()

    assert conn.commits == 1
    assert conn.rollbacks == 0
    alters = [s for s in conn.statements if s.upper().startswith("ALTER TABLE")]
    assert alters, "expected column migrations"
    assert all("ADD COLUMN IF NOT EXISTS" in s for s in alters), alters


def test_sqlite_fresh_schema_initializes_twice(tmp_path: Path) -> None:
    for _ in range(2):
        conn = SQLiteConnection(str(tmp_path / "fresh.db"))
        conn.connect()
        SchemaManager(conn).initialize_schema()
        conn.disconnect()

    db = sqlite3.connect(tmp_path / "fresh.db")
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    db.close()
    assert {"users", "pipeline_runs", "datasets", "reports", "ai_reports", "dataset_versions"} <= tables


def test_sqlite_legacy_tables_get_missing_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE pipeline_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT NOT NULL)")
    db.execute(
        "CREATE TABLE ai_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, pipeline_run_id INTEGER, "
        "user_id INTEGER, report_id INTEGER)"
    )
    db.commit()
    db.close()

    conn = SQLiteConnection(str(db_path))
    conn.connect()
    SchemaManager(conn).initialize_schema()
    conn.disconnect()

    db = sqlite3.connect(db_path)
    runs_cols = {r[1] for r in db.execute("PRAGMA table_info(pipeline_runs)")}
    ai_cols = {r[1] for r in db.execute("PRAGMA table_info(ai_reports)")}
    db.close()
    assert "user_id" in runs_cols
    assert {"source_version_id", "cleaned_version_id", "structured_payload", "confidence"} <= ai_cols
