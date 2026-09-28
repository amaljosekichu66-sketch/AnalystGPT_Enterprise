"""
Regression tests for B-04 / SEC-05: VIEWER-triggered pipeline execution.

The dashboard and Power BI routes are gated on DASHBOARD_VIEW / REPORT_VIEW,
which VIEWER holds. On a cache miss they called `Application.get_or_run()`,
so a VIEWER could execute the pipeline without PIPELINE_EXECUTE. Those
routes are now read-only; execution is only reachable through
`POST /api/pipeline`.

Each test counts actual executions (`Application._execute`) and pipeline run
rows, so "no execution" is measured rather than inferred from a status code.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import get_application
from src.api.exceptions.exception_handlers import register_exception_handlers
from src.api.routes.powerbi import router as powerbi_router
from src.api.server import app
from src.application.app import Application
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from tests.fixtures.datasets import upload_dataset

SAMPLE_CSV = Path("sample_data/customer_data.csv")
_PASSWORD = "Password123!"

READ_ROUTES = [
    "/api/powerbi/dashboard",
    "/api/powerbi/summary",
    "/api/powerbi/statistics",
    "/api/powerbi/correlation",
    "/api/powerbi/distribution",
    "/api/powerbi/categorical",
    "/api/powerbi/report",
    "/api/powerbi/pipeline",
]


@pytest.fixture(scope="module")
def tokens() -> dict[str, dict[str, str]]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))

    result: dict[str, dict[str, str]] = {}
    suffix = uuid.uuid4().hex[:6]
    for key, role in (("analyst", UserRole.ANALYST), ("viewer", UserRole.VIEWER), ("admin", UserRole.ADMIN)):
        name = f"b04_{key}_{suffix}"
        service.register_user(UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=role))
        _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
        result[key] = {"Authorization": f"Bearer {token}"}
    return result


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("src.core.config.AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


@pytest.fixture
def executions(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record every real pipeline execution."""
    calls: list[str] = []
    original = Application._execute

    def spy(self, *args, **kwargs):
        calls.append(kwargs.get("input_label", "?"))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Application, "_execute", spy)
    return calls


def _pipeline_run_count() -> int:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    try:
        cursor = conn.get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM pipeline_runs")
        return int(cursor.fetchone()[0])
    finally:
        conn.disconnect()


@pytest.fixture(scope="module")
def processed_dataset(tokens) -> str:
    """A dataset the ANALYST uploaded AND executed."""
    client = TestClient(app)
    dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["analyst"])
    res = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=tokens["analyst"])
    assert res.status_code == 200 and res.json()["success"] is True, res.text
    return dataset_id


# ==========================================================
# VIEWER can never execute
# ==========================================================


@pytest.mark.parametrize("route", READ_ROUTES)
def test_viewer_read_routes_never_execute_unprocessed_dataset(
    client: TestClient, tokens, executions: list[str], route: str
) -> None:
    """The original bug: a cache miss on a view route ran the pipeline."""
    dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["analyst"])
    runs_before = _pipeline_run_count()

    res = client.get(route, params={"dataset_version_id": dataset_id}, headers=tokens["viewer"])

    assert res.status_code == 404
    assert executions == []
    assert _pipeline_run_count() == runs_before


@pytest.mark.parametrize("route", READ_ROUTES)
def test_viewer_cannot_read_another_users_result(
    client: TestClient, tokens, processed_dataset: str, executions: list[str], route: str
) -> None:
    runs_before = _pipeline_run_count()

    res = client.get(route, params={"dataset_version_id": processed_dataset}, headers=tokens["viewer"])

    assert res.status_code == 404
    assert executions == []
    assert _pipeline_run_count() == runs_before


