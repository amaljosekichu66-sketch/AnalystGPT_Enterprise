"""
Integration and Contract tests for Reports API endpoints.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService


@pytest.fixture
def reports_api_setup():
    conn = ConnectionFactory.create_connection()
    conn.connect()
    schema_mgr = SchemaManager(conn)
    schema_mgr.initialize_schema()

    user_repo = UserRepository(conn)
    user_service = UserService(user_repository=user_repo)

    suffix = uuid.uuid4().hex[:6]
    u1_name = f"rep_analyst_a_{suffix}"
    u2_name = f"rep_analyst_b_{suffix}"

    user_service.register_user(
        UserCreate(username=u1_name, email=f"{u1_name}@example.com", password="Password123!", role=UserRole.ANALYST)
    )
    user_service.register_user(
        UserCreate(username=u2_name, email=f"{u2_name}@example.com", password="Password123!", role=UserRole.ANALYST)
    )

    _, token_a, _ = user_service.login(UserLogin(username=u1_name, password="Password123!"))
    _, token_b, _ = user_service.login(UserLogin(username=u2_name, password="Password123!"))

    client = TestClient(app)
    return {
        "client": client,
        "token_a": token_a,
        "token_b": token_b,
        "sample_csv": "sample_data/customer_data.csv",
    }


def test_get_reports_success_and_contract(reports_api_setup):
    client = reports_api_setup["client"]
    token_a = reports_api_setup["token_a"]
    sample_csv = reports_api_setup["sample_csv"]

    # 1. Execute pipeline
    exec_res = client.post(
        "/api/pipeline",
        json={"input_path": sample_csv},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert exec_res.status_code == 200

    # 2. Fetch reports via /api/reports and /reports
    for endpoint in ("/api/reports", "/reports"):
        res = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert "data" in body
        data = body["data"]
        assert "reports" in data
        assert isinstance(data["reports"], list)
        assert len(data["reports"]) >= 4
        assert "report" in data
        assert data["report"] is not None
        assert "report" in data["report"] or "title" in data["report"]


def test_get_reports_tenant_isolation(reports_api_setup):
    client = reports_api_setup["client"]
    token_a = reports_api_setup["token_a"]
    token_b = reports_api_setup["token_b"]
    sample_csv = reports_api_setup["sample_csv"]

    # User A executes pipeline
    client.post(
        "/api/pipeline",
        json={"input_path": sample_csv},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B requests reports -> returns empty payload
    res_b = client.get(
        "/api/reports",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 200
    body = res_b.json()
    assert body["data"]["report"] is None
    assert body["data"]["reports"] == []


def test_get_reports_unauthenticated_rejected(reports_api_setup):
    client = reports_api_setup["client"]
    res = client.get("/api/reports")
    assert res.status_code in (401, 403)
