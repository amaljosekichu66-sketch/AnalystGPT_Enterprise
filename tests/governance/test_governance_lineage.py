"""
Integration tests for governance lineage and dataset version reuse.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
import pytest

from src.governance.governance_service import (
    CleaningGovernanceService,
    GovernedCleaningError,
)
from src.governance.models import (
    CleaningConfig,
    ExecutionStatus,
    MissingValuePolicy,
)
from src.storage.artifact_store import LocalArtifactStore


@pytest.fixture
def store(tmp_path) -> LocalArtifactStore:
    return LocalArtifactStore(base_dir=tmp_path / "artifacts")


@pytest.fixture
def service(store) -> CleaningGovernanceService:
    return CleaningGovernanceService(artifact_store=store)


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    p = tmp_path / "dataset.csv"
    df = pd.DataFrame(
        {
            "name": ["Alice", None, "Bob", "Charlie"],
            "score": [90.0, 80.0, None, 85.0],
            "dept": ["Eng", "Sales", "Eng", None],
        }
    )
    df.to_csv(p, index=False)
    return p


def test_source_dataset_registration(service, sample_csv):
    source_version, raw_df = service.register_source_dataset(
        file_path_or_bytes=sample_csv,
        filename="dataset.csv",
        user_id=1,
    )
    assert source_version.is_source is True
    assert source_version.row_count == 4
    assert source_version.column_count == 3
    assert Path(source_version.storage_path).exists()


def test_governed_cleaning_execution_lineage(service, sample_csv):
    source_version, raw_df = service.register_source_dataset(sample_csv, "dataset.csv", user_id=1)
    config = CleaningConfig(
        config_id=str(uuid.uuid4()),
        missing_value_policy=MissingValuePolicy.FILL_NUMERIC_MEAN,
        user_id=1,
    )

    res = service.execute_governed_cleaning(
        raw_df=raw_df,
        source_version=source_version,
        config=config,
        pipeline_run_id=101,
        user_id=1,
    )

    # Validate output
    assert res.execution.execution_status == ExecutionStatus.SUCCESS
    assert res.cleaned_version.is_source is False
    assert res.cleaned_version.parent_version_id == source_version.version_id
    assert res.execution.source_version_id == source_version.version_id
    assert res.execution.cleaned_version_id == res.cleaned_version.version_id


def test_dataset_version_reuse_across_runs(service, sample_csv):
    source_version, raw_df = service.register_source_dataset(sample_csv, "dataset.csv", user_id=1)

    # Run 1: DROP_ROWS
    cfg1 = CleaningConfig(config_id=str(uuid.uuid4()), missing_value_policy=MissingValuePolicy.DROP_ROWS)
    res1 = service.execute_governed_cleaning(raw_df, source_version, cfg1, pipeline_run_id=1)

    # Run 2: FILL_NUMERIC_MEAN
    cfg2 = CleaningConfig(config_id=str(uuid.uuid4()), missing_value_policy=MissingValuePolicy.FILL_NUMERIC_MEAN)
    res2 = service.execute_governed_cleaning(raw_df, source_version, cfg2, pipeline_run_id=2)

    # Both runs share the exact same source dataset version
    assert res1.source_version.version_id == source_version.version_id
    assert res2.source_version.version_id == source_version.version_id

    # Each produced a distinct cleaned analytical dataset version
    assert res1.cleaned_version.version_id != res2.cleaned_version.version_id
    assert res1.cleaned_version.parent_version_id == source_version.version_id
    assert res2.cleaned_version.parent_version_id == source_version.version_id


def test_end_to_end_governance_persistence_and_lineage_query(tmp_path, sample_csv):
    """
    Proves full lifecycle:
    Source artifact -> Source DatasetVersion DB row -> CleaningConfig DB row
    -> Governed cleaning -> Cleaned analytical Parquet artifact
    -> Cleaned DatasetVersion DB row -> CleaningExecution DB row -> Lineage query.
    """
    from src.application.app import Application
    from src.database.sqlite_connection import SQLiteConnection
    from src.database.schema_manager import SchemaManager

    # Initialize application with live persistence
    app = Application()
    app.persistence.initialize()

    # 1. Execute complete pipeline
    pipeline_result = app.run(str(sample_csv))
    assert pipeline_result.success is True

    # 2. Query persistence repositories
    dv_repo = app.persistence.dataset_version_repository
    cc_repo = app.persistence.cleaning_config_repository
    ce_repo = app.persistence.cleaning_execution_repository

    assert dv_repo is not None
    assert cc_repo is not None
    assert ce_repo is not None

    run_id = app.persistence._pipeline_run_id
    assert run_id is not None

    # Verify CleaningExecution row
    exec_row = ce_repo.get_by_pipeline_run(run_id)
    assert exec_row is not None
    assert exec_row["execution_status"] == "SUCCESS"

    # Verify Source DatasetVersion row & physical artifact
    src_v_id = exec_row["source_version_id"]
    src_v_row = dv_repo.get_by_version_id(src_v_id)
    assert src_v_row is not None
    assert src_v_row["is_source"] == 1
    assert Path(src_v_row["storage_path"]).exists()
    assert app.artifact_store.verify_checksum(
        src_v_row["storage_path"], src_v_row["checksum_sha256"]
    ) is True

    # Verify Cleaned DatasetVersion row & physical artifact
    clean_v_id = exec_row["cleaned_version_id"]
    clean_v_row = dv_repo.get_by_version_id(clean_v_id)
    assert clean_v_row is not None
    assert clean_v_row["is_source"] == 0
    assert clean_v_row["parent_version_id"] == src_v_id
    assert Path(clean_v_row["storage_path"]).exists()
    assert clean_v_row["storage_path"].endswith(".parquet")
    assert app.artifact_store.verify_checksum(
        clean_v_row["storage_path"], clean_v_row["checksum_sha256"]
    ) is True

    # Verify CleaningConfig row
    cfg_id = exec_row["config_id"]
    cfg_row = cc_repo.get_by_config_id(cfg_id)
    assert cfg_row is not None
    assert cfg_row["missing_value_policy"] == "DROP_ROWS"

    # Verify Lineage query reconstructs complete graph
    lineage_executions = ce_repo.get_by_source_version(src_v_id)
    assert len(lineage_executions) >= 1
    assert lineage_executions[0]["cleaned_version_id"] == clean_v_id

    children = dv_repo.get_children(src_v_id)
    assert len(children) >= 1
    assert children[0]["version_id"] == clean_v_id
