"""
Unit tests for Frontend Upload Service.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

from unittest.mock import MagicMock
from src.frontend.services.upload_service import UploadService


def test_validate_file_extensions():
    service = UploadService()

    valid, _ = service.validate_file("data.csv")
    assert valid is True

    valid, _ = service.validate_file("dataset.parquet")
    assert valid is True

    valid, msg = service.validate_file("malicious.exe")
    assert valid is False
    assert "Unsupported file format" in msg


def test_validate_file_size():
    service = UploadService()

    # Below limit (10 MB)
    valid, _ = service.validate_file("data.csv", size_bytes=10 * 1024 * 1024)
    assert valid is True

    # Exceeding limit (600 MB)
    valid, msg = service.validate_file("large.csv", size_bytes=600 * 1024 * 1024)
    assert valid is False
    assert "exceeds maximum allowable limit" in msg


def test_preview_cleaning_delegation():
    mock_client = MagicMock()
    mock_client._request.return_value = {"preview": {"quality_score": 95}}

    service = UploadService(api_client=mock_client)
    success, data, err = service.preview_cleaning(dataset_version_id="dsv_123")

    assert success is True
    assert data == {"preview": {"quality_score": 95}}
    assert err is None


def test_execute_pipeline_delegation():
    mock_client = MagicMock()
    mock_client._request.return_value = {"success": True, "output_path": "report.txt"}

    service = UploadService(api_client=mock_client)
    success, data, err = service.execute_pipeline(input_path="sample.csv")

    assert success is True
    assert data["output_path"] == "report.txt"
    assert err is None
