"""
Tests for non-destructive CleaningPreviewService.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.governance.models import CleaningConfig, MissingValuePolicy
from src.governance.preview_service import CleaningPreviewService


def test_preview_is_non_destructive():
    df = pd.DataFrame(
        {
            "name": ["Alice", None, "Bob"],
            "age": [20, None, 30],
            "salary": [50000.0, 60000.0, None],
        }
    )
    original_nulls = int(df.isnull().sum().sum())
    original_len = len(df)

    service = CleaningPreviewService()
    config = CleaningConfig(
        config_id="preview-cfg",
        missing_value_policy=MissingValuePolicy.DROP_ROWS,
    )

    result = service.preview(df, config, sample_rows=5)

    # Verify input DataFrame was untouched
    assert int(df.isnull().sum().sum()) == original_nulls
    assert len(df) == original_len

    # Verify preview results calculate expected drop
    assert result.quality_comparison.rows_removed > 0
    assert len(result.preview_sample_cleaned) < len(result.preview_sample_source)


def test_preview_api_requires_dataset_version_id_and_rejects_arbitrary_paths(tmp_path, monkeypatch):
    """
    Regression test: POST /api/governance/preview requires dataset_version_id
    and cannot be tricked with raw filesystem paths.
    """
    from fastapi.testclient import TestClient

    from src.api.dependencies.auth_dependencies import set_user_service_instance
    from src.api.server import app
    from src.database.connection_factory import ConnectionFactory
    from src.database.schema_manager import SchemaManager
    from src.identity.in_memory_user_repository import InMemoryUserRepository
    from src.identity.models import UserCreate, UserLogin, UserRole
    from src.identity.password_hasher import PBKDF2PasswordHasher
    from src.identity.token_revocation import TokenRevocationService
    from src.identity.token_service import TokenService
    from src.identity.user_service import UserService

    db_file = str(tmp_path / "test_preview_sec.db")
    monkeypatch.setattr("src.core.config.SQLITE_DATABASE_PATH", db_file)
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()

    user_service = UserService(
        user_repository=InMemoryUserRepository(),
        password_hasher=PBKDF2PasswordHasher(iterations=1000),
        token_service=TokenService(secret_key="preview-test-secret-key-12345"),
        revocation_service=TokenRevocationService(),
    )
    set_user_service_instance(user_service)

    user_service.register_user(
        UserCreate(
            username="auditor_jane",
            email="jane@test.com",
            password="Password123!",
            role=UserRole.ANALYST,
        )
    )
    _, token, _ = user_service.login(
        UserLogin(username="auditor_jane", password="Password123!")
    )

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Attempt to pass an arbitrary filesystem path (input_path) without dataset_version_id
    res = client.post(
        "/api/governance/preview",
        json={
            "input_path": "/etc/passwd",
            "cleaning_config": {"missing_value_policy": "DROP_ROWS"},
        },
        headers=headers,
    )
    # Pydantic validation error (422) because dataset_version_id is mandatory
    assert res.status_code == 422

    # 2. Attempt with non-existent dataset_version_id -> 404
    res_404 = client.post(
        "/api/governance/preview",
        json={
            "dataset_version_id": "non-existent-uuid-123",
            "cleaning_config": {"missing_value_policy": "DROP_ROWS"},
        },
        headers=headers,
    )
    assert res_404.status_code == 404
