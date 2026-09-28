"""
Regression test: exporting a report by id is owner-only.

`ReportingOrchestrator` verified ownership through
`getattr(application.persistence, "_report_repository", None)` and silently
skipped the check when that attribute was missing. The B-03 fix removed the
shared `application.persistence`, so for a while ANY authenticated user could
download ANY report by id (reproduced: user B -> 200 on user A's report; the
v14.0.0 baseline returned 404). The check now opens its own persistence
session and fails closed.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from tests.fixtures.datasets import run_pipeline_on_file

SAMPLE_CSV = Path("sample_data/customer_data.csv")


@pytest.fixture(scope="module")
def owners() -> dict[str, dict[str, str]]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    headers = {}
    for key in ("a", "b"):
        name = f"export_owner_{key}_{uuid.uuid4().hex[:6]}"
        service.register_user(
            UserCreate(username=name, email=f"{name}@example.com", password="Str0ng-Passw0rd!", role=UserRole.ANALYST)
        )
        _, token, _ = service.login(UserLogin(username=name, password="Str0ng-Passw0rd!"))
        headers[key] = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.fixture(scope="module")
def report_of_a(owners) -> int:
    client = TestClient(app)
    run = run_pipeline_on_file(client, SAMPLE_CSV, owners["a"])
    assert run.status_code == 200 and run.json()["success"] is True
    db = sqlite3.connect(config.SQLITE_DATABASE_PATH)
    try:
        return db.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1").fetchone()[0]
    finally:
        db.close()


@pytest.mark.parametrize("fmt", ["text", "pdf"])
def test_other_user_cannot_export_report_by_id(monkeypatch, owners, report_of_a: int, fmt: str) -> None:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    client = TestClient(app)

    stolen = client.get(f"/api/reports/{report_of_a}/export/{fmt}", headers=owners["b"])
    own = client.get(f"/api/reports/{report_of_a}/export/{fmt}", headers=owners["a"])

    assert stolen.status_code == 404
    assert own.status_code == 200
