"""
Regression tests for P2-14 (Sprint 15 readiness gate).

- The purge committed on its own connection before the user row was deleted
  on another: a failure in between left an account whose data was gone.
- Ownerless rows could never be purged.
- Audit rows and logs kept a deleted user's identity; audit writes were not
  tamper-evident and had no retention.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.audit_store import DatabaseAuditSink
from src.identity.models import AuditEvent, AuditEventType, UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from src.persistence import user_data_purge
from tests.fixtures.datasets import upload_dataset

SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "customer_data.csv"
_PASSWORD = "Password123!"


def _rows(query: str, params: tuple = ()) -> list:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    try:
        return [tuple(r) for r in conn.get_connection().execute(query, params).fetchall()]
    finally:
        conn.disconnect()


@pytest.fixture
def people():
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    out = {}
    for key, role in (("admin", UserRole.ADMIN), ("victim", UserRole.ANALYST)):
        name = f"p214_{key}_{uuid.uuid4().hex[:6]}"
        user = service.register_user(
            UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=role)
        )
        _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
        out[key] = {"id": user.id, "name": name, "headers": {"Authorization": f"Bearer {token}"}}
    return out


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app, raise_server_exceptions=False)


def test_account_and_data_are_deleted_together(client: TestClient, people) -> None:
    victim = people["victim"]
    upload_dataset(client, SAMPLE, victim["headers"])

    res = client.delete(f"/api/admin/users/{victim['id']}", headers=people["admin"]["headers"])

    assert res.status_code == 200
    assert _rows("SELECT id FROM users WHERE id = ?", (victim["id"],)) == []
    assert _rows("SELECT id FROM dataset_versions WHERE user_id = ?", (victim["id"],)) == []


def test_a_failure_part_way_leaves_both_account_and_data(client: TestClient, people, monkeypatch) -> None:
    victim = people["victim"]
    upload_dataset(client, SAMPLE, victim["headers"])

    def explode(*_a, **_k):
        raise RuntimeError("disk full")  # after the data deletes, before commit

    monkeypatch.setattr(user_data_purge.UserDataPurger, "_pseudonymise_audit", staticmethod(explode))

    res = client.delete(f"/api/admin/users/{victim['id']}", headers=people["admin"]["headers"])

    assert res.status_code == 500
    assert _rows("SELECT id FROM users WHERE id = ?", (victim["id"],)) != []
    assert _rows("SELECT id FROM dataset_versions WHERE user_id = ?", (victim["id"],)) != []


def test_deleted_users_audit_rows_are_pseudonymised(client: TestClient, people) -> None:
    victim = people["victim"]
    client.post("/api/auth/login", json={"username": victim["name"], "password": "Wr0ng-Passw0rd!"})

    client.delete(f"/api/admin/users/{victim['id']}", headers=people["admin"]["headers"])

    rows = _rows(
        "SELECT actor_username, details_json FROM audit_events WHERE actor_id = ? OR target_id = ?",
        (victim["id"], victim["id"]),
    )
    assert rows
    for actor_username, details_json in rows:
        assert victim["name"] not in (actor_username or "")
        assert victim["name"] not in (details_json or "") and "@example.com" not in (details_json or "")


class TestAuditChain:
    def _event(self, kind=AuditEventType.LOGIN_FAILURE, actor_id=None) -> AuditEvent:
        from datetime import UTC, datetime

        return AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=kind,
            timestamp=datetime.now(UTC),
            actor_id=actor_id,
            actor_username="someone",
            action="TEST",
            outcome="SUCCESS",
            details={"email": "someone@example.com"},
        )

    def test_chain_verifies_and_detects_tampering(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "audit.db")
        sink = DatabaseAuditSink()
        for _ in range(5):
            sink.write(self._event())
        assert sink.verify_chain() == {"checked": 5, "valid": True, "first_broken_id": None}

        conn = ConnectionFactory.create_connection()
        conn.connect()
        conn.get_connection().execute("UPDATE audit_events SET outcome = 'DENIED' WHERE id = 3;")
        conn.commit()
        conn.disconnect()

        result = sink.verify_chain()
        assert result["valid"] is False and result["first_broken_id"] == 3

    def test_deleting_a_row_breaks_the_chain(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "audit.db")
        sink = DatabaseAuditSink()
        for _ in range(4):
            sink.write(self._event())
        conn = ConnectionFactory.create_connection()
        conn.connect()
        conn.get_connection().execute("DELETE FROM audit_events WHERE id = 2;")
        conn.commit()
        conn.disconnect()
        assert sink.verify_chain()["valid"] is False

    def test_pseudonymisation_keeps_the_chain_valid(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "audit.db")
        sink = DatabaseAuditSink()
        for _ in range(3):
            sink.write(self._event(actor_id=77))
        conn = ConnectionFactory.create_connection()
        conn.connect()
        cursor = conn.get_connection().cursor()
        user_data_purge.UserDataPurger._pseudonymise_audit(cursor, lambda q: q, 77, "someone")
        conn.commit()
        conn.disconnect()

        assert sink.verify_chain()["valid"] is True
        details = [json.loads(r[0]) for r in _rows("SELECT details_json FROM audit_events")]
        assert all(d["email"] == "deleted-user-77" for d in details)

    def test_retention_prunes_old_rows(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "audit.db")
        sink = DatabaseAuditSink()
        sink.write(self._event())
        conn = ConnectionFactory.create_connection()
        conn.connect()
        conn.get_connection().execute("UPDATE audit_events SET occurred_at = '2000-01-01T00:00:00+00:00';")
        conn.commit()
        conn.disconnect()
        sink.write(self._event())

        assert sink.prune(30) == 1
        assert sink.prune(0) == 0

    def test_verify_endpoint(self, client: TestClient, people) -> None:
        res = client.get("/api/admin/audit-events/verify", headers=people["admin"]["headers"])
        assert res.status_code == 200 and "valid" in res.json()
        assert client.get("/api/admin/audit-events/verify", headers=people["victim"]["headers"]).status_code == 403


def test_ownerless_rows_are_counted_then_deleted(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "legacy.db")
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    conn.get_connection().execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    conn.commit()
    conn.disconnect()
    purger = user_data_purge.UserDataPurger(artifact_store=None)  # type: ignore[arg-type]

    assert purger.purge_ownerless(dry_run=True)["pipeline_runs"] == 1
    purger.purge_ownerless(dry_run=False)
    assert purger.purge_ownerless(dry_run=True)["pipeline_runs"] == 0
