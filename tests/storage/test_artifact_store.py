"""
Unit tests for LocalArtifactStore.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
import pytest

from src.storage.artifact_store import LocalArtifactStore
from src.storage.exceptions import ArtifactStoreError


@pytest.fixture
def store(tmp_path) -> LocalArtifactStore:
    return LocalArtifactStore(base_dir=tmp_path / "artifacts")


def test_save_and_read_raw_bytes(store):
    version_id = str(uuid.uuid4())
    data = b"col1,col2\n1,2\n3,4\n"
    path, checksum, size = store.save_raw_artifact(data, "test.csv", version_id)

    assert Path(path).exists()
    assert size == len(data)
    assert store.read_raw_artifact(path) == data
    assert store.verify_checksum(path, checksum) is True


def test_save_and_read_cleaned_dataframe(store):
    version_id = str(uuid.uuid4())
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    path, checksum, size = store.save_cleaned_dataframe(df, version_id, "data")

    assert Path(path).exists()
    assert path.endswith(".parquet")
    assert store.verify_checksum(path, checksum) is True

    loaded_df = store.read_cleaned_dataframe(path)
    pd.testing.assert_frame_equal(df, loaded_df)


def test_verify_checksum_detects_corruption(store):
    version_id = str(uuid.uuid4())
    data = b"important data"
    path, checksum, _ = store.save_raw_artifact(data, "doc.txt", version_id)

    # Tamper with file
    Path(path).write_bytes(b"tampered content")
    assert store.verify_checksum(path, checksum) is False


def test_raw_and_cleaned_in_separate_directories(store):
    v_raw = str(uuid.uuid4())
    v_clean = str(uuid.uuid4())

    p_raw, _, _ = store.save_raw_artifact(b"raw data", "data.csv", v_raw)
    p_clean, _, _ = store.save_cleaned_dataframe(pd.DataFrame({"x": [1]}), v_clean, "data")

    assert "raw" in p_raw
    assert "cleaned" in p_clean
    assert p_raw != p_clean


def test_path_traversal_filename_sanitized_and_contained(store):
    version_id = str(uuid.uuid4())
    # Attacker tries to write outside the artifact directory using path traversal
    malicious_filename = "../../../etc/passwd"
    path, checksum, _ = store.save_raw_artifact(
        b"safe payload", malicious_filename, version_id
    )

    resolved_path = Path(path)
    assert resolved_path.exists()
    assert resolved_path.is_relative_to(store.raw_dir)
    assert resolved_path.name == "passwd"
    # Ensure it never escaped to root filesystem
    assert str(store.base_dir) in str(resolved_path)


def test_path_traversal_stem_sanitized_and_contained(store):
    version_id = str(uuid.uuid4())
    malicious_stem = "../../malicious"
    df = pd.DataFrame({"col": [1, 2]})
    path, checksum, _ = store.save_cleaned_dataframe(df, version_id, malicious_stem)

    resolved_path = Path(path)
    assert resolved_path.exists()
    assert resolved_path.is_relative_to(store.cleaned_dir)
    assert "malicious_cleaned.parquet" in resolved_path.name
    assert str(store.base_dir) in str(resolved_path)
