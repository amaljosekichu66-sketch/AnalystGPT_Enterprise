"""
Upload Service for AnalystGPT Enterprise Frontend.

Provides a technology-neutral service interface for dataset ingestion,
file validation, cleaning previews, and pipeline execution triggers.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.frontend.services.api_client import APIClient


class UploadService:
    """
    Technology-neutral frontend service for dataset upload and pipeline triggers.
    """

    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet", ".json"}
    MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

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

    def preview_cleaning(
        self,
        dataset_version_id: str,
        missing_value_policy: str = "DROP_ROWS",
        outlier_policy: str = "FLAG_ONLY",
        token: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Simulate data cleaning transformations non-destructively.
        """
        try:
            res = self._api_client._request(
                "POST",
                "/api/governance/preview",
                json={
                    "dataset_version_id": dataset_version_id,
                    "cleaning_config": {
                        "missing_value_policy": missing_value_policy,
                        "outlier_policy": outlier_policy,
                    },
                },
                token=token,
            )
            return True, res, None
        except Exception as exc:
            return False, None, str(exc)

    def execute_pipeline(
        self,
        input_path: str,
        token: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Trigger analytics pipeline execution.
        """
        try:
            res = self._api_client._request(
                "POST",
                "/api/pipeline",
                json={"input_path": input_path},
                token=token,
            )
            if res.get("success"):
                return True, res, None
            return False, None, res.get("message") or res.get("error", "Pipeline execution failed.")
        except Exception as exc:
            return False, None, str(exc)
