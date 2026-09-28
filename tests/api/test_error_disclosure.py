"""
Regression tests for SEC-11: internal exception text in API responses.

Reproduced before the fix: an unexpected exception's message came back in
the 500 body, a failed pipeline returned its raw exception text in
`PipelineResponse.error`, and the governance preview echoed `Preview failed:
<exception>` - a simulated credential string leaked through all three - with
no request id to correlate anything.
"""

from __future__ import annotations

import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import get_application
from src.api.server import app
from src.application.app import Application
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.governance.preview_service import CleaningPreviewService
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from tests.fixtures.datasets import upload_dataset

SECRET = "db password=hunter2 at internal-host:5432"


@pytest.fixture(scope="module")
def headers() -> dict[str, str]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"sec11_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password="Str0ng-Passw0rd!", role=UserRole.ANALYST)
    )
    _, token, _ = service.login(UserLogin(username=name, password="Str0ng-Passw0rd!"))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app, raise_server_exceptions=False)


def _boom():
    raise RuntimeError(SECRET)


def test_unhandled_exception_body_is_generic_and_correlated(client, headers, caplog) -> None:
    app.dependency_overrides[get_application] = _boom
    try:
        with caplog.at_level(logging.ERROR):
            res = client.get("/api/reports", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 500
    assert "hunter2" not in res.text
    body = res.json()
    assert body["request_id"] and body["request_id"] == res.headers["X-Request-ID"]
    assert body["request_id"] in body["error"]
    # ...and the detail is where an operator can find it.
    assert any(body["request_id"] in r.getMessage() and "hunter2" in r.getMessage() for r in caplog.records)


def test_pipeline_failure_does_not_return_exception_text(client, headers, monkeypatch) -> None:
    dataset_id = upload_dataset(client, "sample_data/customer_data.csv", headers)
    monkeypatch.setattr(Application, "_assess_quality", lambda self, df: _boom())

    res = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=headers)

    assert res.status_code == 200 and res.json()["success"] is False
    assert "hunter2" not in res.text
    assert res.headers["X-Request-ID"] in res.json()["error"]


def test_preview_failure_does_not_return_exception_text(client, headers, monkeypatch) -> None:
    dataset_id = upload_dataset(client, "sample_data/customer_data.csv", headers)
    monkeypatch.setattr(CleaningPreviewService, "preview", lambda *a, **k: _boom())

    res = client.post("/api/governance/preview", json={"dataset_version_id": dataset_id}, headers=headers)

    assert res.status_code == 400
    assert "hunter2" not in res.text


def test_internal_value_error_is_generic(client, headers) -> None:
    def bad_value():
        raise ValueError(SECRET)

    app.dependency_overrides[get_application] = bad_value
    try:
        res = client.get("/api/reports", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 400
    assert "hunter2" not in res.text


def test_intentional_client_errors_keep_their_message(client) -> None:
    res = client.post(
        "/api/auth/register", json={"username": "policy_user", "email": "p@example.com", "password": "password"}
    )
    assert res.status_code == 400
    assert "too common" in res.json()["error"]


class TestRequestId:
    def test_every_response_carries_one(self, client) -> None:
        res = client.get("/api/health")
        assert len(res.headers["X-Request-ID"]) == 32

    def test_safe_caller_id_is_echoed(self, client) -> None:
        res = client.get("/api/health", headers={"X-Request-ID": "trace-123.abc_DEF"})
        assert res.headers["X-Request-ID"] == "trace-123.abc_DEF"

    @pytest.mark.parametrize("unsafe", ["has space", "x" * 65, "semi;colon", "<script>"])
    def test_unsafe_caller_id_is_replaced(self, client, unsafe: str) -> None:
        res = client.get("/api/health", headers={"X-Request-ID": unsafe})
        assert res.headers["X-Request-ID"] != unsafe
        assert len(res.headers["X-Request-ID"]) == 32
