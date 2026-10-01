"""
GET /api/datasets/{id}/analysis (P2-05) and the dashboard's run ids (P2-06).

The profile, chart plan and policy recommendation used to be computed inside
the Streamlit process; the dashboard response dropped ai_job_id.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from tests.fixtures.datasets import upload_dataset

SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "customer_data.csv"
_PASSWORD = "Password123!"


@pytest.fixture(scope="module")
def tokens() -> dict[str, dict[str, str]]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    out = {}
    for key, role in (("owner", UserRole.ANALYST), ("viewer", UserRole.VIEWER)):
        name = f"anal_{key}_{uuid.uuid4().hex[:6]}"
        service.register_user(UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=role))
        _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
        out[key] = {"Authorization": f"Bearer {token}"}
    return out


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


def test_analysis_returns_profile_plan_and_recommendation(client: TestClient, tokens) -> None:
    dataset_id = upload_dataset(client, SAMPLE, tokens["owner"])

    res = client.get(f"/api/datasets/{dataset_id}/analysis", headers=tokens["owner"])

    assert res.status_code == 200
    body = res.json()
    assert body["dataset_version_id"] == dataset_id
    assert body["profile"]["columns"] and body["profile"]["row_count"] > 0
    assert "charts" in body["visualization_plan"]
    assert body["recommended_policy"]
    json.dumps(body)  # plain JSON all the way down


def test_analysis_of_someone_elses_dataset_is_404(client: TestClient, tokens) -> None:
    dataset_id = upload_dataset(client, SAMPLE, tokens["owner"])
    assert client.get(f"/api/datasets/{dataset_id}/analysis", headers=tokens["viewer"]).status_code == 404


def test_dashboard_returns_the_runs_ids(client: TestClient, tokens) -> None:
    dataset_id = upload_dataset(client, SAMPLE, tokens["owner"])
    run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=tokens["owner"]).json()

    dashboard = client.get("/api/powerbi/dashboard", params={"dataset_version_id": dataset_id}, headers=tokens["owner"])

    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["ai_job_id"] == run["ai_job_id"]
    assert body["pipeline_run_id"] == run["pipeline_run_id"]
    assert body["report_id"] == run["report_id"]
