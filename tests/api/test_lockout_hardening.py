"""
Regression tests for the lockout and rate-limit findings of the 2026-09-29 audit.

- M11: limits were keyed by socket peer, and every Streamlit user reaches the
  API from the frontend's address: one bucket for everybody.
- M12: the lockout was keyed on the identifier alone, so one request every
  15 minutes kept any account (e.g. 'admin') locked; only a restart cleared it.
- L5: lockout was per identifier, so spraying one password across many
  accounts never tripped it; the denylist had ~60 entries.
- I3: lockout state lived in process memory.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from src.api import rate_limit
from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.core import config
from src.identity.audit import AuditService
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.login_throttle import LoginThrottle
from src.identity.login_throttle_store import DatabaseThrottleStore
from src.identity.models import UserCreate, UserRole
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.password_policy import COMMON_PASSWORDS, WeakPasswordError, validate_password_strength
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService

STRONG = "Str0ng-Passw0rd!"
SECRET = "lockout-test-secret-key-0123456789abcdefgh"
FRONTEND = "10.0.0.10"


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
    set_user_service_instance(svc)
    yield svc
    set_user_service_instance(None)


def _client(peer: str = "203.0.113.1") -> TestClient:
    return TestClient(app, client=(peer, 50000))


def _create(service: UserService, name: str, role: UserRole = UserRole.ANALYST) -> None:
    service.register_user(UserCreate(username=name, email=f"{name}@example.com", password=STRONG, role=role))


def _login(client: TestClient, name: str, password: str = STRONG, forwarded: str | None = None):
    headers = {"X-Forwarded-For": forwarded} if forwarded else None
    return client.post("/api/auth/login", json={"username": name, "password": password}, headers=headers)


def _request(peer: str, forwarded: str | None = None) -> Request:
    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
    return Request({"type": "http", "client": (peer, 1), "headers": headers})


class TestClientAddress:
    @pytest.fixture(autouse=True)
    def trust_frontend(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(config, "TRUSTED_PROXY_IPS", f"{FRONTEND}, 192.168.50.0/24")

    def test_untrusted_peer_header_is_ignored(self) -> None:
        assert rate_limit.client_address(_request("198.51.100.7", "1.2.3.4")) == "198.51.100.7"

    def test_trusted_peer_header_is_used(self) -> None:
        assert rate_limit.client_address(_request(FRONTEND, "198.51.100.7")) == "198.51.100.7"

    def test_prepended_fake_hop_is_ignored(self) -> None:
        # The client sent "X-Forwarded-For: 1.2.3.4"; the proxy appended the real address.
        assert rate_limit.client_address(_request(FRONTEND, "1.2.3.4, 198.51.100.7")) == "198.51.100.7"

    def test_trusted_hops_are_skipped(self) -> None:
        assert rate_limit.client_address(_request(FRONTEND, "198.51.100.7, 192.168.50.3")) == "198.51.100.7"

    def test_malformed_header_falls_back_to_peer(self) -> None:
        assert rate_limit.client_address(_request(FRONTEND, "not-an-ip")) == FRONTEND

    def test_nothing_trusted_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(config, "TRUSTED_PROXY_IPS", "")
        assert rate_limit.client_address(_request(FRONTEND, "198.51.100.7")) == FRONTEND


class TestSeparateBucketsBehindTheFrontend:
    @pytest.fixture(autouse=True)
    def enabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(config, "AUTH_RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr(config, "AUTH_LOGIN_RATE_LIMIT", "3/60")
        monkeypatch.setattr(config, "TRUSTED_PROXY_IPS", FRONTEND)
        rate_limit.limiter.reset()
        yield
        rate_limit.limiter.reset()

    def test_one_users_burst_does_not_limit_another(self, service) -> None:
        _create(service, "bystander")
        client = _client(FRONTEND)
        codes = [_login(client, f"noisy_{i}", "wrong-pw-1", forwarded="198.51.100.1").status_code for i in range(4)]

        assert codes[-1] == 429
        assert _login(client, "bystander", forwarded="198.51.100.2").status_code == 200


class TestLockoutIsPerSource:
    def test_attacker_cannot_lock_the_owner_out(self, service) -> None:
        _create(service, "admin_owner", UserRole.ADMIN)
        attacker, owner = _client("198.51.100.66"), _client("203.0.113.5")
        for i in range(config.AUTH_LOGIN_MAX_FAILURES):
            _login(attacker, "admin_owner", f"wrong-{i}")

        assert _login(attacker, "admin_owner").status_code == 429
        assert _login(owner, "admin_owner").status_code == 200

    def test_username_and_email_share_one_counter(self, service) -> None:
        _create(service, "dual")
        client = _client()
        for i in range(config.AUTH_LOGIN_MAX_FAILURES - 1):
            _login(client, "dual", f"wrong-{i}")
        _login(client, "dual@example.com", "wrong-last")

        assert _login(client, "dual").status_code == 429

    def test_account_wide_backoff_is_short(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now = [1000.0]
        throttle = LoginThrottle(clock=lambda: now[0])
        for i in range(config.AUTH_LOGIN_ACCOUNT_MAX_FAILURES):
            throttle.record_failure("user:1", f"198.51.100.{i}")

        assert throttle.retry_after("user:1", "203.0.113.5") == config.AUTH_LOGIN_ACCOUNT_LOCKOUT_SECONDS
        now[0] += config.AUTH_LOGIN_ACCOUNT_LOCKOUT_SECONDS + 1
        assert throttle.retry_after("user:1", "203.0.113.5") == 0

    def test_refused_attempts_do_not_count(self) -> None:
        throttle = LoginThrottle(clock=lambda: 0.0)
        for _ in range(config.AUTH_LOGIN_MAX_FAILURES):
            throttle.record_failure("user:1", "198.51.100.66")
        # Locked for that source: the service refuses before recording anything.
        assert throttle.retry_after("user:1", "198.51.100.66") > 0
        assert throttle.retry_after("user:1", "203.0.113.5") == 0

    def test_admin_can_unlock(self, service) -> None:
        _create(service, "boss", UserRole.ADMIN)
        _create(service, "locked_out")
        client = _client()
        for i in range(config.AUTH_LOGIN_MAX_FAILURES):
            _login(client, "locked_out", f"wrong-{i}")
        assert _login(client, "locked_out").status_code == 429

        token = _login(_client("203.0.113.9"), "boss").json()["access_token"]
        user_id = service._user_repository.get_by_username("locked_out").id
        res = client.post(f"/api/admin/users/{user_id}/unlock", headers={"Authorization": f"Bearer {token}"})

        assert res.status_code == 200
        assert _login(client, "locked_out").status_code == 200

    def test_non_admin_cannot_unlock(self, service) -> None:
        _create(service, "plain")
        client = _client()
        token = _login(client, "plain").json()["access_token"]
        user_id = service._user_repository.get_by_username("plain").id
        res = client.post(f"/api/admin/users/{user_id}/unlock", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403


class TestPasswordSpraying:
    def test_one_source_spraying_many_accounts_is_locked(self, service, monkeypatch) -> None:
        monkeypatch.setattr(config, "AUTH_LOGIN_SOURCE_MAX_FAILURES", 6)
        for i in range(8):
            _create(service, f"target_{i}")
        sprayer = _client("198.51.100.77")
        codes = [_login(sprayer, f"target_{i}", "Summer2026!").status_code for i in range(8)]

        assert codes[:6] == [401] * 6
        assert codes[6:] == [429, 429]
        # Other sources are unaffected.
        assert _login(_client("203.0.113.8"), "target_7").status_code == 200

    def test_bundled_list_is_loaded(self) -> None:
        assert len(COMMON_PASSWORDS) > 2000

    @pytest.mark.parametrize("password", ["michelle", "jennifer", "trustno1", "superman"])
    def test_listed_passwords_are_rejected(self, password: str) -> None:
        with pytest.raises(WeakPasswordError):
            validate_password_strength(password)


def test_lockout_survives_a_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", tmp_path / "throttle.db")
    first = LoginThrottle(store=DatabaseThrottleStore())
    for _ in range(config.AUTH_LOGIN_MAX_FAILURES):
        first.record_failure("user:7", "198.51.100.1")

    restarted = LoginThrottle(store=DatabaseThrottleStore())
    assert restarted.retry_after("user:7", "198.51.100.1") > 0
    assert restarted.retry_after("user:7", "203.0.113.1") == 0

    restarted.unlock("user:7")
    assert first.retry_after("user:7", "198.51.100.1") == 0
