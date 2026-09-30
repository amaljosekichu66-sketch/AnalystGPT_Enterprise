"""
Regression tests for L16, L18, I6, I7 and I14 (audit 2026-09-29).

- L16: every report was mirrored to one shared analystgpt_report.txt, and
  frontend exports were written to shared filenames that were never deleted.
- L18: when the REST export failed - a 403 included - the frontend exported
  in-process, skipping the API's permission checks.
- I6: a stored report_path was served without a containment check.
- I7: no way to delete one dataset, no retention, orphaned files when the
  database write failed.
- I14: SQLite foreign keys were enforced only on the schema connection, and
  purge IN lists could exceed SQLite's bound-variable limit.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import get_application
from src.api.server import app
from src.application.reporting_orchestrator import _contained_report_file
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from tests.fixtures.datasets import upload_dataset

REPO = Path(__file__).resolve().parents[2]
SAMPLE_CSV = REPO / "sample_data" / "customer_data.csv"
_PASSWORD = "Password123!"


@pytest.fixture(scope="module")
def tokens() -> dict[str, dict[str, str]]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    out = {}
    for key in ("owner", "other"):
        name = f"i7_{key}_{uuid.uuid4().hex[:6]}"
        service.register_user(
            UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=UserRole.ANALYST)
        )
        _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
        out[key] = {"Authorization": f"Bearer {token}"}
    return out


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


def _stored_path(version_id: str) -> Path | None:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    try:
        row = (
            conn.get_connection()
            .execute("SELECT storage_path FROM dataset_versions WHERE version_id = ?", (version_id,))
            .fetchone()
        )
        return None if row is None else Path(row[0])
    finally:
        conn.disconnect()


class TestDatasetDelete:
    def test_owner_deletes_rows_and_file(self, client: TestClient, tokens) -> None:
        dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["owner"])
        stored = _stored_path(dataset_id)
        assert stored is not None and stored.exists()

        res = client.delete(f"/api/datasets/{dataset_id}", headers=tokens["owner"])

        assert res.status_code == 200
        assert _stored_path(dataset_id) is None
        assert not stored.exists()
        run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=tokens["owner"])
        assert run.status_code == 404

    def test_other_users_cannot_delete(self, client: TestClient, tokens) -> None:
        dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["owner"])
        assert client.delete(f"/api/datasets/{dataset_id}", headers=tokens["other"]).status_code == 404
        assert _stored_path(dataset_id) is not None

    def test_failed_registration_leaves_no_file(self, client: TestClient, tokens, monkeypatch) -> None:
        from src.database.repositories.dataset_version_repository import DatasetVersionRepository

        raw_dir = get_application().artifact_store.raw_dir
        before = {p for p in raw_dir.rglob("*") if p.is_file()}
        monkeypatch.setattr(DatasetVersionRepository, "create", MagicMock(side_effect=RuntimeError("db down")))

        res = TestClient(app, raise_server_exceptions=False).post(
            "/api/datasets", headers=tokens["owner"], files={"file": ("a.csv", b"a,b\n1,2\n", "text/csv")}
        )

        assert res.status_code == 500
        assert {p for p in raw_dir.rglob("*") if p.is_file()} == before

    def test_retention_deletes_old_uploads(self, client: TestClient, tokens, monkeypatch) -> None:
        dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["owner"])
        conn = ConnectionFactory.create_connection()
        conn.connect()
        conn.get_connection().execute(
            "UPDATE dataset_versions SET created_at = '2000-01-01T00:00:00+00:00' WHERE version_id = ?", (dataset_id,)
        )
        conn.commit()
        conn.disconnect()
        monkeypatch.setattr(config, "DATASET_RETENTION_DAYS", 30)

        get_application()._apply_dataset_retention()

        assert _stored_path(dataset_id) is None


class TestContainedReportPath:
    def test_path_outside_the_report_directory_is_refused(self, tmp_path: Path) -> None:
        outside = tmp_path / "secret.txt"
        outside.write_text("x", encoding="utf-8")
        assert _contained_report_file(str(outside)) is None

    def test_path_inside_is_served(self) -> None:
        inside = Path(config.REPORT_OUTPUT_DIRECTORY) / f"contained_{uuid.uuid4().hex}.txt"
        inside.parent.mkdir(parents=True, exist_ok=True)
        inside.write_text("x", encoding="utf-8")
        try:
            assert _contained_report_file(str(inside)) == inside.resolve()
        finally:
            inside.unlink()

    def test_directory_and_missing_paths_are_refused(self) -> None:
        assert _contained_report_file(str(config.REPORT_OUTPUT_DIRECTORY)) is None
        assert _contained_report_file(None) is None


class TestFrontendExports:
    def test_api_refusal_is_not_worked_around(self) -> None:
        from src.frontend.services import report_service

        client = MagicMock()
        client.__enter__.return_value.export_pdf_report.side_effect = RuntimeError("Backend returned HTTP 403: no")
        with (
            patch.object(report_service, "APIClient", return_value=client),
            patch("src.application.app.Application", side_effect=AssertionError("in-process export")),
        ):
            result = report_service.export_pdf_report()

        assert result["success"] is False
        assert "cannot export" in result["message"]

    def test_no_shared_latest_report_copy(self) -> None:
        source = (REPO / "src" / "reporting" / "reporting_manager.py").read_text(encoding="utf-8")
        assert "_mirror_as_latest" not in source


class TestForeignKeys:
    def test_every_sqlite_connection_enforces_them(self, tmp_path: Path) -> None:
        conn = SQLiteConnection(str(tmp_path / "fk.db"))
        conn.connect()
        assert conn.get_connection().execute("PRAGMA foreign_keys;").fetchone()[0] == 1
        conn.disconnect()

    def test_purge_handles_more_runs_than_sqlite_variables(self, monkeypatch) -> None:
        from src.persistence import user_data_purge

        executed: list[int] = []

        class Cursor:
            rowcount = 0

            def execute(self, query, params=()):
                executed.append(len(params))
                if "SELECT username" in query:
                    self._rows = [("big",)]
                elif "SELECT id FROM pipeline_runs" in query:
                    self._rows = [(i,) for i in range(1200)]
                else:
                    self._rows = []

            def fetchone(self):
                return self._rows[0] if self._rows else None

            def fetchall(self):
                return self._rows

            def close(self):
                pass

        conn = MagicMock()
        conn.database_type.return_value = "sqlite"
        conn.get_connection.return_value.cursor.return_value = Cursor()
        monkeypatch.setattr(user_data_purge.ConnectionFactory, "create_connection", lambda: conn)
        monkeypatch.setattr(user_data_purge.SchemaManager, "initialize_schema", lambda self: None)

        user_data_purge.UserDataPurger(MagicMock()).purge(1, "big")

        assert max(executed) <= user_data_purge._IN_CHUNK
