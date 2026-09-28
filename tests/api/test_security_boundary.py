"""
Regression tests for the HTTP security boundary.

Each test here pins a defect that was reproduced against the running
application during the Sprint 14 forensic audit:

1. `GET /api/admin/users` with `X-User-Role: ADMIN` and no token returned 200
   and the full user directory.
2. The CORS middleware reflected any `Origin` back with
   `Access-Control-Allow-Credentials: true`.
3. `AUTH_SECRET_KEY` silently fell back to a key published in the repository.

The authorization layer itself was never the problem - it correctly returned
403 for an ANALYST. The problem was that the identity feeding it was
caller-supplied, so these tests target authentication, not RBAC.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.core import config


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ==========================================================
# 1. Identity headers must not authenticate
# ==========================================================


@pytest.fixture()
def header_identity_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restore the production posture inside this test package."""
    monkeypatch.setattr(
        "src.core.config.AUTH_ALLOW_HEADER_IDENTITY",
        False,
        raising=False,
    )


def test_header_identity_is_disabled_by_default() -> None:
    """The shipped default must be off, whatever the test fixtures do."""
    reloaded = importlib.reload(config)
    try:
        assert reloaded.AUTH_ALLOW_HEADER_IDENTITY is False
    finally:
        importlib.reload(config)


@pytest.mark.usefixtures("header_identity_disabled")
def test_forged_admin_header_cannot_reach_admin_endpoint(
    client: TestClient,
) -> None:
    """
    The reproduction case: ADMIN asserted by header, no token.

    Observed before the fix: 200 plus every user record.
    """
    response = client.get(
        "/api/admin/users",
        headers={
            "X-User-Id": "999999",
            "X-User-Name": "attacker",
            "X-User-Role": "ADMIN",
        },
    )

    assert response.status_code == 401
    assert "items" not in response.text


@pytest.mark.usefixtures("header_identity_disabled")
def test_forged_header_cannot_read_current_user(
    client: TestClient,
) -> None:
    """`/api/auth/me` returned a real user record for a forged id."""
    response = client.get(
        "/api/auth/me",
        headers={"X-User-Id": "1", "X-User-Role": "ADMIN"},
    )

    assert response.status_code == 401


@pytest.mark.usefixtures("header_identity_disabled")
def test_anonymous_request_is_still_rejected(client: TestClient) -> None:
    """Refusing headers must not accidentally open the anonymous path."""
    response = client.get("/api/admin/users")

    assert response.status_code == 401


@pytest.mark.usefixtures("header_identity_disabled")
def test_malformed_bearer_token_is_rejected(client: TestClient) -> None:
    """Token authentication remains the only accepted mechanism."""
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_header_identity_still_works_when_explicitly_enabled(
    client: TestClient,
) -> None:
    """
    The development convenience must survive the fix.

    The package-level autouse fixture enables the flag, so this request takes
    the same path a developer gets locally.
    """
    response = client.get(
        "/api/admin/users",
        headers={"X-User-Id": "1", "X-User-Role": "ADMIN"},
    )

    assert response.status_code == 200


# ==========================================================
# 2. CORS must not reflect arbitrary origins
# ==========================================================


def test_cors_does_not_reflect_an_unknown_origin(client: TestClient) -> None:
    """
    Observed before the fix:
        access-control-allow-origin : https://evil.example.com
        access-control-allow-credentials : true
    """
    response = client.get(
        "/api/health",
        headers={"Origin": "https://evil.example.com"},
    )

    allowed = response.headers.get("access-control-allow-origin")
    assert allowed != "https://evil.example.com"
    assert allowed != "*"


def test_cors_allows_a_configured_origin(client: TestClient) -> None:
    """The legitimate frontend origin must still be permitted."""
    origin = config.CORS_ALLOWED_ORIGINS[0]

    response = client.get("/api/health", headers={"Origin": origin})

    assert response.headers.get("access-control-allow-origin") == origin


def test_wildcard_origin_is_not_configured() -> None:
    """A wildcard plus credentials is the reflection bug in disguise."""
    assert "*" not in config.CORS_ALLOWED_ORIGINS


# ==========================================================
# 3. The signing key must not be the published default
# ==========================================================


def test_default_secret_key_is_refused_outside_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Startup must fail rather than sign tokens with a public key."""
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        importlib.reload(config)

    monkeypatch.undo()
    importlib.reload(config)


def test_explicit_secret_key_is_accepted_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_SECRET_KEY", "a-private-deployment-key")

    try:
        reloaded = importlib.reload(config)
        assert reloaded.AUTH_SECRET_KEY == "a-private-deployment-key"
        assert reloaded.IS_DEVELOPMENT is False
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_header_identity_cannot_be_enabled_outside_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The flag is development-only; the combination is refused outright."""
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_SECRET_KEY", "a-private-deployment-key")
    monkeypatch.setenv("AUTH_ALLOW_HEADER_IDENTITY", "true")

    with pytest.raises(RuntimeError, match="AUTH_ALLOW_HEADER_IDENTITY"):
        importlib.reload(config)

    monkeypatch.undo()
    importlib.reload(config)
