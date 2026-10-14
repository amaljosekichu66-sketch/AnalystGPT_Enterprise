"""
Regression tests for P3-05 (Sprint 15 readiness gate).

- Token validation did not check `iat` against the clock or honour `nbf`:
  a token "issued" an hour from now was accepted.
- /api/powerbi/status needed no authentication and always said "Ready".
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from src.core import config
from src.identity.exceptions import InvalidTokenError
from src.identity.token_service import CLOCK_SKEW_SECONDS, TokenService

SECRET = "test-secret-key-32-bytes-long!!!"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _token(**overrides) -> str:
    now = int(time.time())
    payload = {
        "sub": "1",
        "type": "access",
        "iat": now,
        "exp": now + 600,
        "jti": uuid.uuid4().hex,
        "iss": config.AUTH_TOKEN_ISSUER,
        "aud": config.AUTH_TOKEN_AUDIENCE,
    }
    payload.update(overrides)
    payload = {k: v for k, v in payload.items() if v is not None}
    head = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SECRET.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{_b64(sig)}"


@pytest.fixture
def service() -> TokenService:
    return TokenService(secret_key=SECRET)


def test_a_normal_token_verifies(service: TokenService) -> None:
    assert service.verify_access_token(_token())["sub"] == "1"


def test_a_token_issued_in_the_future_is_refused(service: TokenService) -> None:
    now = int(time.time())
    with pytest.raises(InvalidTokenError, match="future"):
        service.verify_access_token(_token(iat=now + 3600, exp=now + 3900))


def test_small_clock_skew_is_tolerated(service: TokenService) -> None:
    now = int(time.time())
    assert service.verify_access_token(_token(iat=now + CLOCK_SKEW_SECONDS - 5, exp=now + 600))


def test_not_before_is_honoured(service: TokenService) -> None:
    now = int(time.time())
    with pytest.raises(InvalidTokenError, match="not yet valid"):
        service.verify_access_token(_token(nbf=now + 3600))
    assert service.verify_access_token(_token(nbf=now - 10))


@pytest.mark.parametrize("claim", ["exp", "iat", "nbf"])
@pytest.mark.parametrize("value", ["1700000000", True, 1.5e12])
def test_time_claims_must_be_integers(service: TokenService, claim: str, value) -> None:
    with pytest.raises(InvalidTokenError):
        service.verify_access_token(_token(**{claim: value}))


# ==========================================================
# /api/powerbi/status
# ==========================================================


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.api.server import app

    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


def _headers(client: TestClient) -> dict[str, str]:
    from src.database.connection_factory import ConnectionFactory
    from src.database.repositories.user_repository import UserRepository
    from src.database.schema_manager import SchemaManager
    from src.identity.models import UserCreate, UserLogin, UserRole
    from src.identity.user_service import UserService

    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"p305_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password="Password123!", role=UserRole.VIEWER)
    )
    _, token, _ = service.login(UserLogin(username=name, password="Password123!"))
    conn.disconnect()
    return {"Authorization": f"Bearer {token}"}


def test_status_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/powerbi/status").status_code == 401


def test_status_reports_the_database_check(client: TestClient) -> None:
    body = client.get("/api/powerbi/status", headers=_headers(client)).json()

    assert body["status"] == "Ready" and body["checks"] == {"database": "ok"}


def test_status_degrades_when_the_database_is_unreachable(monkeypatch) -> None:
    from src.application.dashboard_orchestrator import DashboardOrchestrator
    from src.database import connection_factory

    def broken():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(connection_factory.ConnectionFactory, "create_connection", staticmethod(broken))
    status = DashboardOrchestrator(application=None).get_status()  # type: ignore[arg-type]

    assert status["status"] == "Degraded" and status["checks"] == {"database": "unavailable"}
    assert "connection refused" not in json.dumps(status)
