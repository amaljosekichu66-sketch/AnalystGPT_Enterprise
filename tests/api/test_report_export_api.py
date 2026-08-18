"""
Integration tests for Report Export REST Endpoints.

Sprint 14 Phase 5 — Reporting & PDF Export Stabilization.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService


@pytest.fixture
def test_setup(tmp_path):
    conn = ConnectionFactory.create_connection()
    conn.connect()
    schema_mgr = SchemaManager(conn)
    schema_mgr.initialize_schema()

    user_repo = UserRepository(conn)
    user_service = UserService(user_repository=user_repo)

    import uuid
    suffix = uuid.uuid4().hex[:6]
    u1_name = f"analyst_exp_a_{suffix}"
    u2_name = f"analyst_exp_b_{suffix}"

    # Create Analyst A and Analyst B
    u_a = user_service.register_user(
        UserCreate(username=u1_name, email=f"{u1_name}@example.com", password="Password123!", role=UserRole.ANALYST)
    )
    u_b = user_service.register_user(
        UserCreate(username=u2_name, email=f"{u2_name}@example.com", password="Password123!", role=UserRole.ANALYST)
    )

    _, token_a, _ = user_service.login(
        UserLogin(username=u1_name, password="Password123!")
    )
    _, token_b, _ = user_service.login(
        UserLogin(username=u2_name, password="Password123!")
    )

    sample_csv = "sample_data/customer_data.csv"
    client = TestClient(app)

    return {
        "client": client,
        "token_a": token_a,
        "token_b": token_b,
        "user_a": u_a,
        "user_b": u_b,
        "sample_csv": sample_csv,
    }


def test_export_text_and_pdf_endpoints(test_setup):
    client = test_setup["client"]
    token_a = test_setup["token_a"]
    token_b = test_setup["token_b"]
    sample_csv = test_setup["sample_csv"]

    # 1. User A executes pipeline
    res_a = client.post(
        "/api/pipeline",
        json={"input_path": sample_csv},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200

    # 2. User A exports latest text report
    res_text = client.get(
        "/api/reports/export/text",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_text.status_code == 200
    assert "text/plain" in res_text.headers.get("content-type", "")
    assert "attachment" in res_text.headers.get("content-disposition", "")
    assert "EXECUTIVE SUMMARY" in res_text.text

    # 3. User A exports latest PDF report
    res_pdf = client.get(
        "/api/reports/export/pdf",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers.get("content-type", "")
    assert "attachment" in res_pdf.headers.get("content-disposition", "")
    assert res_pdf.content.startswith(b"%PDF-")

    # 4. User B has no report -> returns 404
    res_b_text = client.get(
        "/api/reports/export/text",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b_text.status_code == 404


def test_unauthenticated_export_rejected(test_setup):
    client = test_setup["client"]
    res = client.get("/api/reports/export/text")
    assert res.status_code in (401, 403)

    res_pdf = client.get("/api/reports/export/pdf")
    assert res_pdf.status_code in (401, 403)
