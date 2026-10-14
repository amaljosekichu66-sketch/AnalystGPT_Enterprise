"""
End-to-end user journey through the real API (P2-21).

This file used to build UploadManager, CleaningManager, QualityManager and
the other managers by hand and chain them. That skipped everything the
product actually does in between: authentication, ownership, governed
cleaning with an approved policy, persistence, lineage, the AI job and the
exports. It now drives the routes a user (through the Streamlit frontend)
reaches, in order, against a real database:

    register (VIEWER) -> admin promotes to ANALYST -> upload -> analysis
    -> propose policy -> admin approves -> pipeline -> dashboard views
    -> lineage -> report list -> text and PDF export by id -> AI job
    -> delete dataset

The LLM is not reached: OLLAMA_HOST points at a closed port in the test
environment, so the AI job ends FAILED with a generic message. Live
generation is covered by `pytest -m integration` (P2-24).
"""

from __future__ import annotations

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

SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "customer_data.csv"
PASSWORD = "Journey-Passw0rd!"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    monkeypatch.setattr(config, "AUTH_SELF_REGISTRATION_ENABLED", True)
    return TestClient(app)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"journey_admin_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password=PASSWORD, role=UserRole.ADMIN)
    )
    _, token, _ = service.login(UserLogin(username=name, password=PASSWORD))
    conn.disconnect()
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, name: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": name, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_complete_user_journey(client: TestClient, admin_headers: dict[str, str]) -> None:
    # --- account: self-registration yields a read-only VIEWER
    name = f"journey_{uuid.uuid4().hex[:6]}"
    reg = client.post(
        "/api/auth/register", json={"username": name, "email": f"{name}@example.com", "password": PASSWORD}
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["id"]
    assert reg.json()["role"] == "VIEWER"
    viewer = _login(client, name)
    assert (
        client.post("/api/datasets", files={"file": (SAMPLE.name, SAMPLE.read_bytes())}, headers=viewer).status_code
        == 403
    )

    # --- an administrator promotes the account; role changes revoke old tokens
    promoted = client.patch(f"/api/admin/users/{user_id}", json={"role": "ANALYST"}, headers=admin_headers)
    assert promoted.status_code == 200, promoted.text
    analyst = _login(client, name)
    assert client.get("/api/auth/me", headers=analyst).json()["role"] == "ANALYST"

    # --- upload and analysis (read-only, nothing runs)
    upload = client.post("/api/datasets", files={"file": (SAMPLE.name, SAMPLE.read_bytes())}, headers=analyst)
    assert upload.status_code == 201, upload.text
    dataset_id = upload.json()["dataset_version_id"]
    analysis = client.get(f"/api/datasets/{dataset_id}/analysis", headers=analyst)
    assert analysis.status_code == 200 and analysis.json()["profile"]["columns"]
    assert (
        client.get("/api/powerbi/dashboard", params={"dataset_version_id": dataset_id}, headers=analyst).status_code
        == 404
    )

    # --- policy: proposed by the analyst, approved by the administrator
    proposal = client.post(
        "/api/governance/policies",
        json={"dataset_version_id": dataset_id, "missing_value_policy": "FILL_NUMERIC_MEDIAN"},
        headers=analyst,
    )
    assert proposal.status_code == 201, proposal.text
    proposal_id = proposal.json()["proposal_id"]
    approve = client.post(f"/api/governance/policies/{proposal_id}/approve", json={"note": "ok"}, headers=admin_headers)
    assert approve.status_code == 200 and approve.json()["status"] == "APPROVED"

    # --- pipeline under the approved policy
    run = client.post(
        "/api/pipeline",
        json={"dataset_version_id": dataset_id, "cleaning_policy_proposal_id": proposal_id},
        headers=analyst,
    )
    assert run.status_code == 200 and run.json()["success"], run.text
    run_id, report_id = run.json()["pipeline_run_id"], run.json()["report_id"]
    assert run_id is not None and report_id is not None

    # --- dashboard and Power BI views now answer, and read the same run
    dashboard = client.get("/api/powerbi/dashboard", params={"dataset_version_id": dataset_id}, headers=analyst)
    assert dashboard.status_code == 200 and dashboard.json()["pipeline_run_id"] == run_id
    for view in ("summary", "statistics", "correlation", "distribution", "categorical", "report", "pipeline"):
        res = client.get(f"/api/powerbi/{view}", params={"dataset_version_id": dataset_id}, headers=analyst)
        assert res.status_code == 200, (view, res.text)

    # --- lineage records the policy and who approved it
    lineage = client.get(f"/api/governance/lineage/run/{run_id}", headers=analyst).json()
    assert lineage["cleaning_config"]["missing_value_policy"] == "FILL_NUMERIC_MEDIAN"
    assert lineage["cleaning_config"]["proposal_id"] == proposal_id
    assert lineage["cleaning_config"]["approved_by"] is not None

    # --- reports: listed, and exported by id in both formats
    latest = client.get("/api/reports", headers=analyst).json()
    assert latest["data"]["report_id"] == report_id
    text = client.get(f"/api/reports/{report_id}/export/text", headers=analyst)
    assert text.status_code == 200 and len(text.content) > 100
    pdf = client.get(f"/api/reports/{report_id}/export/pdf", headers=analyst)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")

    # --- the AI job exists and belongs to this run
    job_id = run.json()["ai_job_id"]
    job = client.get(f"/api/ai/jobs/{job_id}", headers=analyst)
    assert job.status_code == 200 and job.json()["pipeline_run_id"] == run_id

    # --- nobody else sees any of it
    stranger = admin_headers  # an admin is still not the owner for user-scoped reads
    assert client.get(f"/api/reports/{report_id}/export/text", headers=stranger).status_code == 404

    # --- the owner can delete the dataset; it is gone afterwards
    assert client.delete(f"/api/datasets/{dataset_id}", headers=analyst).status_code in (200, 204)
    assert client.get(f"/api/datasets/{dataset_id}/analysis", headers=analyst).status_code == 404
