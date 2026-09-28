"""
API integration test suite for AI endpoints (/api/ai/*).

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.ai.ai_report import AIReport
from src.ai.models import AIFailureCategory, AIJobStatus
from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.schema_manager import SchemaManager
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService


@pytest.fixture
def ai_test_setup(tmp_path, monkeypatch):
    """
    Setup isolated database, user service, and FastAPI test client.
    """
    # Setup DB
    db_file = str(tmp_path / "test_api_ai.db")
    monkeypatch.setattr("src.core.config.SQLITE_DATABASE_PATH", db_file)
    connection = ConnectionFactory.create_connection()
    connection.connect()
    schema = SchemaManager(connection)
    schema.initialize_schema()

    # Setup User Service
    repo = InMemoryUserRepository()
    hasher = PBKDF2PasswordHasher(iterations=10_000)
    token_svc = TokenService(secret_key="test-api-ai-secret-key-12345")
    revocation_svc = TokenRevocationService()
    user_service = UserService(
        user_repository=repo,
        password_hasher=hasher,
        token_service=token_svc,
        revocation_service=revocation_svc,
    )

    # Register users
    user1 = user_service.register_user(
        UserCreate(
            username="analyst_alice",
            email="alice@enterprise.com",
            password="Password123!",
            role=UserRole.ANALYST,
        )
    )
    user2 = user_service.register_user(
        UserCreate(
            username="analyst_bob",
            email="bob@enterprise.com",
            password="Password123!",
            role=UserRole.ANALYST,
        )
    )
    admin = user_service.register_user(
        UserCreate(
            username="admin_carol",
            email="carol@enterprise.com",
            password="Password123!",
            role=UserRole.ADMIN,
        )
    )

    _, token1, _ = user_service.login(UserLogin(username="analyst_alice", password="Password123!"))
    _, token2, _ = user_service.login(UserLogin(username="analyst_bob", password="Password123!"))
    _, admin_token, _ = user_service.login(UserLogin(username="admin_carol", password="Password123!"))

    conn_raw = connection.get_connection()
    conn_raw.execute(
        "INSERT INTO users (id, username, email, hashed_password, role, status) VALUES (?, ?, ?, ?, ?, 'ACTIVE');",
        (user1.id, user1.username, user1.email, "hash1", user1.role.value),
    )
    conn_raw.execute(
        "INSERT INTO users (id, username, email, hashed_password, role, status) VALUES (?, ?, ?, ?, ?, 'ACTIVE');",
        (user2.id, user2.username, user2.email, "hash2", user2.role.value),
    )
    conn_raw.execute(
        "INSERT INTO users (id, username, email, hashed_password, role, status) VALUES (?, ?, ?, ?, ?, 'ACTIVE');",
        (admin.id, admin.username, admin.email, "hash3", admin.role.value),
    )
    connection.commit()

    set_user_service_instance(user_service)
    client = TestClient(app)

    yield {
        "client": client,
        "connection": connection,
        "user1": user1,
        "token1": token1,
        "user2": user2,
        "token2": token2,
        "admin": admin,
        "admin_token": admin_token,
    }

    set_user_service_instance(None)
    connection.close()


def test_get_ai_job_requires_auth(ai_test_setup) -> None:
    """
    GET /api/ai/jobs/{job_id} requires authentication.
    """
    client = ai_test_setup["client"]
    response = client.get("/api/ai/jobs/non_existent_job")
    assert response.status_code == 401


def test_get_ai_job_lifecycle_and_scoping(ai_test_setup) -> None:
    """
    Verify retrieval of job and report with user ownership scoping.
    """
    client = ai_test_setup["client"]
    conn = ai_test_setup["connection"]
    user1 = ai_test_setup["user1"]
    token1 = ai_test_setup["token1"]
    token2 = ai_test_setup["token2"]
    admin_token = ai_test_setup["admin_token"]

    # Insert pipeline run and job for user1
    conn.get_connection().execute(f"INSERT INTO pipeline_runs (user_id, status) VALUES ({user1.id}, 'SUCCESS');")
    conn.commit()

    job_repo = AIJobRepository(conn)
    report_repo = AIReportRepository(conn)

    job_repo.create_job(
        job_id="job_alice_001",
        pipeline_run_id=1,
        user_id=user1.id,
    )
    job_repo.claim_next_pending_job()
    job_repo.mark_ready("job_alice_001")

    report_repo.save_ai_report(
        job_id="job_alice_001",
        pipeline_run_id=1,
        user_id=user1.id,
        ai_report=AIReport(
            executive_summary="Executive summary for Alice.",
            recommendations=["Rec A", "Rec B"],
            explanations=["Expl A"],
            narrative="Narrative Alice.",
            model="gemma3:4b",
            provider="ollama",
            execution_time=1.2,
            prompt_count=1,
        ),
    )

    # 1. Owner (Alice) fetches job
    res1 = client.get(
        "/api/ai/jobs/job_alice_001",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["job_id"] == "job_alice_001"
    assert data1["status"] == "READY"
    assert data1["ai_report"] is not None
    assert data1["ai_report"]["executive_summary"] == "Executive summary for Alice."

    # 2. Non-owner (Bob) attempts to fetch Alice's job -> 404 (scoped isolation)
    res2 = client.get(
        "/api/ai/jobs/job_alice_001",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res2.status_code == 404

    # 3. Admin (Carol) fetches job -> 200 OK
    res_admin = client.get(
        "/api/ai/jobs/job_alice_001",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["job_id"] == "job_alice_001"


def test_get_latest_ai_job_status(ai_test_setup) -> None:
    """
    Verify GET /api/ai/jobs/latest/status returns latest job for authenticated user.
    """
    client = ai_test_setup["client"]
    conn = ai_test_setup["connection"]
    user1 = ai_test_setup["user1"]
    token1 = ai_test_setup["token1"]

    conn.get_connection().execute(f"INSERT INTO pipeline_runs (user_id, status) VALUES ({user1.id}, 'SUCCESS');")
    conn.commit()

    job_repo = AIJobRepository(conn)
    job_repo.create_job(
        job_id="job_alice_latest",
        pipeline_run_id=1,
        user_id=user1.id,
    )

    res = client.get(
        "/api/ai/jobs/latest/status",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == "job_alice_latest"
    assert data["status"] == "PENDING"


def test_retry_ai_job_endpoint(ai_test_setup) -> None:
    """
    Verify POST /api/ai/jobs/{job_id}/retry transitions FAILED job back to PENDING.
    """
    client = ai_test_setup["client"]
    conn = ai_test_setup["connection"]
    user1 = ai_test_setup["user1"]
    token1 = ai_test_setup["token1"]

    conn.get_connection().execute(f"INSERT INTO pipeline_runs (user_id, status) VALUES ({user1.id}, 'SUCCESS');")
    conn.commit()

    job_repo = AIJobRepository(conn)
    job_repo.create_job(
        job_id="job_alice_failed",
        pipeline_run_id=1,
        user_id=user1.id,
    )
    job_repo.claim_next_pending_job()
    job_repo.mark_failed(
        "job_alice_failed",
        error="Provider timeout",
        failure_category=AIFailureCategory.TIMEOUT,
    )

    # Retry the failed job
    res = client.post(
        "/api/ai/jobs/job_alice_failed/retry",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "PENDING"
    assert data["job_id"] == "job_alice_failed"

    # Verify attempting to retry a PENDING or non-FAILED job returns 400
    res_invalid = client.post(
        "/api/ai/jobs/job_alice_failed/retry",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_invalid.status_code == 400
