"""
Regression tests for SEC-12: exports shared one default file across users.

Reproduced: exports without a report id resolved to the exporter's single
default file (`analystgpt_report.txt` / `.pdf`). Alice's and Bob's exports
returned the same path, and after Bob exported, the file Alice's response
streams from contained Bob's report. Each export now writes its own file,
which is deleted once the response has been sent.
"""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import get_application
from src.api.server import app
from src.application.reporting_orchestrator import ReportingOrchestrator
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from src.reporting.reporting_manager import ReportingManager
from tests.fixtures.datasets import run_pipeline_on_file

ROWS = {"a": 23, "b": 4111}


@pytest.fixture(scope="module")
def users(tmp_path_factory) -> dict[str, dict]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    client = TestClient(app)
    out = {}
    for key, rows in ROWS.items():
        name = f"sec12_{key}_{uuid.uuid4().hex[:6]}"
        user = service.register_user(
            UserCreate(username=name, email=f"{name}@example.com", password="Str0ng-Passw0rd!", role=UserRole.ANALYST)
        )
        _, token, _ = service.login(UserLogin(username=name, password="Str0ng-Passw0rd!"))
        headers = {"Authorization": f"Bearer {token}"}
        csv = tmp_path_factory.mktemp(key) / "data.csv"
        pd.DataFrame({"segment": ["x"] * rows, "amount": range(rows)}).to_csv(csv, index=False)
        assert run_pipeline_on_file(client, csv, headers).json()["success"] is True
        out[key] = {"id": user.id, "headers": headers}
    return out


def _exports_dir() -> Path:
    return Path(config.REPORT_OUTPUT_DIRECTORY) / "exports"


def _mentions_rows(text: str, rows: int) -> bool:
    return str(rows) in text or f"{rows:,}" in text


def test_each_export_gets_its_own_file(users) -> None:
    orchestrator = ReportingOrchestrator(get_application())

    a = orchestrator.export_text_report(user_id=users["a"]["id"])
    a_content = Path(a["path"]).read_text(encoding="utf-8")
    b = orchestrator.export_text_report(user_id=users["b"]["id"])

    assert a["path"] != b["path"]
    assert Path(a["path"]).read_text(encoding="utf-8") == a_content
    assert a["filename"] == config.DEFAULT_REPORT_FILENAME
    for result in (a, b):
        Path(result["path"]).unlink()


@pytest.mark.parametrize(
    "fmt, filename", [("text", config.DEFAULT_REPORT_FILENAME), ("pdf", config.DEFAULT_PDF_REPORT_FILENAME)]
)
def test_export_file_is_removed_after_the_response(users, fmt: str, filename: str) -> None:
    before = set(_exports_dir().glob("*")) if _exports_dir().exists() else set()

    res = TestClient(app).get(f"/api/reports/export/{fmt}", headers=users["a"]["headers"])

    assert res.status_code == 200
    assert filename in res.headers["content-disposition"]
    after = set(_exports_dir().glob("*"))
    assert after <= before, after - before


def test_concurrent_exports_each_receive_their_own_report(users, monkeypatch) -> None:
    """Both exports are written before either response is streamed."""
    barrier = threading.Barrier(2, timeout=60)
    original = ReportingManager.export_text

    def export_then_wait(self, *args, **kwargs):
        path = original(self, *args, **kwargs)
        barrier.wait()
        return path

    monkeypatch.setattr(ReportingManager, "export_text", export_then_wait)

    def fetch(key: str) -> str:
        res = TestClient(app).get("/api/reports/export/text", headers=users[key]["headers"])
        assert res.status_code == 200
        return res.text

    with ThreadPoolExecutor(max_workers=2) as pool:
        body_a, body_b = pool.map(fetch, ["a", "b"])

    assert not barrier.broken
    assert _mentions_rows(body_b, ROWS["b"])
    assert not _mentions_rows(body_a, ROWS["b"])
