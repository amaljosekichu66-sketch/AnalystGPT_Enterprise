"""
Artifact Storage implementation for AnalystGPT Enterprise.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Provides concrete local artifact storage that physically preserves original
uploaded bytes and separately persists cleaned analytical dataset artifacts.
Computes and verifies cryptographic SHA-256 digests.
"""

from __future__ import annotations

import abc
import hashlib
import io
import shutil
from pathlib import Path
from typing import BinaryIO

import pandas as pd
from pandas import DataFrame

from src.core.config import PROJECT_ROOT
from src.core.logger import logger
from src.storage.exceptions import ArtifactStoreError, ChecksumMismatchError


class ArtifactStore(abc.ABC):
    """
    Abstract interface for persisting and reading dataset artifacts.
    """

    @abc.abstractmethod
    def save_raw_artifact(
        self,
        source_path_or_stream: Path | BinaryIO | bytes,
        filename: str,
        version_id: str,
    ) -> tuple[str, str, int]:
        """
        Preserve raw uploaded artifact.
        Returns: (storage_path, checksum_sha256, byte_size)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save_cleaned_dataframe(
        self,
        dataframe: DataFrame,
        version_id: str,
        stem_name: str,
    ) -> tuple[str, str, int]:
        """
        Persist cleaned DataFrame as Parquet analytical artifact.
        Returns: (storage_path, checksum_sha256, byte_size)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def read_raw_artifact(self, storage_path: str) -> bytes:
        """Read raw artifact bytes from storage."""
        raise NotImplementedError

    @abc.abstractmethod
    def read_cleaned_dataframe(self, storage_path: str) -> DataFrame:
        """Read cleaned DataFrame from Parquet storage."""
        raise NotImplementedError

    @abc.abstractmethod
    def verify_checksum(self, storage_path: str, expected_checksum: str) -> bool:
        """Verify checksum of stored artifact."""
        raise NotImplementedError


class LocalArtifactStore(ArtifactStore):
    """
    Local filesystem artifact storage with deterministic sharding by version ID.
    Raw and cleaned artifacts are stored in separate dedicated subdirectories.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (PROJECT_ROOT / "data" / "artifacts")
        self.raw_dir = self.base_dir / "raw"
        self.cleaned_dir = self.base_dir / "cleaned"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        # Strip all directory components to prevent path traversal
        clean_name = Path(filename).name
        # Remove any null bytes or invalid traversal sequences
        clean_name = clean_name.replace("\x00", "").replace("..", "_")
        if not clean_name:
            clean_name = "unnamed_artifact.csv"
        return clean_name

    def _get_raw_path(self, version_id: str, filename: str) -> Path:
        clean_filename = self._sanitize_filename(filename)
        shard = version_id[:2]
        target_dir = (self.raw_dir / shard / version_id).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = (target_dir / clean_filename).resolve()

        # Strict containment verification: target_path must be within raw_dir
        if not target_path.is_relative_to(self.raw_dir.resolve()):
            raise ArtifactStoreError(
                f"Path traversal detected: attempted path '{target_path}' is outside '{self.raw_dir}'"
            )
        return target_path

    def _get_cleaned_path(self, version_id: str, stem_name: str) -> Path:
        clean_stem = self._sanitize_filename(stem_name)
        shard = version_id[:2]
        target_dir = (self.cleaned_dir / shard / version_id).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = (target_dir / f"{clean_stem}_cleaned.parquet").resolve()

        # Strict containment verification: target_path must be within cleaned_dir
        if not target_path.is_relative_to(self.cleaned_dir.resolve()):
            raise ArtifactStoreError(
                f"Path traversal detected: attempted path '{target_path}' is outside '{self.cleaned_dir}'"
            )
        return target_path

    def save_raw_artifact(
        self,
        source_path_or_stream: Path | BinaryIO | bytes,
        filename: str,
        version_id: str,
    ) -> tuple[str, str, int]:
        target_path = self._get_raw_path(version_id, filename)
        hasher = hashlib.sha256()
        byte_size = 0

        try:
            if isinstance(source_path_or_stream, Path):
                with open(source_path_or_stream, "rb") as src, open(target_path, "wb") as dst:
                    for chunk in iter(lambda: src.read(65536), b""):
                        hasher.update(chunk)
                        dst.write(chunk)
                        byte_size += len(chunk)
            elif isinstance(source_path_or_stream, bytes):
                hasher.update(source_path_or_stream)
                byte_size = len(source_path_or_stream)
                target_path.write_bytes(source_path_or_stream)
            elif hasattr(source_path_or_stream, "read"):
                with open(target_path, "wb") as dst:
                    for chunk in iter(lambda: source_path_or_stream.read(65536), b""):
                        hasher.update(chunk)
                        dst.write(chunk)
                        byte_size += len(chunk)
            else:
                raise ArtifactStoreError(f"Unsupported source type: {type(source_path_or_stream)}")

            checksum = hasher.hexdigest()
            logger.info(
                "Persisted raw artifact: path=%s bytes=%d sha256=%s",
                target_path,
                byte_size,
                checksum,
            )
            return str(target_path), checksum, byte_size
        except Exception as exc:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise ArtifactStoreError(f"Failed to persist raw artifact: {exc}") from exc

    def save_cleaned_dataframe(
        self,
        dataframe: DataFrame,
        version_id: str,
        stem_name: str,
    ) -> tuple[str, str, int]:
        target_path = self._get_cleaned_path(version_id, stem_name)
        try:
            dataframe.to_parquet(target_path, index=False)
            hasher = hashlib.sha256()
            with open(target_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            checksum = hasher.hexdigest()
            byte_size = target_path.stat().st_size
            logger.info(
                "Persisted cleaned analytical parquet: path=%s bytes=%d sha256=%s",
                target_path,
                byte_size,
                checksum,
            )
            return str(target_path), checksum, byte_size
        except Exception as exc:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise ArtifactStoreError(f"Failed to persist cleaned dataframe: {exc}") from exc

    def read_raw_artifact(self, storage_path: str) -> bytes:
        p = Path(storage_path)
        if not p.exists():
            raise ArtifactStoreError(f"Artifact not found at path: {storage_path}")
        return p.read_bytes()

    def read_cleaned_dataframe(self, storage_path: str) -> DataFrame:
        p = Path(storage_path)
        if not p.exists():
            raise ArtifactStoreError(f"Cleaned artifact not found at path: {storage_path}")
        return pd.read_parquet(p)

    def verify_checksum(self, storage_path: str, expected_checksum: str) -> bool:
        p = Path(storage_path)
        if not p.exists():
            return False
        hasher = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest() == expected_checksum
