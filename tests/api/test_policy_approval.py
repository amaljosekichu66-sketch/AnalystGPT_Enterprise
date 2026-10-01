"""
End-to-end tests for P2-04 (Sprint 15 readiness gate): cleaning policy
selection and approval.

The chosen policy used to be stored in Streamlit session state and ignored:
the pipeline always ran DROP_ROWS, and nothing could approve, modify or
reject a policy.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
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

_PASSWORD = "Password123!"


@pytest.fixture(scope="module")
def tokens() -> dict[str, dict[str, str]]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    out = {}
    for key, role in (("owner", UserRole.ANALYST), ("other", UserRole.ANALYST), ("admin", UserRole.ADMIN)):
        name = f"p204_{key}_{uuid.uuid4().hex[:6]}"
        service.register_user(UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=role))
        _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
        out[key] = {"Authorization": f"Bearer {token}"}
    return out


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


@pytest.fixture
def dataset(client: TestClient, tokens, tmp_path: Path) -> str:
    """40 rows; 10 have a missing value, so DROP_ROWS and a median fill differ."""
    values = [float(i) if i % 4 else None for i in range(40)]
    path = tmp_path / "gaps.csv"
    pd.DataFrame({"id": range(40), "amount": values, "region": ["north", "south"] * 20}).to_csv(path, index=False)
    return upload_dataset(client, path, tokens["owner"])


def _propose(client: TestClient, headers, dataset_id: str, policy: str = "FILL_NUMERIC_MEDIAN"):
    return client.post(
        "/api/governance/policies",
        json={"dataset_version_id": dataset_id, "missing_value_policy": policy},
        headers=headers,
    )


def _run(client: TestClient, headers, dataset_id: str, proposal_id: str | None = None):
    body = {"dataset_version_id": dataset_id}
    if proposal_id:
        body["cleaning_policy_proposal_id"] = proposal_id
    return client.post("/api/pipeline", json=body, headers=headers)


def _lineage(client: TestClient, headers, run_id: int) -> dict:
    res = client.get(f"/api/governance/lineage/run/{run_id}", headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def test_approved_policy_is_applied_and_recorded_in_lineage(client: TestClient, tokens, dataset: str) -> None:
    proposal = _propose(client, tokens["owner"], dataset)
    assert proposal.status_code == 201 and proposal.json()["status"] == "PROPOSED"
    proposal_id = proposal.json()["proposal_id"]

    # Not approved yet: the pipeline refuses it.
    assert _run(client, tokens["owner"], dataset, proposal_id).status_code == 409

    approved = client.post(
        f"/api/governance/policies/{proposal_id}/approve", json={"note": "ok"}, headers=tokens["admin"]
    )
    assert approved.status_code == 200 and approved.json()["status"] == "APPROVED"

    run = _run(client, tokens["owner"], dataset, proposal_id)
    assert run.status_code == 200 and run.json()["success"], run.text
    lineage = _lineage(client, tokens["owner"], run.json()["pipeline_run_id"])

    assert lineage["cleaning_config"]["missing_value_policy"] == "FILL_NUMERIC_MEDIAN"
    assert lineage["cleaning_config"]["proposal_id"] == proposal_id
    assert lineage["cleaning_config"]["approved_by"] is not None
    assert lineage["cleaning_execution"]["rows_removed"] == 0  # filled, not dropped


def test_default_run_still_uses_the_default_policy(client: TestClient, tokens, dataset: str) -> None:
    run = _run(client, tokens["owner"], dataset)
    assert run.status_code == 200
    lineage = _lineage(client, tokens["owner"], run.json()["pipeline_run_id"])
    config_row = lineage["cleaning_config"]
    assert config_row["missing_value_policy"] == "DROP_ROWS" and config_row["proposal_id"] is None
    assert lineage["cleaning_execution"]["rows_removed"] == 10


def test_owner_can_modify_then_reject(client: TestClient, tokens, dataset: str) -> None:
    proposal_id = _propose(client, tokens["owner"], dataset).json()["proposal_id"]

    modified = client.patch(
        f"/api/governance/policies/{proposal_id}",
        json={"missing_value_policy": "PRESERVE_NULLS"},
        headers=tokens["owner"],
    )
    assert modified.status_code == 200 and modified.json()["missing_value_policy"] == "PRESERVE_NULLS"

    rejected = client.post(
        f"/api/governance/policies/{proposal_id}/reject", json={"note": "no"}, headers=tokens["owner"]
    )
    assert rejected.json()["status"] == "REJECTED"
    assert _run(client, tokens["owner"], dataset, proposal_id).status_code == 409
    # A reviewed proposal is final.
    assert client.post(f"/api/governance/policies/{proposal_id}/approve", headers=tokens["admin"]).status_code == 409


def test_other_users_cannot_see_or_review_a_proposal(client: TestClient, tokens, dataset: str) -> None:
    proposal_id = _propose(client, tokens["owner"], dataset).json()["proposal_id"]

    assert client.post(f"/api/governance/policies/{proposal_id}/approve", headers=tokens["other"]).status_code == 404
    listed = client.get("/api/governance/policies", headers=tokens["other"]).json()
    assert proposal_id not in {row["proposal_id"] for row in listed}
    assert _propose(client, tokens["other"], dataset).status_code == 404  # not their dataset


def test_proposal_runs_only_for_its_own_dataset(client: TestClient, tokens, dataset: str, tmp_path: Path) -> None:
    proposal_id = _propose(client, tokens["owner"], dataset).json()["proposal_id"]
    client.post(f"/api/governance/policies/{proposal_id}/approve", headers=tokens["admin"])
    path = tmp_path / "other.csv"
    pd.DataFrame({"x": range(10)}).to_csv(path, index=False)
    other_dataset = upload_dataset(client, path, tokens["owner"])

    assert _run(client, tokens["owner"], other_dataset, proposal_id).status_code == 404


def test_separate_approver_rule(client: TestClient, tokens, dataset: str, monkeypatch) -> None:
    monkeypatch.setattr(config, "GOVERNANCE_REQUIRE_SEPARATE_APPROVER", True)
    proposal_id = _propose(client, tokens["owner"], dataset).json()["proposal_id"]

    assert client.post(f"/api/governance/policies/{proposal_id}/approve", headers=tokens["owner"]).status_code == 403
    assert client.post(f"/api/governance/policies/{proposal_id}/approve", headers=tokens["admin"]).status_code == 200


def test_unknown_policy_name_is_400(client: TestClient, tokens, dataset: str) -> None:
    assert _propose(client, tokens["owner"], dataset, "MAKE_IT_UP").status_code == 400
