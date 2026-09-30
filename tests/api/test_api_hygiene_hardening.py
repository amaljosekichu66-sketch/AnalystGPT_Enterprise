"""
Regression tests for L14, L13, L15 and the rest of I10 (audit 2026-09-29).

- L14: no security headers and no Host allow-list (the body limit is covered
  in test_upload_limits_hardening.py).
- L13: uploads, pipeline runs, exports, admin cross-tenant reads, rejected
  tokens, rate-limit hits and blocked last-admin attempts were not audited.
- L15: export temp files survived a malformed Range header or disconnect.
- I10: unused permissions, AdminUserUpdate ignored unknown fields, CORS sent
  allow-credentials.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.api import rate_limit
from src.api.server import app
from src.application.reporting_orchestrator import ReportingOrchestrator
from src.core import config
from src.identity.audit import get_audit_service
from src.identity.models import AdminUserUpdate, AuditEventType

REPO = Path(__file__).resolve().parents[2]
ADMIN = {"X-User-Id": "7001", "X-User-Name": "hygiene_admin", "X-User-Role": "ADMIN"}
ANALYST = {"X-User-Id": "7002", "X-User-Name": "hygiene_analyst", "X-User-Role": "ANALYST"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", True)
    return TestClient(app)


def _events(event_type: AuditEventType) -> list:
    return get_audit_service().get_events(event_type=event_type, limit=1000)


class TestSecurityHeaders:
    def test_api_responses_carry_hardening_headers(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.headers["x-content-type-options"] == "nosniff"
        assert res.headers["x-frame-options"] == "DENY"
        assert res.headers["referrer-policy"] == "no-referrer"
        assert "frame-ancestors 'none'" in res.headers["content-security-policy"]
        assert "default-src 'none'" in res.headers["content-security-policy"]

    def test_error_responses_carry_them_too(self, client: TestClient) -> None:
        assert client.get("/api/does-not-exist").headers["x-content-type-options"] == "nosniff"

    def test_hsts_only_when_enabled(self, client: TestClient, monkeypatch) -> None:
        assert "strict-transport-security" not in client.get("/api/health").headers
        monkeypatch.setattr(config, "API_HSTS_ENABLED", True)
        assert "max-age=" in client.get("/api/health").headers["strict-transport-security"]


class TestTrustedHosts:
    def test_middleware_is_registered_with_the_configured_hosts(self) -> None:
        entries = [m for m in app.user_middleware if m.cls.__name__ == "TrustedHostMiddleware"]
        assert entries and entries[0].kwargs["allowed_hosts"] == config.API_ALLOWED_HOSTS

    def test_deployed_default_is_restrictive(self) -> None:
        env = {**os.environ, "APP_ENVIRONMENT": "production"}
        env.pop("API_ALLOWED_HOSTS", None)
        out = subprocess.run(
            [sys.executable, "-c", "from src.core import config; print(config.API_ALLOWED_HOSTS)"],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "'*'" not in out and "'api'" in out


def test_cors_does_not_allow_credentials(client: TestClient) -> None:
    origin = config.CORS_ALLOWED_ORIGINS[0]
    res = client.options("/api/health", headers={"Origin": origin, "Access-Control-Request-Method": "GET"})
    assert res.headers.get("access-control-allow-origin") == origin
    assert "access-control-allow-credentials" not in res.headers


def test_admin_user_update_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AdminUserUpdate.model_validate({"role": "VIEWER", "hashed_password": "x"})


def test_read_only_admin_routes_use_user_read() -> None:
    source = (REPO / "src" / "api" / "routes" / "admin.py").read_text(encoding="utf-8")
    assert source.count("require_permission(Permission.USER_READ)") == 2


class TestExports:
    @pytest.fixture
    def export_file(self, tmp_path: Path, monkeypatch) -> Path:
        path = tmp_path / "export_abc.txt"
        path.write_text("report body", encoding="utf-8")
        monkeypatch.setattr(
            ReportingOrchestrator,
            "export_text_report",
            lambda self, user_id=None, report_id=None: {
                "success": True,
                "path": str(path),
                "filename": 'report "x".txt',
                "ephemeral": True,
                "report_id": 42,
            },
        )
        return path

    def test_export_is_served_deleted_and_audited(self, client: TestClient, export_file: Path) -> None:
        before = len(_events(AuditEventType.REPORT_EXPORTED))

        res = client.get("/api/reports/latest/export/text", headers=ANALYST)

        assert res.status_code == 200 and res.text == "report body"
        assert 'filename="report__x_.txt"' in res.headers["content-disposition"]
        assert not export_file.exists()
        assert len(_events(AuditEventType.REPORT_EXPORTED)) == before + 1

    def test_malformed_range_still_deletes_the_file(self, client: TestClient, export_file: Path) -> None:
        res = client.get("/api/reports/latest/export/text", headers={**ANALYST, "Range": "bytes=zzz"})
        assert res.status_code == 200
        assert not export_file.exists()


class TestAuditTrail:
    def test_rejected_tokens_are_audited_once_per_client_per_minute(self, client: TestClient) -> None:
        before = len(_events(AuditEventType.TOKEN_REJECTED))
        for _ in range(3):
            assert client.get("/api/auth/me", headers={"Authorization": "Bearer a.b.c"}).status_code == 401
        assert len(_events(AuditEventType.TOKEN_REJECTED)) <= before + 1

    def test_rate_limit_hits_are_audited_once_per_window(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(config, "AUTH_RATE_LIMIT_ENABLED", True)
        monkeypatch.setattr(config, "AUTH_LOGIN_RATE_LIMIT", "1/600")
        rate_limit.limiter.reset()
        before = len(_events(AuditEventType.RATE_LIMITED))
        try:
            codes = [
                client.post("/api/auth/login", json={"username": "x", "password": "y"}).status_code for _ in range(4)
            ]
        finally:
            rate_limit.limiter.reset()
        assert codes.count(429) == 3
        assert len(_events(AuditEventType.RATE_LIMITED)) == before + 1

    def test_admin_reading_another_users_ai_job_is_audited(self, client: TestClient, monkeypatch) -> None:
        from src.ai.ai_job_service import AIJobService

        job = {"job_id": "j", "pipeline_run_id": 1, "status": "READY", "provider": "p", "model": "m", "user_id": 99}
        monkeypatch.setattr(AIJobService, "get_job_with_report", lambda self, **_: job)
        before = len(_events(AuditEventType.ADMIN_CROSS_TENANT_ACCESS))

        assert client.get("/api/ai/jobs/j", headers=ADMIN).status_code == 200

        events = _events(AuditEventType.ADMIN_CROSS_TENANT_ACCESS)
        assert len(events) == before + 1 and events[-1].target_id == 99

    def test_blocked_last_admin_operation_is_audited(self) -> None:
        from src.identity.in_memory_user_repository import InMemoryUserRepository
        from src.identity.models import UserCreate, UserRole
        from src.identity.password_hasher import PBKDF2PasswordHasher
        from src.identity.token_service import TokenService
        from src.identity.user_service import AdminOperationError, UserService

        audit = MagicMock()
        service = UserService(
            user_repository=InMemoryUserRepository(),
            password_hasher=PBKDF2PasswordHasher(iterations=1_000),
            token_service=TokenService(secret_key="x" * 40),
            audit_service=audit,
        )
        admin = service.register_user(
            UserCreate(username="solo", email="solo@example.com", password="Str0ng-Passw0rd!", role=UserRole.ADMIN)
        )
        with pytest.raises(AdminOperationError):
            service.delete_user_admin(admin.id)

        kinds = [call.kwargs.get("event_type") for call in audit.record_event.call_args_list]
        assert AuditEventType.ADMIN_OPERATION_BLOCKED in kinds


def test_upload_and_pipeline_are_audited(monkeypatch: pytest.MonkeyPatch) -> None:
    import uuid

    from src.database.connection_factory import ConnectionFactory
    from src.database.repositories.user_repository import UserRepository
    from src.database.schema_manager import SchemaManager
    from src.identity.models import UserCreate, UserLogin, UserRole
    from src.identity.user_service import UserService
    from tests.fixtures.datasets import upload_dataset

    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"l13_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password="Password123!", role=UserRole.ANALYST)
    )
    _, token, _ = service.login(UserLogin(username=name, password="Password123!"))
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)
    uploads, runs = len(_events(AuditEventType.DATASET_UPLOADED)), len(_events(AuditEventType.PIPELINE_EXECUTED))

    dataset_id = upload_dataset(client, REPO / "sample_data" / "customer_data.csv", headers)
    res = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=headers)

    assert res.status_code == 200
    assert len(_events(AuditEventType.DATASET_UPLOADED)) == uploads + 1
    assert len(_events(AuditEventType.PIPELINE_EXECUTED)) == runs + 1
    assert _events(AuditEventType.PIPELINE_EXECUTED)[-1].actor_username == name
