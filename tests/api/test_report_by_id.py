"""
Regression tests for P2-03 (Sprint 15 readiness gate).

On a by-id cache miss (after a restart, for example) export by id fell back
to the user's LATEST result: /api/reports/1/export/pdf returned run 2's
content. Text export by id served the plain run file without AI or lineage,
and /api/reports returned no report id, so the UI could only export "latest".
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import get_application
from src.api.server import app
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from tests.fixtures.datasets import upload_dataset

_PASSWORD = "Password123!"


@pytest.fixture(scope="module")
def headers() -> dict[str, str]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"p203_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=UserRole.ANALYST)
    )
    _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


def _run(client: TestClient, headers, tmp_path: Path, marker: str) -> dict:
    path = tmp_path / f"{marker}.csv"
    pd.DataFrame({f"{marker}_metric": range(1, 41), "region": ["north", "south"] * 20}).to_csv(path, index=False)
    dataset_id = upload_dataset(client, path, headers)
    res = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=headers)
    assert res.status_code == 200 and res.json()["success"], res.text
    return res.json()


@pytest.fixture
def two_runs(client: TestClient, headers, tmp_path: Path):
    first = _run(client, headers, tmp_path, "alphaonly")
    second = _run(client, headers, tmp_path, "betaonly")
    return first, second


def _evict_report_cache() -> None:
    application = get_application()
    with application._cache_lock:
        for report_id in list(application._report_pipeline_results):
            del application._report_pipeline_results[report_id]


def test_reports_listing_returns_the_report_id(client: TestClient, headers, two_runs) -> None:
    _, second = two_runs
    data = client.get("/api/reports", headers=headers).json()["data"]
    assert second["report_id"] is not None
    assert data["report_id"] == second["report_id"]


@pytest.mark.parametrize("fmt", ["text", "pdf"])
def test_export_by_id_after_cache_eviction_is_the_right_report(client: TestClient, headers, two_runs, fmt) -> None:
    first, _ = two_runs
    _evict_report_cache()

    res = client.get(f"/api/reports/{first['report_id']}/export/{fmt}", headers=headers)

    assert res.status_code == 200
    if fmt == "text":
        assert "alphaonly_metric" in res.text
        assert "betaonly_metric" not in res.text
    else:
        assert res.content.startswith(b"%PDF-")


def test_unrecoverable_report_is_404_not_another_report(client: TestClient, headers, two_runs) -> None:
    first, _ = two_runs
    _evict_report_cache()
    conn = ConnectionFactory.create_connection()
    conn.connect()
    conn.get_connection().execute("UPDATE ai_jobs SET report_payload = NULL WHERE report_id = ?", (first["report_id"],))
    conn.commit()
    conn.disconnect()

    res = client.get(f"/api/reports/{first['report_id']}/export/pdf", headers=headers)

    assert res.status_code == 404


def test_resolved_report_for_an_evicted_id_is_that_runs_report(client: TestClient, headers, two_runs) -> None:
    from src.application.reporting_orchestrator import ReportingOrchestrator

    first, _ = two_runs
    _evict_report_cache()
    user_id = client.get("/api/auth/me", headers=headers).json()["id"]

    report, _, lineage = ReportingOrchestrator(get_application())._resolve_context_and_report(
        user_id=user_id, report_id=first["report_id"]
    )

    assert report is not None
    assert "alphaonly_metric" in str(report.to_dict()) and "betaonly_metric" not in str(report.to_dict())
    assert lineage["pipeline_run_id"] == first["pipeline_run_id"]
