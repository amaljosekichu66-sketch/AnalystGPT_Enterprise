"""
Multi-user tenant isolation tests for AI Data Context & Async Job Retrieval.

Sprint 14 Phase 4 — AI Data Context & Analytical Integrity.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.ai.context_builder import AIDataContextBuilder
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.repositories.cleaning_execution_repository import CleaningExecutionRepository
from src.database.repositories.dataset_version_repository import DatasetVersionRepository
from src.database.repositories.pipeline_run_repository import PipelineRunRepository
from src.database.repositories.report_repository import ReportRepository
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.governance.models import CleaningExecution, DatasetVersion, ExecutionStatus
from src.identity.models import UserCreate, UserRole


@pytest.fixture
def isolated_db():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test_ai_isolation.db"
    conn = SQLiteConnection(str(db_path))
    conn.connect()

    schema_manager = SchemaManager(conn)
    schema_manager.initialize_schema()

    # Seed User 1 and User 2
    user_repo = UserRepository(conn)
    user_1 = user_repo.create(
        UserCreate(username="user1", email="u1@test.com", password="Password123!", role=UserRole.ANALYST),
        hashed_password="hash",
    )
    user_2 = user_repo.create(
        UserCreate(username="user2", email="u2@test.com", password="Password123!", role=UserRole.ANALYST),
        hashed_password="hash",
    )

    yield conn, user_1, user_2
    conn.disconnect()
    temp_dir.cleanup()


def test_ai_context_builder_ownership_isolation(isolated_db):
    """Verify AIDataContextBuilder blocks cross-user context reconstruction."""
    conn, user_1, user_2 = isolated_db

    # Create Pipeline Run for User 1
    pipeline_repo = PipelineRunRepository(conn)
    run_1_id = pipeline_repo.create(status="SUCCESS", user_id=user_1.id)

    # Create Governance entities for User 1
    version_repo = DatasetVersionRepository(conn)
    version_repo.create(
        DatasetVersion(
            version_id="src-u1",
            source_filename="u1_data.csv",
            byte_size=100,
            checksum_sha256="sha1",
            row_count=50,
            column_count=2,
            storage_path="/path/1",
            is_source=True,
            user_id=user_1.id,
        )
    )
    version_repo.create(
        DatasetVersion(
            version_id="cln-u1",
            source_filename="u1_data_cleaned.parquet",
            byte_size=100,
            checksum_sha256="sha2",
            row_count=45,
            column_count=2,
            storage_path="/path/2",
            is_source=False,
            user_id=user_1.id,
            parent_version_id="src-u1",
        )
    )

    from src.database.repositories.cleaning_config_repository import CleaningConfigRepository
    from src.governance.models import CleaningConfig, MissingValuePolicy

    cfg_repo = CleaningConfigRepository(conn)
    cfg_repo.create(
        CleaningConfig(
            config_id="cfg-u1",
            missing_value_policy=MissingValuePolicy.DROP_ROWS,
            user_id=user_1.id,
        )
    )

    exec_repo = CleaningExecutionRepository(conn)
    exec_repo.create(
        CleaningExecution(
            execution_id="exec-u1",
            pipeline_run_id=run_1_id,
            user_id=user_1.id,
            source_version_id="src-u1",
            cleaned_version_id="cln-u1",
            config_id="cfg-u1",
            execution_status=ExecutionStatus.SUCCESS,
            source_row_count=50,
            cleaned_row_count=45,
            rows_removed=5,
            pct_rows_removed=10.0,
        )
    )

    # 1. User 1 successfully builds their own context
    ctx_u1 = AIDataContextBuilder.build_from_database(
        connection=conn,
        pipeline_run_id=run_1_id,
        user_id=user_1.id,
    )
    assert ctx_u1 is not None
    assert ctx_u1.source.row_count == 50
    assert ctx_u1.cleaning.rows_removed == 5
    assert ctx_u1.lineage.source_version_id == "src-u1"

    # 2. Case A: requested user_id != resource owner -> denied
    ctx_u2 = AIDataContextBuilder.build_from_database(
        connection=conn,
        pipeline_run_id=run_1_id,
        user_id=user_2.id,
    )
    assert ctx_u2 is None

    # 3. Create Pipeline Run with NULL owner (e.g. legacy/unowned system run)
    run_null_id = pipeline_repo.create(status="SUCCESS", user_id=None)
    version_repo.create(
        DatasetVersion(
            version_id="src-null",
            source_filename="null_data.csv",
            byte_size=100,
            checksum_sha256="sha_null",
            row_count=30,
            column_count=2,
            storage_path="/path/null",
            is_source=True,
            user_id=None,
        )
    )
    cfg_repo.create(
        CleaningConfig(
            config_id="cfg-null",
            missing_value_policy=MissingValuePolicy.DROP_ROWS,
            user_id=None,
        )
    )
    exec_repo.create(
        CleaningExecution(
            execution_id="exec-null",
            pipeline_run_id=run_null_id,
            user_id=None,
            source_version_id="src-null",
            config_id="cfg-null",
            execution_status=ExecutionStatus.SUCCESS,
            source_row_count=30,
            cleaned_row_count=30,
        )
    )

    # Case B: requested user_id + resource owner NULL -> denied (cannot claim unowned resource)
    ctx_null_requested = AIDataContextBuilder.build_from_database(
        connection=conn,
        pipeline_run_id=run_null_id,
        user_id=user_1.id,
    )
    assert ctx_null_requested is None

    # Case C: user_id omitted for legitimate system/internal operation -> allowed
    ctx_system = AIDataContextBuilder.build_from_database(
        connection=conn,
        pipeline_run_id=run_null_id,
        user_id=None,
    )
    assert ctx_system is not None
    assert ctx_system.source.row_count == 30


def test_ai_report_provenance_persistence_and_scoping(isolated_db):
    """Verify AIReportRepository stores and scopes provenance metadata."""
    conn, user_1, user_2 = isolated_db

    pipeline_repo = PipelineRunRepository(conn)
    run_1_id = pipeline_repo.create(status="SUCCESS", user_id=user_1.id)

    job_repo = AIJobRepository(conn)
    job = job_repo.create_job(
        job_id="job-prov-1",
        pipeline_run_id=run_1_id,
        user_id=user_1.id,
    )

    from src.ai.ai_report import AIReport

    report = AIReport(
        executive_summary="Summary",
        recommendations=["Rec 1"],
        explanations=["Exp 1"],
        narrative="Narrative text",
        model="gemma3:4b",
        provider="ollama",
        execution_time=1.23,
    )

    report_repo = AIReportRepository(conn)
    report_repo.save_ai_report(
        job_id=job.job_id,
        pipeline_run_id=run_1_id,
        ai_report=report,
        user_id=user_1.id,
        source_version_id="src-v-1",
        cleaned_version_id="cln-v-1",
        cleaning_execution_id="exec-v-1",
        context_version="v1.0",
    )

    # User 1 can retrieve it and provenance matches
    saved_u1 = report_repo.get_by_job_id(job.job_id, user_id=user_1.id)
    assert saved_u1 is not None
    assert saved_u1["source_version_id"] == "src-v-1"
    assert saved_u1["cleaned_version_id"] == "cln-v-1"
    assert saved_u1["cleaning_execution_id"] == "exec-v-1"
    assert saved_u1["context_version"] == "v1.0"

    # User 2 cannot retrieve User 1's report
    saved_u2 = report_repo.get_by_job_id(job.job_id, user_id=user_2.id)
    assert saved_u2 is None
