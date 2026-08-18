"""
Resource ownership, cross-user isolation, and IDOR prevention test suite for AnalystGPT Enterprise.
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.application.app import Application
from src.database.repositories.dataset_repository import DatasetRepository
from src.database.repositories.pipeline_run_repository import PipelineRunRepository
from src.database.repositories.report_repository import ReportRepository
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.identity.context import UserContext
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import User, UserCreate, UserLogin, UserRole, UserStatus
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService


@pytest.fixture
def sqlite_test_db():
    """Create a temporary SQLite database initialized with the full schema."""
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test_ownership.db"

    conn = SQLiteConnection(str(db_path))
    conn.connect()

    schema_mgr = SchemaManager(conn)
    schema_mgr.initialize_schema()

    yield conn

    conn.disconnect()
    temp_dir.cleanup()


@pytest.fixture
def test_users(sqlite_test_db: SQLiteConnection):
    """Create two test users in the SQLite database."""
    hasher = PBKDF2PasswordHasher(iterations=10_000)
    user_repo = UserRepository(sqlite_test_db)

    u1 = user_repo.create(
        user_create=UserCreate(
            username="user1",
            email="user1@example.com",
            password="Pass12345!",
            role=UserRole.ANALYST,
        ),
        hashed_password=hasher.hash("Pass12345!"),
    )

    u2 = user_repo.create(
        user_create=UserCreate(
            username="user2",
            email="user2@example.com",
            password="Pass12345!",
            role=UserRole.ANALYST,
        ),
        hashed_password=hasher.hash("Pass12345!"),
    )

    return u1, u2


@pytest.fixture
def sample_csv():
    """Create a temporary sample CSV file for pipeline execution."""
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    )
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "sales": [100.0, 200.0, 150.0, 300.0],
            "category": ["A", "B", "A", "B"],
        }
    )
    df.to_csv(temp_file.name, index=False)
    temp_file.close()

    yield temp_file.name

    Path(temp_file.name).unlink(missing_ok=True)


class TestDatabaseResourceOwnership:
    """Test server-side database repository ownership filtering and IDOR prevention."""

    def test_pipeline_run_ownership_isolation(
        self, sqlite_test_db: SQLiteConnection, test_users
    ) -> None:
        u1, u2 = test_users
        pipeline_repo = PipelineRunRepository(sqlite_test_db)

        # User 1 creates a pipeline run
        run_1_id = pipeline_repo.create(status="SUCCESS", user_id=u1.id)

        # User 2 creates a pipeline run
        run_2_id = pipeline_repo.create(status="SUCCESS", user_id=u2.id)

        # Anonymous creates a pipeline run
        run_anon_id = pipeline_repo.create(status="SUCCESS", user_id=None)
        assert run_anon_id is not None

        # User 1 can retrieve run 1
        run_1_user_1 = pipeline_repo.get_by_id(run_1_id, user_id=u1.id)
        assert run_1_user_1 is not None
        assert run_1_user_1["id"] == run_1_id
        assert run_1_user_1["user_id"] == u1.id

        # IDOR Prevention: User 2 CANNOT retrieve run 1
        run_1_user_2 = pipeline_repo.get_by_id(run_1_id, user_id=u2.id)
        assert run_1_user_2 is None

        # User 2 can retrieve run 2
        run_2_user_2 = pipeline_repo.get_by_id(run_2_id, user_id=u2.id)
        assert run_2_user_2 is not None
        assert run_2_user_2["id"] == run_2_id

        # IDOR Prevention: User 1 CANNOT retrieve run 2
        run_2_user_1 = pipeline_repo.get_by_id(run_2_id, user_id=u1.id)
        assert run_2_user_1 is None

        # User 1 list returns ONLY User 1 records
        user_1_runs = pipeline_repo.get_all(user_id=u1.id)
        assert len(user_1_runs) == 1
        assert user_1_runs[0]["id"] == run_1_id

        # User 2 list returns ONLY User 2 records
        user_2_runs = pipeline_repo.get_all(user_id=u2.id)
        assert len(user_2_runs) == 1
        assert user_2_runs[0]["id"] == run_2_id

        # Unscoped list returns all runs (including anonymous)
        all_runs = pipeline_repo.get_all()
        assert len(all_runs) == 3

        # User 2 attempts to delete User 1's run -> Rejected (no effect)
        pipeline_repo.delete(run_1_id, user_id=u2.id)
        assert pipeline_repo.get_by_id(run_1_id, user_id=u1.id) is not None

        # User 1 deletes User 1's run -> Success
        pipeline_repo.delete(run_1_id, user_id=u1.id)
        assert pipeline_repo.get_by_id(run_1_id, user_id=u1.id) is None

    def test_dataset_ownership_isolation(
        self, sqlite_test_db: SQLiteConnection, test_users
    ) -> None:
        u1, u2 = test_users
        pipeline_repo = PipelineRunRepository(sqlite_test_db)
        dataset_repo = DatasetRepository(sqlite_test_db)

        run_a = pipeline_repo.create(status="SUCCESS", user_id=u1.id)
        run_b = pipeline_repo.create(status="SUCCESS", user_id=u2.id)

        ds_a_id = dataset_repo.create(
            pipeline_run_id=run_a,
            dataset_name="financial_a.csv",
            row_count=100,
            column_count=5,
            user_id=u1.id,
        )

        ds_b_id = dataset_repo.create(
            pipeline_run_id=run_b,
            dataset_name="sales_b.csv",
            row_count=200,
            column_count=8,
            user_id=u2.id,
        )

        # Owner lookup
        assert dataset_repo.get_by_id(ds_a_id, user_id=u1.id) is not None
        assert dataset_repo.get_by_id(ds_b_id, user_id=u2.id) is not None

        # Cross-user IDOR access blocked
        assert dataset_repo.get_by_id(ds_a_id, user_id=u2.id) is None
        assert dataset_repo.get_by_id(ds_b_id, user_id=u1.id) is None

        # Pipeline run association
        assert (
            dataset_repo.get_by_pipeline_run(run_a, user_id=u1.id) is not None
        )
        assert dataset_repo.get_by_pipeline_run(run_a, user_id=u2.id) is None

        # List isolation
        assert len(dataset_repo.get_all(user_id=u1.id)) == 1
        assert len(dataset_repo.get_all(user_id=u2.id)) == 1

    def test_report_ownership_isolation(
        self, sqlite_test_db: SQLiteConnection, test_users
    ) -> None:
        u1, u2 = test_users
        pipeline_repo = PipelineRunRepository(sqlite_test_db)
        report_repo = ReportRepository(sqlite_test_db)

        run_a = pipeline_repo.create(status="SUCCESS", user_id=u1.id)
        run_b = pipeline_repo.create(status="SUCCESS", user_id=u2.id)

        rep_a = report_repo.create(
            run_a, "/reports/report_a.txt", user_id=u1.id
        )
        rep_b = report_repo.create(
            run_b, "/reports/report_b.txt", user_id=u2.id
        )

        # Owner lookup
        assert report_repo.get_by_id(rep_a, user_id=u1.id) is not None
        assert report_repo.get_by_id(rep_b, user_id=u2.id) is not None

        # IDOR lookup blocked
        assert report_repo.get_by_id(rep_a, user_id=u2.id) is None
        assert report_repo.get_by_id(rep_b, user_id=u1.id) is None

        # Latest report isolation
        latest_a = report_repo.get_latest_report(user_id=u1.id)
        assert latest_a is not None
        assert latest_a["id"] == rep_a

        latest_b = report_repo.get_latest_report(user_id=u2.id)
        assert latest_b is not None
        assert latest_b["id"] == rep_b

        # Cross-user deletion protection
        report_repo.delete(rep_a, user_id=u2.id)
        assert report_repo.get_by_id(rep_a, user_id=u1.id) is not None

        # Owner deletion
        report_repo.delete(rep_a, user_id=u1.id)
        assert report_repo.get_by_id(rep_a, user_id=u1.id) is None


class TestApplicationCacheIsolation:
    """Test in-memory multi-user cache isolation in Application."""

    def test_multi_user_pipeline_result_isolation(
        self, sample_csv: str
    ) -> None:
        app_instance = Application()
        app_instance.persistence.initialize()
        user_repo = app_instance.persistence.user_repository

        # Ensure user records exist in DB for FK validation
        user_1_entity = user_repo.get_by_id(1)
        if not user_1_entity:
            user_1_entity = user_repo.create(
                UserCreate(
                    username="user_alpha",
                    email="alpha@enterprise.com",
                    password="Password123!",
                    role=UserRole.ANALYST,
                ),
                hashed_password="hash",
            )

        user_2_entity = user_repo.get_by_id(2)
        if not user_2_entity:
            user_2_entity = user_repo.create(
                UserCreate(
                    username="user_beta",
                    email="beta@enterprise.com",
                    password="Password123!",
                    role=UserRole.ANALYST,
                ),
                hashed_password="hash",
            )

        context_user_1 = UserContext.from_user(user_1_entity)
        context_user_2 = UserContext.from_user(user_2_entity)



        # Execute for User 1
        result_1 = app_instance.run(
            input_path=sample_csv,
            user_context=context_user_1,
        )
        assert result_1.success is True

        # User 1 cache contains result_1
        assert app_instance.get_result_for_user(user_id=1) is not None

        # User 2 cache has NOT run yet and is None
        assert app_instance.get_result_for_user(user_id=2) is None


        # User 3 cache is None
        assert app_instance.get_result_for_user(user_id=3) is None

        # Execute for User 2
        result_2 = app_instance.run(
            input_path=sample_csv,
            user_context=context_user_2,
        )
        assert result_2.success is True

        # Both have independent cached results
        assert app_instance.get_result_for_user(user_id=1) is not None
        assert app_instance.get_result_for_user(user_id=2) is not None
        assert app_instance.get_result_for_user(user_id=999) is None

        # Clear cache for User 1 only
        app_instance.clear_cache(user_id=1)
        assert app_instance.get_result_for_user(user_id=1) is None
        assert app_instance.get_result_for_user(user_id=2) is not None


class TestAPIDataIsolation:
    """Test API endpoint data isolation and token-driven UserContext."""

    def test_api_reports_user_scoped(
        self, sample_csv: str
    ) -> None:
        user_repo = InMemoryUserRepository()
        hasher = PBKDF2PasswordHasher(iterations=10_000)
        token_service = TokenService(secret_key="test-secret-key-32-bytes-long!!")
        revocation = TokenRevocationService()
        user_service = UserService(user_repo, hasher, token_service, revocation)

        set_user_service_instance(user_service)

        # Register User A and User B
        user_a = user_service.register_user(
            UserCreate(
                username="analyst_a",
                email="a@enterprise.com",
                password="Password123!",
                role=UserRole.ANALYST,
            )
        )
        assert user_a.id is not None

        user_b = user_service.register_user(
            UserCreate(
                username="analyst_b",
                email="b@enterprise.com",
                password="Password123!",
                role=UserRole.ANALYST,
            )
        )
        assert user_b.id is not None

        _, token_a, _ = user_service.login(
            UserLogin(username="analyst_a", password="Password123!")
        )
        _, token_b, _ = user_service.login(
            UserLogin(username="analyst_b", password="Password123!")
        )

        client = TestClient(app)

        # User A executes pipeline
        res_a = client.post(
            "/api/pipeline",
            json={"input_path": sample_csv},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 200

        # User A calls /reports -> gets reports
        rep_res_a = client.get(
            "/reports",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert rep_res_a.status_code == 200
        assert rep_res_a.json()["data"]["report"] is not None

        # User B calls /reports -> gets None (User B has not executed pipeline)
        rep_res_b = client.get(
            "/reports",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert rep_res_b.status_code == 200
        assert rep_res_b.json()["data"]["report"] is None
