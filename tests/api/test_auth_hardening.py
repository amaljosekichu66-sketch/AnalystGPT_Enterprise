"""
Regression tests for the authentication findings SEC-08, SEC-09, SEC-15,
SEC-16 and SEC-18. Each was reproduced against the running API first:

- SEC-08: `aaaaaaaa` / `password` accepted; 15 wrong logins then the right one
  -> 200; 30 rapid registrations from one client -> 30 x 201.
- SEC-09: unauthenticated logout with a 5,000-character junk "token" -> 200
  and stored; a revoked token was valid again after an API restart.
- SEC-15: the 409 named the existing username.
- SEC-16: two logins in the same second returned the identical token; no
  jti / iss / aud claims.
- SEC-18: a non-ASCII header segment -> 400 with a raw codec error.
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

from src.api import rate_limit
from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.exceptions import InvalidTokenError
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.login_throttle import LoginThrottle
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.password_policy import WeakPasswordError, validate_password_strength
from src.identity.token_revocation import DatabaseTokenRevocationService, TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import DUPLICATE_ACCOUNT_MESSAGE, UserService

STRONG = "Str0ng-Passw0rd!"
SECRET = "auth-hardening-test-secret-key-0123456789"


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    svc = UserService(
        user_repository=InMemoryUserRepository(),
        password_hasher=PBKDF2PasswordHasher(iterations=10_000),
        token_service=TokenService(secret_key=SECRET),
        revocation_service=TokenRevocationService(),
    )
    set_user_service_instance(svc)
    yield svc
    set_user_service_instance(None)


@pytest.fixture
def client(service) -> TestClient:
    return TestClient(app)


def _register(client: TestClient, name: str, password: str = STRONG):
    return client.post(
        "/api/auth/register", json={"username": name, "email": f"{name}@example.com", "password": password}
    )


def _login(client: TestClient, name: str, password: str = STRONG):
    return client.post("/api/auth/login", json={"username": name, "password": password})


# ==========================================================
# SEC-08 — password policy, lockout, rate limits
# ==========================================================


class TestPasswordPolicy:
    @pytest.mark.parametrize("password", ["aaaaaaaa", "password", "Password123", "12345678", "abababab", "short1!"])
    def test_weak_passwords_rejected_at_registration(self, client: TestClient, service, password: str) -> None:
        res = _register(client, f"weak_{uuid.uuid4().hex[:6]}", password)

        # 422 = schema length check, 400 = password policy; either way nothing is created.
        assert res.status_code in (400, 422)
        assert service._user_repository.count() == 0

    def test_password_containing_username_rejected(self) -> None:
        with pytest.raises(WeakPasswordError, match="username"):
            validate_password_strength("xx-carol_ops-2026", username="carol_ops", email="c@example.com")

    def test_strong_password_accepted(self, client: TestClient) -> None:
        assert _register(client, "strong_user").status_code == 201


class TestLoginLockout:
    def test_repeated_failures_lock_the_account_even_for_the_right_password(self, client: TestClient) -> None:
        _register(client, "victim")
        codes = [_login(client, "victim", f"wrong-{i}").status_code for i in range(config.AUTH_LOGIN_MAX_FAILURES)]

        locked = _login(client, "victim")

        assert codes == [401] * config.AUTH_LOGIN_MAX_FAILURES
        assert locked.status_code == 429
        assert int(locked.headers["Retry-After"]) >= 1

    def test_unknown_identifiers_lock_identically(self, client: TestClient) -> None:
        for i in range(config.AUTH_LOGIN_MAX_FAILURES):
            _login(client, "ghost_user", f"wrong-{i}")

        assert _login(client, "ghost_user").status_code == 429

    def test_success_resets_the_counter(self, client: TestClient) -> None:
        _register(client, "resetter")
        for i in range(config.AUTH_LOGIN_MAX_FAILURES - 1):
            _login(client, "resetter", f"wrong-{i}")
        assert _login(client, "resetter").status_code == 200

        for i in range(config.AUTH_LOGIN_MAX_FAILURES - 1):
            _login(client, "resetter", f"wrong-{i}")
        assert _login(client, "resetter").status_code == 200

    def test_lockout_is_progressive_and_expires(self) -> None:
        now = [1000.0]
        throttle = LoginThrottle(clock=lambda: now[0])
        lockouts = [throttle.record_failure("u") for _ in range(config.AUTH_LOGIN_MAX_FAILURES + 2)]

        base = config.AUTH_LOGIN_LOCKOUT_BASE_SECONDS
        assert lockouts[-3:] == [base, base * 2, base * 4]
        assert throttle.retry_after("u") == base * 4
        now[0] += base * 4 + 1
        assert throttle.retry_after("u") == 0

    def test_lockout_is_capped(self) -> None:
        throttle = LoginThrottle(clock=lambda: 0.0)
        for _ in range(60):
            last = throttle.record_failure("u")
        assert last == config.AUTH_LOGIN_LOCKOUT_MAX_SECONDS


class TestRateLimits:
    @pytest.fixture(autouse=True)
    def enabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(config, "AUTH_RATE_LIMIT_ENABLED", True)
        rate_limit.limiter.reset()
        yield
        rate_limit.limiter.reset()

    def test_registration_is_rate_limited_per_client(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(config, "AUTH_REGISTER_RATE_LIMIT", "3/600")

        codes = [_register(client, f"burst_{i}").status_code for i in range(5)]

        assert codes[:3] == [201, 201, 201]
        assert codes[3:] == [429, 429]

    def test_login_is_rate_limited_per_client(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(config, "AUTH_LOGIN_RATE_LIMIT", "4/60")
        monkeypatch.setattr(config, "AUTH_LOGIN_MAX_FAILURES", 1000)

        codes = [_login(client, f"spray_{i}", "whatever-1").status_code for i in range(6)]

        assert codes[:4] == [401] * 4
        assert codes[4:] == [429, 429]


# ==========================================================
# SEC-09 — logout and persistent revocation
# ==========================================================


class TestLogout:
    def test_logout_requires_authentication_and_stores_nothing(self, client: TestClient, service) -> None:
        anonymous = client.post("/api/auth/logout")
        junk = client.post("/api/auth/logout", headers={"Authorization": "Bearer " + "x" * 5000})

        assert anonymous.status_code == 401
        assert junk.status_code == 401
        assert len(service._revocation_service) == 0

    def test_logout_revokes_only_that_token(self, client: TestClient) -> None:
        _register(client, "multi_session")
        first = _login(client, "multi_session").json()["access_token"]
        second = _login(client, "multi_session").json()["access_token"]

        assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {first}"}).status_code == 200

        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {first}"}).status_code == 401
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {second}"}).status_code == 200

    def test_in_memory_revocations_expire(self) -> None:
        store = TokenRevocationService()
        store.revoke("expired", int(time.time()) - 1)
        store.revoke("live", int(time.time()) + 60)

        assert not store.is_revoked("expired")
        assert store.is_revoked("live")
        assert len(store) == 1


def test_revocation_survives_api_restart(monkeypatch: pytest.MonkeyPatch) -> None:
    """The original PoC: log out, restart the API, reuse the token."""
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    name = f"restart_{uuid.uuid4().hex[:6]}"
    UserService(user_repository=UserRepository(conn)).register_user(
        UserCreate(username=name, email=f"{name}@example.com", password=STRONG, role=UserRole.ANALYST)
    )
    conn.disconnect()

    set_user_service_instance(None)
    try:
        client = TestClient(app)
        token = _login(client, name).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.post("/api/auth/logout", headers=headers).status_code == 200

        set_user_service_instance(None)  # a fresh UserService == API restart / another worker

        assert client.get("/api/auth/me", headers=headers).status_code == 401
        claims = TokenService().verify_access_token(token)
        assert DatabaseTokenRevocationService().is_revoked(claims["jti"])
    finally:
        set_user_service_instance(None)


# ==========================================================
# SEC-15 — no enumeration through the 409
# ==========================================================


def test_duplicate_registration_does_not_say_which_field(client: TestClient) -> None:
    _register(client, "taken_name")

    by_name = client.post(
        "/api/auth/register", json={"username": "taken_name", "email": "fresh@example.com", "password": STRONG}
    )
    by_email = client.post(
        "/api/auth/register", json={"username": "fresh_name", "email": "taken_name@example.com", "password": STRONG}
    )

    assert by_name.status_code == by_email.status_code == 409
    assert by_name.json()["error"] == by_email.json()["error"] == DUPLICATE_ACCOUNT_MESSAGE
    assert "taken_name" not in by_name.text + by_email.text


# ==========================================================
# SEC-16 — unique, bound tokens
# ==========================================================


def _forge(claims: dict) -> str:
    def enc(obj: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    signing_input = f"{enc({'alg': 'HS256', 'typ': 'JWT'})}.{enc(claims)}"
    sig = hmac.new(SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{base64.urlsafe_b64encode(sig).decode().rstrip('=')}"


class TestTokenClaims:
    def test_same_second_logins_get_distinct_tokens(self, service) -> None:
        service.register_user(UserCreate(username="twice", email="twice@example.com", password=STRONG))

        _, first, _ = service.login(UserLogin(username="twice", password=STRONG))
        _, second, _ = service.login(UserLogin(username="twice", password=STRONG))

        assert first != second
        claims = TokenService(secret_key=SECRET).verify_access_token(first)
        assert claims["iss"] == config.AUTH_TOKEN_ISSUER
        assert claims["aud"] == config.AUTH_TOKEN_AUDIENCE
        assert len(claims["jti"]) >= 32

    @pytest.mark.parametrize(
        "override, reason",
        [
            ({"jti": None}, "unique identifier"),
            ({"iss": "someone-else"}, "issuer"),
            ({"aud": "another-api"}, "audience"),
        ],
    )
    def test_correctly_signed_tokens_with_bad_claims_are_rejected(self, override: dict, reason: str) -> None:
        claims = {
            "sub": "1",
            "type": "access",
            "iat": int(time.time()),
            "exp": int(time.time()) + 60,
            "jti": uuid.uuid4().hex,
            "iss": config.AUTH_TOKEN_ISSUER,
            "aud": config.AUTH_TOKEN_AUDIENCE,
        }
        claims.update(override)
        claims = {k: v for k, v in claims.items() if v is not None}

        with pytest.raises(InvalidTokenError, match=reason):
            TokenService(secret_key=SECRET).verify_access_token(_forge(claims))


# ==========================================================
# SEC-18 — non-ASCII tokens
# ==========================================================


@pytest.mark.parametrize("token", ["aé.b.c", "a.bé.c", "a.b.é"])
def test_non_ascii_tokens_are_401_not_400(client: TestClient, token: str) -> None:
    res = client.get("/api/auth/me", headers={"Authorization": ("Bearer " + token).encode("latin-1")})

    assert res.status_code == 401
    assert "codec" not in res.text

    with pytest.raises(InvalidTokenError):
        TokenService(secret_key=SECRET).verify_access_token(token)
