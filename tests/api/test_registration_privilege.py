"""
Regression tests for B-01 / SEC-01: public registration privilege escalation.

`POST /api/auth/register` is unauthenticated. It used to bind the internal
`UserCreate` schema, whose `role` field is writable, so an anonymous request
carrying `"role": "ADMIN"` created an administrator and could immediately call
`/api/admin/*`. The public contract is now `UserRegistration`, which has no
role and forbids unknown fields; the role is fixed server-side.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService

_PASSWORD = "SecurePassword123!"


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch):
    # Production posture: no forgeable identity headers.
    monkeypatch.setattr("src.core.config.AUTH_ALLOW_HEADER_IDENTITY", False)
    svc = UserService(
        user_repository=InMemoryUserRepository(),
        password_hasher=PBKDF2PasswordHasher(iterations=10_000),
        token_service=TokenService(secret_key="registration-privilege-test-secret-key-0123456789"),
        revocation_service=TokenRevocationService(),
    )
    set_user_service_instance(svc)
    yield svc
    set_user_service_instance(None)


@pytest.fixture
def client(service: UserService) -> TestClient:
    return TestClient(app)


def _token(service: UserService, username: str) -> str:
    _, token, _ = service.login(UserLogin(username=username, password=_PASSWORD))
    return token


def _payload(username: str, **extra: object) -> dict[str, object]:
    return {"username": username, "email": f"{username}@example.com", "password": _PASSWORD, **extra}


class TestSelfRegistrationRole:
    def test_register_without_role_gets_default_role(self, client: TestClient, service: UserService) -> None:
        res = client.post("/api/auth/register", json=_payload("plain_user"))

        assert res.status_code == 201
        # VIEWER since M10: self-registration must not grant upload or LLM access.
        assert res.json()["role"] == UserService.SELF_REGISTRATION_ROLE.value == "VIEWER"
        assert service.get_user_by_id(res.json()["id"]).role == UserRole.VIEWER

    @pytest.mark.parametrize("role", ["ADMIN", "admin", " Admin ", "ANALYST", "VIEWER"])
    def test_register_with_role_is_rejected_and_creates_nothing(
        self, client: TestClient, service: UserService, role: str
    ) -> None:
        res = client.post("/api/auth/register", json=_payload("escalator", role=role))

        assert res.status_code == 422
        assert service._user_repository.get_by_username("escalator") is None

    def test_register_with_unknown_privilege_fields_is_rejected(self, client: TestClient, service: UserService) -> None:
        res = client.post("/api/auth/register", json=_payload("escalator2", status="ACTIVE", is_admin=True))

        assert res.status_code == 422
        assert service._user_repository.get_by_username("escalator2") is None

    def test_original_poc_cannot_reach_admin_api(self, client: TestClient) -> None:
        """The original PoC: register as ADMIN, log in, list all users."""
        client.post("/api/auth/register", json=_payload("pocadmin", role="ADMIN"))
        login = client.post("/api/auth/login", json={"username": "pocadmin", "password": _PASSWORD})

        # The account was never created, so there is nothing to log in as.
        assert login.status_code == 401

        client.post("/api/auth/register", json=_payload("pocadmin"))
        token = client.post("/api/auth/login", json={"username": "pocadmin", "password": _PASSWORD}).json()[
            "access_token"
        ]
        res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403


class TestPrivilegedRoleChanges:
    def test_unauthenticated_caller_cannot_grant_admin(self, client: TestClient, service: UserService) -> None:
        created = client.post("/api/auth/register", json=_payload("target_user")).json()

        res = client.patch(f"/api/admin/users/{created['id']}", json={"role": "ADMIN"})

        assert res.status_code == 401
        assert service.get_user_by_id(created["id"]).role == UserRole.VIEWER

    def test_self_registered_user_cannot_promote_self(self, client: TestClient, service: UserService) -> None:
        created = client.post("/api/auth/register", json=_payload("self_promoter")).json()
        token = _token(service, "self_promoter")

        res = client.patch(
            f"/api/admin/users/{created['id']}",
            json={"role": "ADMIN"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 403
        assert service.get_user_by_id(created["id"]).role == UserRole.VIEWER

    def test_admin_can_still_change_roles(self, client: TestClient, service: UserService) -> None:
        service.register_user(
            UserCreate(username="real_admin", email="real_admin@example.com", password=_PASSWORD, role=UserRole.ADMIN)
        )
        created = client.post("/api/auth/register", json=_payload("promotable")).json()

        res = client.patch(
            f"/api/admin/users/{created['id']}",
            json={"role": "VIEWER"},
            headers={"Authorization": f"Bearer {_token(service, 'real_admin')}"},
        )

        assert res.status_code == 200
        assert res.json()["role"] == "VIEWER"
        assert service.get_user_by_id(created["id"]).role == UserRole.VIEWER


class TestAdminBootstrapScript:
    def test_create_admin_script_creates_admin(self, service: UserService, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import create_admin

        monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", _PASSWORD)

        assert create_admin.main(["--username", "boot_admin", "--email", "boot_admin@example.com"]) == 0
        assert service._user_repository.get_by_username("boot_admin").role == UserRole.ADMIN

    def test_create_admin_script_refuses_duplicates(
        self, service: UserService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts import create_admin

        monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", _PASSWORD)
        create_admin.main(["--username", "boot_admin", "--email", "boot_admin@example.com"])

        assert create_admin.main(["--username", "boot_admin", "--email", "other@example.com"]) == 1

    def test_create_admin_script_enforces_password_policy(
        self, service: UserService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts import create_admin

        monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "password")

        assert create_admin.main(["--username", "weak_admin", "--email", "weak_admin@example.com"]) == 2
        assert service._user_repository.get_by_username("weak_admin") is None
