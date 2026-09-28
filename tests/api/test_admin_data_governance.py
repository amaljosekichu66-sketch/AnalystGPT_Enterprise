"""
Regression tests for SEC-20, SEC-21 and SEC-25.

Reproduced before the fix:
- SEC-21: two admins demoting each other concurrently both succeeded,
  leaving zero active administrators; the count only looked at the first
  10,000 users.
- SEC-20: deleting a user left all of their pipeline runs, datasets,
  dataset versions, reports, AI jobs and cleaning records in the database
  with no owner, and their files on disk.
- SEC-25: audit events existed only in memory (1,000-event buffer).
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.audit import AuditService
from src.identity.audit_store import DatabaseAuditSink
from src.identity.exceptions import AdminOperationError
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import AdminUserUpdate, AuditEventType, UserCreate, UserLogin, UserRole
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_service import TokenService
from src.identity.user_service import UserService
from tests.fixtures.datasets import run_pipeline_on_file

PW = "Str0ng-Passw0rd!"
TABLES = ("pipeline_runs", "datasets", "reports", "dataset_versions", "cleaning_executions", "ai_jobs")


def _memory_service(**kwargs) -> UserService:
    return UserService(
        InMemoryUserRepository(),
        PBKDF2PasswordHasher(iterations=1000),
        TokenService(secret_key="admin-governance-test-secret-0123456789"),
        **kwargs,
    )


# ==========================================================
# SEC-21 — last active administrator
# ==========================================================


class TestLastAdminGuard:
    def test_concurrent_mutual_demotion_leaves_one_admin(self, monkeypatch) -> None:
        svc = _memory_service()
        a = svc.register_user(UserCreate(username="adm_a", email="a@example.com", password=PW, role=UserRole.ADMIN))
        b = svc.register_user(UserCreate(username="adm_b", email="b@example.com", password=PW, role=UserRole.ADMIN))

        # Hold each request inside the check so both would pass it unguarded.
        barrier = threading.Barrier(2, timeout=2)
        original = svc._count_active_admins

        def racing_count():
            count = original()
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass
            return count

        monkeypatch.setattr(svc, "_count_active_admins", racing_count)

        def demote(target):
            try:
                svc.update_user_admin(target.id, AdminUserUpdate(role=UserRole.ANALYST))
                return "demoted"
            except AdminOperationError:
                return "blocked"

        with ThreadPoolExecutor(2) as pool:
            outcomes = sorted(pool.map(demote, [a, b]))

        assert outcomes == ["blocked", "demoted"]
        assert svc._user_repository.count_active_admins() == 1

    def test_admins_beyond_the_first_10000_users_are_counted(self) -> None:
        svc = _memory_service()
        repo = svc._user_repository
        for i in range(10_001):
            repo.create(UserCreate(username=f"bulk{i}", email=f"bulk{i}@example.com", password=PW), "x")
        late_a = svc.register_user(
            UserCreate(username="late_a", email="late_a@example.com", password=PW, role=UserRole.ADMIN)
        )
        svc.register_user(UserCreate(username="late_b", email="late_b@example.com", password=PW, role=UserRole.ADMIN))

        # Two admins exist, so demoting one is allowed (the old count saw zero and refused).
        svc.update_user_admin(late_a.id, AdminUserUpdate(role=UserRole.ANALYST))
        assert repo.count_active_admins() == 1

    def test_sql_repository_counts_active_admins(self) -> None:
        conn = ConnectionFactory.create_connection()
        conn.connect()
        SchemaManager(conn).initialize_schema()
        repo = UserRepository(conn)
        before = repo.count_active_admins()
        name = f"sql_admin_{uuid.uuid4().hex[:6]}"
        repo.create(UserCreate(username=name, email=f"{name}@example.com", password=PW, role=UserRole.ADMIN), "x")

        assert repo.count_active_admins() == before + 1


# ==========================================================
# SEC-20 — data purge on user deletion
# ==========================================================


@pytest.fixture
def db_users(monkeypatch):
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    set_user_service_instance(None)
    made = {}
    for key, role in (("admin", UserRole.ADMIN), ("leaver", UserRole.ANALYST), ("stayer", UserRole.ANALYST)):
        name = f"purge_{key}_{uuid.uuid4().hex[:6]}"
        user = service.register_user(UserCreate(username=name, email=f"{name}@example.com", password=PW, role=role))
        _, token, _ = service.login(UserLogin(username=name, password=PW))
        made[key] = {"id": user.id, "username": name, "headers": {"Authorization": f"Bearer {token}"}}
    yield made
    conn.disconnect()


def _owned(db: sqlite3.Connection, user_id: int) -> dict[str, int]:
    return {t: db.execute(f"SELECT COUNT(*) FROM {t} WHERE user_id = ?", (user_id,)).fetchone()[0] for t in TABLES}


def test_deleting_a_user_purges_their_rows_and_files(db_users) -> None:
    client = TestClient(app)
    for key in ("leaver", "stayer"):
        assert run_pipeline_on_file(client, "sample_data/customer_data.csv", db_users[key]["headers"]).json()["success"]

    db = sqlite3.connect(config.SQLITE_DATABASE_PATH)
    leaver = db_users["leaver"]["id"]
    run_ids = [r[0] for r in db.execute("SELECT id FROM pipeline_runs WHERE user_id = ?", (leaver,))]
    files = [r[0] for r in db.execute("SELECT storage_path FROM dataset_versions WHERE user_id = ?", (leaver,))]
    files += [r[0] for r in db.execute("SELECT report_path FROM reports WHERE user_id = ?", (leaver,))]
    stayer_before = _owned(db, db_users["stayer"]["id"])
    assert all(_owned(db, leaver).values()) and files

    res = client.delete(f"/api/admin/users/{leaver}", headers=db_users["admin"]["headers"])

    assert res.status_code == 200
    assert not any(_owned(db, leaver).values())
    placeholders = ",".join("?" * len(run_ids))
    for table in ("datasets", "reports", "ai_jobs", "cleaning_executions", "quality_reports", "analytics_reports"):
        left = db.execute(f"SELECT COUNT(*) FROM {table} WHERE pipeline_run_id IN ({placeholders})", run_ids).fetchone()
        assert left[0] == 0, table
    assert not any(Path(p).exists() for p in files if p)
    assert _owned(db, db_users["stayer"]["id"]) == stayer_before
    db.close()


def test_purge_refuses_a_mismatched_account(db_users) -> None:
    from src.api.dependencies.application_dependency import get_application

    client = TestClient(app)
    assert run_pipeline_on_file(client, "sample_data/customer_data.csv", db_users["stayer"]["headers"]).json()[
        "success"
    ]
    db = sqlite3.connect(config.SQLITE_DATABASE_PATH)
    before = _owned(db, db_users["stayer"]["id"])

    assert get_application().purge_user_data(db_users["stayer"]["id"], "someone-else") == {}
    assert _owned(db, db_users["stayer"]["id"]) == before
    db.close()


# ==========================================================
# SEC-25 — durable audit trail
# ==========================================================


class TestDurableAudit:
    def test_events_survive_a_restart(self) -> None:
        marker = f"audit_{uuid.uuid4().hex[:8]}"
        AuditService(sink=DatabaseAuditSink()).record_event(
            AuditEventType.USER_UPDATED, action="TEST_ACTION", actor_username=marker
        )

        fresh = DatabaseAuditSink()  # a new process would start from here
        events = fresh.recent(limit=50, event_type=AuditEventType.USER_UPDATED.value)
        assert any(e["actor_username"] == marker and e["action"] == "TEST_ACTION" for e in events)

    def test_audit_endpoint_is_admin_only(self, db_users) -> None:
        client = TestClient(app)
        client.delete("/api/admin/users/999999999", headers=db_users["admin"]["headers"])

        admin = client.get("/api/admin/audit-events", params={"limit": 20}, headers=db_users["admin"]["headers"])
        analyst = client.get("/api/admin/audit-events", headers=db_users["stayer"]["headers"])

        assert admin.status_code == 200 and isinstance(admin.json(), list) and admin.json()
        assert analyst.status_code == 403

    def test_store_failure_does_not_break_the_operation(self, caplog) -> None:
        class BrokenSink:
            def write(self, event):
                raise RuntimeError("database unavailable")

        with caplog.at_level(logging.ERROR):
            event = AuditService(sink=BrokenSink()).record_event(AuditEventType.LOGOUT, action="USER_LOGOUT")

        assert event.action == "USER_LOGOUT"
        assert any("AUDIT_PERSIST_FAILED" in r.getMessage() for r in caplog.records)

    def test_security_relevant_events_raise_an_alert_line(self, caplog) -> None:
        with caplog.at_level(logging.WARNING):
            AuditService().record_event(AuditEventType.ACCESS_DENIED, action="PERMISSION_CHECK", outcome="DENIED")
            AuditService().record_event(AuditEventType.LOGIN_SUCCESS, action="USER_LOGIN")

        alerts = [r.getMessage() for r in caplog.records if r.getMessage().startswith("SECURITY_ALERT")]
        assert len(alerts) == 1 and "ACCESS_DENIED" in alerts[0]
