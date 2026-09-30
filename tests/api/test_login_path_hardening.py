"""
Regression tests for the login-path findings of the 2026-09-29 audit.

- M1: the unknown-user dummy hash had an undecodable salt, so verify()
  returned without running PBKDF2 (0.0003 s against 0.70 s for a real user).
- M2: `async def` login/register ran 600k-iteration PBKDF2 on the event loop.
- L1: a disabled account answered 403 to the right password, 401 otherwise.
- L2: the login identifier was unbounded and logged verbatim.
- I4: registration logged the full email address.
- I1: `token + "=="` verified as the same token.
"""

from __future__ import annotations

import asyncio
import inspect
import logging

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.routes import auth as auth_routes
from src.api.server import app
from src.core import config
from src.core.logger import logger
from src.identity import password_hasher as hasher_module
from src.identity.audit import AuditService
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import UserStatus, UserUpdate
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService

STRONG = "Str0ng-Passw0rd!"
SECRET = "login-path-test-secret-key-0123456789abcd"


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


@pytest.fixture
def log_lines():
    lines: list[str] = []

    class _Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            lines.append(record.getMessage())

    handler = _Collect()
    logger.addHandler(handler)
    yield lines
    logger.removeHandler(handler)


@pytest.fixture
def pbkdf2_calls(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Iteration counts of every PBKDF2 derivation made through the hasher module."""
    calls: list[int] = []
    real = hasher_module.hashlib.pbkdf2_hmac

    def counting(*args, **kwargs):
        calls.append(args[3])
        return real(*args, **kwargs)

    monkeypatch.setattr(hasher_module.hashlib, "pbkdf2_hmac", counting)
    return calls


def _register(client: TestClient, name: str) -> dict:
    res = client.post("/api/auth/register", json={"username": name, "email": f"{name}@example.com", "password": STRONG})
    assert res.status_code == 201, res.text
    return res.json()


def _login(client: TestClient, name: str, password: str = STRONG):
    return client.post("/api/auth/login", json={"username": name, "password": password})


def _off_event_loop() -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return True
    return False


class TestUnknownUserRunsPbkdf2:
    def test_dummy_hash_is_a_real_hash(self, service, pbkdf2_calls) -> None:
        assert service._password_hasher.verify("anything", service._dummy_hash) is False
        assert pbkdf2_calls == [10_000]

    def test_unknown_user_login_derives_a_key(self, client: TestClient, pbkdf2_calls) -> None:
        assert _login(client, "nobody_here").status_code == 401
        assert pbkdf2_calls == [10_000]

    def test_default_dummy_hash_uses_production_iterations(self) -> None:
        svc = UserService(user_repository=InMemoryUserRepository(), token_service=TokenService(secret_key=SECRET))
        assert svc._dummy_hash.startswith("$pbkdf2-sha256$600000$")


class TestHashingOffTheEventLoop:
    @pytest.mark.parametrize("endpoint", [auth_routes.login, auth_routes.register, auth_routes.logout])
    def test_endpoints_are_sync(self, endpoint) -> None:
        assert not inspect.iscoroutinefunction(endpoint)

    def test_login_runs_in_a_worker_thread(self, client: TestClient, service, monkeypatch) -> None:
        _register(client, "threaded")
        seen: list[bool] = []
        original = service.authenticate_user

        def probe(*args, **kwargs):
            seen.append(_off_event_loop())
            return original(*args, **kwargs)

        monkeypatch.setattr(service, "authenticate_user", probe)
        assert _login(client, "threaded").status_code == 200
        assert seen == [True]

    def test_token_verification_runs_in_a_worker_thread(self, client: TestClient, service, monkeypatch) -> None:
        _register(client, "threaded_me")
        token = _login(client, "threaded_me").json()["access_token"]
        seen: list[bool] = []
        original = service.get_current_user_from_token

        def probe(token_value):
            seen.append(_off_event_loop())
            return original(token_value)

        monkeypatch.setattr(service, "get_current_user_from_token", probe)
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
        assert seen == [True]


def test_disabled_account_with_right_password_matches_wrong_password(client: TestClient, service) -> None:
    user = _register(client, "sleeper")
    service._user_repository.update(user["id"], UserUpdate(status=UserStatus.SUSPENDED))

    right = _login(client, "sleeper")
    wrong = _login(client, "sleeper", "Wr0ng-Passw0rd!")

    assert right.status_code == wrong.status_code == 401
    assert {k: v for k, v in right.json().items() if k != "request_id"} == {
        k: v for k, v in wrong.json().items() if k != "request_id"
    }


class TestLoginInputBounds:
    def test_overlong_identifier_rejected(self, client: TestClient) -> None:
        assert _login(client, "a" * 255).status_code == 422

    def test_overlong_password_rejected(self, client: TestClient) -> None:
        assert _login(client, "someone", "p" * 129).status_code == 422

    def test_unknown_fields_rejected(self, client: TestClient) -> None:
        res = client.post("/api/auth/login", json={"username": "x", "password": "y", "role": "ADMIN"})
        assert res.status_code == 422

    def test_unknown_identifier_is_not_logged_or_audited(self, client: TestClient, service, log_lines) -> None:
        secret_like = "MyPassw0rd!typed-into-username"
        assert _login(client, secret_like).status_code == 401
        assert log_lines
        assert not any(secret_like in line for line in log_lines)
        assert not any(secret_like in (e.actor_username or "") for e in service._audit_service.get_events())

    def test_identifier_cannot_forge_log_lines(self, client: TestClient, service, log_lines) -> None:
        forged = "bob\nSECURITY_ALERT | forged"
        for _ in range(config.AUTH_LOGIN_MAX_FAILURES + 1):
            _login(client, forged)
        assert not any("\nSECURITY_ALERT" in line for line in log_lines)
        assert not any("\n" in (e.actor_username or "") for e in service._audit_service.get_events())


def test_registration_log_masks_email(client: TestClient, log_lines) -> None:
    _register(client, "masked")
    assert not any("masked@example.com" in line for line in log_lines)
    assert any("m***@example.com" in line for line in log_lines)


def test_padded_token_is_rejected(client: TestClient) -> None:
    _register(client, "padder")
    token = _login(client, "padder").json()["access_token"]
    ok = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    padded = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}=="})
    assert ok.status_code == 200
    assert padded.status_code == 401
