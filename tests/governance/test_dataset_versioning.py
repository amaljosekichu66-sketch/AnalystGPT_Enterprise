"""
Tests for DatasetVersion and ArtifactStore immutability.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pandas as pd
import pytest

from src.governance.governance_service import CleaningGovernanceService
from src.governance.models import DatasetVersion
from src.storage.artifact_store import LocalArtifactStore


@pytest.fixture
def store(tmp_path) -> LocalArtifactStore:
    return LocalArtifactStore(base_dir=tmp_path / "artifacts")


@pytest.fixture
def svc(store) -> CleaningGovernanceService:
    return CleaningGovernanceService(artifact_store=store)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


@pytest.fixture
def csv_file(tmp_path, sample_df) -> Path:
    p = tmp_path / "test_data.csv"
    sample_df.to_csv(p, index=False)
    return p


def test_source_version_creation(svc, csv_file):
    version, raw_df = svc.register_source_dataset(
        file_path_or_bytes=csv_file,
        filename="test_data.csv",
        user_id=42,
    )
    assert isinstance(version, DatasetVersion)
    assert version.is_source is True
    assert len(version.version_id) == 36
    assert version.checksum_sha256 != ""
    assert version.byte_size > 0
    assert len(raw_df) == 3


def test_source_version_is_immutable(svc, csv_file):
    version, _ = svc.register_source_dataset(csv_file, "test_data.csv", user_id=1)
    with pytest.raises((AttributeError, TypeError)):
        version.checksum_sha256 = "tampered"  # type: ignore[misc]


def test_unique_version_ids(svc, csv_file):
    v1, _ = svc.register_source_dataset(csv_file, "test_data.csv", user_id=1)
    v2, _ = svc.register_source_dataset(csv_file, "test_data.csv", user_id=1)
    assert v1.version_id != v2.version_id
