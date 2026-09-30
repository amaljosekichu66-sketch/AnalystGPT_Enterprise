"""
Regression tests for the registration findings of the 2026-09-29 audit.

- M10: open self-registration granted ANALYST (upload, pipeline, LLM access)
  to anyone who could reach the sign-up form. Now VIEWER, and switchable off.
- L3: the repository's pre-insert checks named the clashing field.
- L6: username/email uniqueness was case-sensitive in the schema while every
  lookup used LOWER(), so concurrent 'Alice' / 'alice' registrations could
  both succeed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.core import config
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.identity.audit import AuditService
from src.identity.exceptions import UserAlreadyExistsError
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import UserCreate, UserRole
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import DUPLICATE_ACCOUNT_MESSAGE, UserService

STRONG = "Str0ng-Passw0rd!"
SECRET = "registration-test-secret-key-0123456789ab"


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    svc = UserService(
        user_repository=InMemoryUserRepository(),
        password_hasher=PBKDF2PasswordHasher(iterations=10_000),
        token_service=TokenService(secret_key=SECRET),
        revocation_service=TokenRevocationService(),
        audit_service=AuditService(),
    )
    set_user_service_instance(svc)
    yield svc
    set_user_service_instance(None)


@pytest.fixture
def client(service) -> TestClient:
    return TestClient(app)


def _register(client: TestClient, name: str):
    return client.post(
        "/api/auth/register", json={"username": name, "email": f"{name}@example.com", "password": STRONG}
    )


class TestSelfRegistration:
    def test_self_registered_accounts_are_viewers(self, client: TestClient) -> None:
        res = _register(client, "newcomer")
        assert res.status_code == 201
        assert res.json()["role"] == UserRole.VIEWER.value

    def test_self_registered_viewer_cannot_upload(self, client: TestClient) -> None:
        _register(client, "uploader")
        token = client.post("/api/auth/login", json={"username": "uploader", "password": STRONG}).json()["access_token"]
        res = client.post(
            "/api/datasets",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("a.csv", b"a,b\n1,2\n", "text/csv")},
        )
        assert res.status_code == 403

    def test_registration_can_be_switched_off(self, client: TestClient, service, monkeypatch) -> None:
        monkeypatch.setattr(config, "AUTH_SELF_REGISTRATION_ENABLED", False)
        res = _register(client, "blocked")
        assert res.status_code == 403
        assert service._user_repository.count() == 0


@pytest.fixture
def sqlite_repo(tmp_path: Path):
    conn = SQLiteConnection(str(tmp_path / "users.db"))
    conn.connect()
    SchemaManager(conn).initialize_schema()
    yield UserRepository(conn), conn
    conn.disconnect()


def _create(repo: UserRepository, username: str, email: str):
    return repo.create(UserCreate(username=username, email=email, password=STRONG), hashed_password="x")


class TestCaseInsensitiveUniqueness:
    def test_schema_rejects_case_variants(self, sqlite_repo) -> None:
        repo, conn = sqlite_repo
        _create(repo, "Alice", "alice@example.com")
        with pytest.raises(sqlite3.IntegrityError):
            conn.get_connection().execute(
                "INSERT INTO users(username, email, hashed_password, role, status, created_at, updated_at) "
                "VALUES ('alice', 'other@example.com', 'x', 'VIEWER', 'ACTIVE', '', '');"
            )

    def test_race_past_the_checks_is_a_generic_conflict(self, sqlite_repo, monkeypatch) -> None:
        repo, _ = sqlite_repo
        _create(repo, "Alice", "alice@example.com")
        # Simulate a concurrent registration that passed the pre-insert checks.
        monkeypatch.setattr(repo, "get_by_username", lambda _name: None)
        monkeypatch.setattr(repo, "get_by_email", lambda _email: None)

        with pytest.raises(UserAlreadyExistsError) as info:
            _create(repo, "ALICE", "second@example.com")
        assert str(info.value) == DUPLICATE_ACCOUNT_MESSAGE

    def test_repository_message_does_not_name_the_field(self, sqlite_repo) -> None:
        repo, _ = sqlite_repo
        _create(repo, "Alice", "alice@example.com")
        with pytest.raises(UserAlreadyExistsError) as info:
            _create(repo, "Alice", "fresh@example.com")
        assert "Alice" not in str(info.value)
        assert str(info.value) == DUPLICATE_ACCOUNT_MESSAGE

    def test_existing_case_duplicates_stop_startup(self, tmp_path: Path) -> None:
        conn = SQLiteConnection(str(tmp_path / "legacy.db"))
        conn.connect()
        SchemaManager(conn).initialize_schema()
        raw = conn.get_connection()
        raw.execute("DROP INDEX uq_users_username_lower;")
        for name, email in (("Bob", "bob1@example.com"), ("bob", "bob2@example.com")):
            raw.execute(
                "INSERT INTO users(username, email, hashed_password, role, status, created_at, updated_at) "
                f"VALUES ('{name}', '{email}', 'x', 'VIEWER', 'ACTIVE', '', '');"
            )
        raw.commit()

        with pytest.raises(RuntimeError, match="differ only by case"):
            SchemaManager(conn).initialize_schema()
        conn.disconnect()
