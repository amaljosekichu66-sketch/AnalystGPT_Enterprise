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

    # The server cannot parse parquet uploads, so the client no longer offers it.
    valid, _ = service.validate_file("dataset.parquet")
    assert valid is False

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


def test_upload_dataset_sends_bytes_not_paths():
    mock_client = MagicMock()
    mock_client.upload_dataset.return_value = {"dataset_version_id": "dsv-9"}

    success, data, err = UploadService(api_client=mock_client).upload_dataset("sales.csv", b"a,b\n1,2\n")

    assert (success, data, err) == (True, {"dataset_version_id": "dsv-9"}, None)
    mock_client.upload_dataset.assert_called_once_with(filename="sales.csv", content=b"a,b\n1,2\n", token=None)


def test_upload_dataset_rejects_unsupported_type_locally():
    mock_client = MagicMock()

    success, _, err = UploadService(api_client=mock_client).upload_dataset("payload.exe", b"MZ")

    assert success is False
    assert "Unsupported file format" in err
    mock_client.upload_dataset.assert_not_called()
