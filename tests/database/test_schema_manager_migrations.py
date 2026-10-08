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

    def fetchone(self):
        return None  # an empty database: no schema_version, no columns yet

    def close(self) -> None:
        pass


def test_postgresql_schema_is_one_transaction_with_no_expected_failures() -> None:
    conn = _RecordingPostgresConnection()

    SchemaManager(conn).initialize_schema()

    # One commit closes the version read (P2-16), one commits the whole schema.
    assert conn.commits == 2
    assert conn.rollbacks == 0
    assert any("pg_advisory_xact_lock" in s for s in conn.statements)
    assert any(s.startswith("INSERT INTO schema_version") for s in conn.statements)
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


def test_a_current_database_runs_no_ddl(tmp_path: Path) -> None:
    """P2-16: once migrated, initialisation is one read, with no DDL at all."""
    path = str(tmp_path / "versioned.db")
    conn = SQLiteConnection(path)
    conn.connect()
    SchemaManager(conn).initialize_schema()
    conn.disconnect()

    statements: list[str] = []
    conn = SQLiteConnection(path)
    conn.connect()
    conn.get_connection().set_trace_callback(statements.append)
    manager = SchemaManager(conn)
    manager.initialize_schema()
    conn.disconnect()

    ddl = [s for s in statements if s.split()[0].upper() in {"CREATE", "ALTER", "DROP", "PRAGMA"}]
    assert ddl == []


def test_version_is_recorded_and_force_reruns(tmp_path: Path) -> None:
    from src.database.schema_manager import SCHEMA_VERSION

    conn = SQLiteConnection(str(tmp_path / "v.db"))
    conn.connect()
    manager = SchemaManager(conn)
    assert manager.current_version() is None
    manager.initialize_schema()
    assert manager.current_version() == SCHEMA_VERSION
    manager.initialize_schema(force=True)
    assert manager.current_version() == SCHEMA_VERSION
    conn.disconnect()


def test_schema_version_is_bumped_with_the_ddl() -> None:
    """
    P2-16: a current database skips the DDL, so a DDL change that keeps
    SCHEMA_VERSION would never reach existing databases. Changed the DDL?
    Bump SCHEMA_VERSION and record the new fingerprint here.
    """
    import hashlib
    import inspect

    from src.database.schema_manager import SCHEMA_VERSION

    methods = (
        SchemaManager._create_schema,
        SchemaManager._ensure_case_insensitive_user_uniqueness,
        SchemaManager._add_column_if_missing,
    )
    fingerprint = hashlib.sha256("".join(inspect.getsource(m) for m in methods).encode()).hexdigest()[:16]
    assert (SCHEMA_VERSION, fingerprint) == (15, "5311cc7334a43a47")
