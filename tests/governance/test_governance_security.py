"""
Security tests for governance entities — IDOR isolation and scoping.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import uuid
import pytest

from src.database.repositories.cleaning_config_repository import CleaningConfigRepository
from src.database.repositories.cleaning_execution_repository import CleaningExecutionRepository
from src.database.repositories.dataset_version_repository import DatasetVersionRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.governance.models import (
    CleaningConfig,
    CleaningExecution,
    DatasetVersion,
    ExecutionStatus,
    MissingValuePolicy,
)


@pytest.fixture
def db_connection():
    conn = SQLiteConnection(":memory:")
    conn.connect()
    sm = SchemaManager(conn)
    sm.initialize_schema()
    # Insert test users for FK validation
    cursor = conn.get_connection().cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, username, email, hashed_password) VALUES (1, 'u1', 'u1@test.com', 'pwd');")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, email, hashed_password) VALUES (2, 'u2', 'u2@test.com', 'pwd');")
    conn.commit()
    cursor.close()
    yield conn
    conn.disconnect()



@pytest.fixture
def dv_repo(db_connection) -> DatasetVersionRepository:
    return DatasetVersionRepository(db_connection)


@pytest.fixture
def cc_repo(db_connection) -> CleaningConfigRepository:
    return CleaningConfigRepository(db_connection)


@pytest.fixture
def ce_repo(db_connection) -> CleaningExecutionRepository:
    return CleaningExecutionRepository(db_connection)


def test_dataset_version_idor_isolation(dv_repo):
    v1 = DatasetVersion(
        version_id=str(uuid.uuid4()),
        source_filename="u1.csv",
        byte_size=100,
        checksum_sha256="abc",
        row_count=10,
        column_count=2,
        storage_path="/path/u1.csv",
        user_id=1,
    )
    dv_repo.create(v1)

    assert dv_repo.get_by_version_id(v1.version_id, user_id=2) is None
    assert dv_repo.get_by_version_id(v1.version_id, user_id=1) is not None


def test_cleaning_execution_idor_isolation(dv_repo, cc_repo, ce_repo):
    # First create valid parent dataset_version and cleaning_config
    src_v = DatasetVersion(
        version_id=str(uuid.uuid4()),
        source_filename="src.csv",
        byte_size=100,
        checksum_sha256="abc",
        row_count=10,
        column_count=2,
        storage_path="/path/src.csv",
        user_id=1,
    )
    dv_repo.create(src_v)

    cfg = CleaningConfig(
        config_id=str(uuid.uuid4()),
        missing_value_policy=MissingValuePolicy.DROP_ROWS,
        user_id=1,
    )
    cc_repo.create(cfg)

    e1 = CleaningExecution(
        execution_id=str(uuid.uuid4()),
        source_version_id=src_v.version_id,
        config_id=cfg.config_id,
        execution_status=ExecutionStatus.SUCCESS,
        source_row_count=50,
        user_id=1,
    )
    ce_repo.create(e1)

    assert ce_repo.get_by_execution_id(e1.execution_id, user_id=2) is None
    assert ce_repo.get_by_execution_id(e1.execution_id, user_id=1) is not None
