"""
Regression tests for the session-lifecycle findings of the 2026-09-29 audit.

- I2: no password change, no "log out everywhere", no upper bound on token
  lifetime, and a demoted or suspended user kept using old tokens until
  they expired.
- L4: development mode silently signed tokens with the published key, even
  when the API was bound to a non-loopback address.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.core import config
from src.identity.audit import AuditService
from src.identity.exceptions import InvalidTokenError
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import User, UserCreate, UserRole
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService

STRONG = "Str0ng-Passw0rd!"
NEW = "An0ther-Str0ng-Pass!"
SECRET = "session-lifecycle-test-secret-key-0123456"


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    svc = UserService(
        user_repository=InMemoryUserRepository(),
        password_hasher=PBKDF2PasswordHasher(iterations=1_000),
        token_service=TokenService(secret_key=SECRET),
        revocation_service=TokenRevocationService(),
        audit_service=AuditService(),
    )
    for name, role in (("owner", UserRole.ANALYST), ("chief", UserRole.ADMIN)):
        svc.register_user(UserCreate(username=name, email=f"{name}@example.com", password=STRONG, role=role))
    set_user_service_instance(svc)
    yield svc
    set_user_service_instance(None)


@pytest.fixture
def client(service) -> TestClient:
    return TestClient(app)


def _token(client: TestClient, name: str = "owner", password: str = STRONG) -> str:
    res = client.post("/api/auth/login", json={"username": name, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _me(client: TestClient, token: str) -> int:
    return client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code


def _change(client: TestClient, token: str, current: str, new: str):
    return client.post(
        "/api/auth/password",
        json={"current_password": current, "new_password": new},
        headers={"Authorization": f"Bearer {token}"},
    )


class TestPasswordChange:
    def test_change_signs_out_every_session(self, client: TestClient) -> None:
        first, second = _token(client), _token(client)

        assert _change(client, first, STRONG, NEW).status_code == 200

        assert _me(client, first) == 401
        assert _me(client, second) == 401
        assert client.post("/api/auth/login", json={"username": "owner", "password": STRONG}).status_code == 401
        assert _me(client, _token(client, password=NEW)) == 200

    def test_wrong_current_password_is_refused(self, client: TestClient) -> None:
        token = _token(client)
        res = _change(client, token, "Wr0ng-Passw0rd!", NEW)

        assert res.status_code == 400
        assert _me(client, token) == 200

    def test_new_password_must_meet_policy(self, client: TestClient) -> None:
        token = _token(client)
        assert _change(client, token, STRONG, "password123").status_code == 400

    def test_requires_authentication(self, client: TestClient) -> None:
        res = client.post("/api/auth/password", json={"current_password": STRONG, "new_password": NEW})
        assert res.status_code == 401


def test_logout_everywhere_revokes_every_token(client: TestClient) -> None:
    first, second = _token(client), _token(client)

    res = client.post("/api/auth/logout-all", headers={"Authorization": f"Bearer {first}"})

    assert res.status_code == 200
    assert _me(client, first) == 401
    assert _me(client, second) == 401
    assert _me(client, _token(client)) == 200


@pytest.mark.parametrize("change", [{"role": "VIEWER"}, {"status": "SUSPENDED"}])
def test_role_or_status_change_invalidates_old_tokens(client: TestClient, service, change: dict) -> None:
    victim = _token(client)
    admin = _token(client, "chief")
    user_id = service._user_repository.get_by_username("owner").id

    res = client.patch(f"/api/admin/users/{user_id}", json=change, headers={"Authorization": f"Bearer {admin}"})

    assert res.status_code == 200
    # 401 (token version) for a role change; a suspension is already refused 403.
    assert _me(client, victim) in (401, 403)


def test_email_only_change_keeps_sessions(client: TestClient, service) -> None:
    victim = _token(client)
    admin = _token(client, "chief")
    user_id = service._user_repository.get_by_username("owner").id

    client.patch(
        f"/api/admin/users/{user_id}",
        json={"email": "owner2@example.com"},
        headers={"Authorization": f"Bearer {admin}"},
    )

    assert _me(client, victim) == 200


class TestTokenLifetimeBound:
    def test_issued_lifetime_is_clamped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(config, "AUTH_TOKEN_MAX_LIFETIME_MINUTES", 10)
        service = TokenService(secret_key=SECRET, expire_minutes=600)
        claims = service.verify_access_token(
            service.create_access_token(User(id=1, username="u", email="u@example.com", hashed_password="x"))
        )
        assert claims["exp"] - claims["iat"] == 600

    def test_overlong_tokens_are_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        long_lived = TokenService(secret_key=SECRET, expire_minutes=600).create_access_token(
            User(id=1, username="u", email="u@example.com", hashed_password="x")
        )
        monkeypatch.setattr(config, "AUTH_TOKEN_MAX_LIFETIME_MINUTES", 10)
        with pytest.raises(InvalidTokenError, match="lifetime"):
            TokenService(secret_key=SECRET).verify_access_token(long_lived)


class TestDevelopmentKeyGuard:
    @pytest.mark.parametrize("key", [None, "", config.INSECURE_DEFAULT_AUTH_SECRET_KEY])
    def test_published_key_refused_on_non_loopback_host(self, key) -> None:
        with pytest.raises(RuntimeError, match="loopback"):
            config.validate_auth_secret_key("development", key, "0.0.0.0")

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
    def test_published_key_allowed_on_loopback(self, host: str) -> None:
        assert config.validate_auth_secret_key("development", None, host) == config.INSECURE_DEFAULT_AUTH_SECRET_KEY

    def test_private_key_allowed_anywhere_in_development(self) -> None:
        key = "a-private-development-key-of-enough-length"
        assert config.validate_auth_secret_key("development", key, "0.0.0.0") == key