def test_demoted_viewer_cannot_execute_own_dataset_through_views(
    client: TestClient, tokens, executions: list[str]
) -> None:
    """
    Ownership alone does not stop B-04: a user who uploaded as ANALYST and
    was then demoted to VIEWER still owns the dataset. Views must not run it.
    """
    name = f"b04_demoted_{uuid.uuid4().hex[:6]}"
    client.post("/api/auth/register", json={"username": name, "email": f"{name}@example.com", "password": _PASSWORD})
    login = client.post("/api/auth/login", json={"username": name, "password": _PASSWORD}).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    dataset_id = upload_dataset(client, SAMPLE_CSV, headers)

    demote = client.patch(f"/api/admin/users/{login['user']['id']}", json={"role": "VIEWER"}, headers=tokens["admin"])
    assert demote.status_code == 200 and demote.json()["role"] == "VIEWER"
    relogin = client.post("/api/auth/login", json={"username": name, "password": _PASSWORD}).json()
    viewer_headers = {"Authorization": f"Bearer {relogin['access_token']}"}
    runs_before = _pipeline_run_count()

    for route in READ_ROUTES:
        res = client.get(route, params={"dataset_version_id": dataset_id}, headers=viewer_headers)
        assert res.status_code == 404, (route, res.status_code)
    run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=viewer_headers)

    assert run.status_code == 403
    assert executions == []
    assert _pipeline_run_count() == runs_before


def test_viewer_cannot_execute_or_upload(client: TestClient, tokens, executions: list[str]) -> None:
    dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["analyst"])
    runs_before = _pipeline_run_count()

    run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=tokens["viewer"])
    upload = client.post("/api/datasets", files={"file": ("x.csv", SAMPLE_CSV.read_bytes())}, headers=tokens["viewer"])

    assert run.status_code == 403
    assert upload.status_code == 403
    assert executions == []
    assert _pipeline_run_count() == runs_before


def test_shadowed_powerbi_dashboard_handler_is_read_only_too(tokens, executions: list[str]) -> None:
    """
    `dashboard.py` and `powerbi.py` both declare `/powerbi/dashboard`; the
    first-mounted one wins in the real app. Mount the Power BI router alone so
    its own handler is exercised as well.
    """
    isolated = FastAPI()
    register_exception_handlers(isolated)
    isolated.include_router(powerbi_router, prefix="/api")

    client = TestClient(isolated)
    dataset_id = upload_dataset(TestClient(app), SAMPLE_CSV, tokens["analyst"])

    res = client.get("/api/powerbi/dashboard", params={"dataset_version_id": dataset_id}, headers=tokens["viewer"])

    assert res.status_code in (401, 404)
    assert executions == []


# ==========================================================
# Views are read-only for every role
# ==========================================================


@pytest.mark.parametrize("route", READ_ROUTES)
def test_analyst_view_of_unprocessed_dataset_does_not_execute(
    client: TestClient, tokens, executions: list[str], route: str
) -> None:
    dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["analyst"])

    res = client.get(route, params={"dataset_version_id": dataset_id}, headers=tokens["analyst"])

    assert res.status_code == 404
    assert "POST /api/pipeline" in res.json()["error"]
    assert executions == []


# ==========================================================
# ANALYST with PIPELINE_EXECUTE still works
# ==========================================================


def test_analyst_executes_then_views_without_re_executing(client: TestClient, tokens, executions: list[str]) -> None:
    dataset_id = upload_dataset(client, SAMPLE_CSV, tokens["analyst"])

    run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=tokens["analyst"])
    assert run.status_code == 200 and run.json()["success"] is True
    assert len(executions) == 1
    runs_after_execute = _pipeline_run_count()

    for route in READ_ROUTES:
        res = client.get(route, params={"dataset_version_id": dataset_id}, headers=tokens["analyst"])
        assert res.status_code == 200, (route, res.text)

    assert len(executions) == 1
    assert _pipeline_run_count() == runs_after_execute


def test_admin_can_view_analyst_result(client: TestClient, tokens, processed_dataset: str) -> None:
    res = client.get(
        "/api/powerbi/dashboard", params={"dataset_version_id": processed_dataset}, headers=tokens["admin"]
    )
    assert res.status_code == 200
