"""
Upload Service for AnalystGPT Enterprise Frontend.

Provides a technology-neutral service interface for dataset ingestion,
file validation, cleaning previews, and pipeline execution triggers.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core import config
from src.frontend.services.api_client import APIClient


class UploadService:
    """
    Technology-neutral frontend service for dataset upload and pipeline triggers.
    """

    # Mirrors the server allow-list (`src/upload/upload_policy.py`); the
    # server remains the authority.
    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json"}
    MAX_FILE_SIZE_BYTES = config.MAX_FILE_SIZE_MB * 1024 * 1024

    def __init__(self, api_client: APIClient | None = None) -> None:
        self._api_client = api_client or APIClient()

    def validate_file(
        self,
        filename: str,
        size_bytes: int | None = None,
    ) -> tuple[bool, str]:
        """
        Validate file extension and size constraints.
        """
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(self.ALLOWED_EXTENSIONS))
            return False, f"Unsupported file format '{ext}'. Allowed formats: {allowed}"

        if size_bytes is not None and size_bytes > self.MAX_FILE_SIZE_BYTES:
            max_mb = self.MAX_FILE_SIZE_BYTES // (1024 * 1024)
            return False, f"File size exceeds maximum allowable limit of {max_mb} MB."

        return True, "File validation passed."

    def upload_dataset(
        self,
        filename: str,
        content: bytes,
        token: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Upload dataset bytes; the response carries the server-issued `dataset_version_id`.
        """
        ok, message = self.validate_file(filename, size_bytes=len(content))
        if not ok:
            return False, None, message
        try:
            return True, self._api_client.upload_dataset(filename=filename, content=content, token=token), None
        except Exception as exc:
            return False, None, str(exc)
