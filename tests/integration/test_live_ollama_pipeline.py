"""
P2-24: the full product path against a LIVE Ollama model.

AI jobs had only ever been exercised against a closed port. This drives the
real API with sample_data/support_tickets.xlsx (synthetic, seeded, tracked;
see scripts/make_live_sample.py): upload -> pipeline -> background AI job ->
live gemma3:4b generation -> structured report persisted -> READY -> report
and PDF export.

Deselected by default (`integration`) and skipped when no Ollama with the
configured model answers. Run, and keep the log:

    pytest -m integration -v tests/ai/test_ollama_connection.py \\
        tests/ai/test_ollama_production_path.py tests/integration/test_live_ollama_pipeline.py
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from src.core import config

pytestmark = pytest.mark.integration

SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "support_tickets.xlsx"


def _model_available() -> bool:
    try:
        tags = httpx.get(f"{config.OLLAMA_HOST.rstrip('/')}/api/tags", timeout=5).json()
    except Exception:
        return False
    return any(m.get("name") == config.OLLAMA_MODEL for m in tags.get("models", []))


if not _model_available():
    pytest.skip(f"Ollama at {config.OLLAMA_HOST} with {config.OLLAMA_MODEL} is not available", allow_module_level=True)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.api.server import app

    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


@pytest.fixture
def analyst() -> dict[str, str]:
    from src.database.connection_factory import ConnectionFactory
    from src.database.repositories.user_repository import UserRepository
    from src.database.schema_manager import SchemaManager
    from src.identity.models import UserCreate, UserLogin, UserRole
    from src.identity.user_service import UserService

    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"live_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password="Live-Passw0rd!", role=UserRole.ANALYST)
    )
    _, token, _ = service.login(UserLogin(username=name, password="Live-Passw0rd!"))
    conn.disconnect()
    return {"Authorization": f"Bearer {token}"}


def test_live_generation_end_to_end(client: TestClient, analyst: dict[str, str]) -> None:
    upload = client.post("/api/datasets", files={"file": (SAMPLE.name, SAMPLE.read_bytes())}, headers=analyst)
    assert upload.status_code == 201, upload.text
    dataset_id = upload.json()["dataset_version_id"]

    run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=analyst)
    assert run.status_code == 200 and run.json()["success"], run.text
    job_id, report_id = run.json()["ai_job_id"], run.json()["report_id"]
    print(f"\npipeline_run_id={run.json()['pipeline_run_id']} report_id={report_id} ai_job_id={job_id}")

    started = time.monotonic()
    deadline = started + config.AI_TIMEOUT * max(1, config.AI_MAX_RETRIES) + 60
    status = None
    while time.monotonic() < deadline:
        job = client.get(f"/api/ai/jobs/{job_id}", headers=analyst).json()
        if job["status"] != status:
            status = job["status"]
            print(f"  t+{time.monotonic() - started:6.1f}s  {status}")
        if status in {"READY", "FAILED", "CANCELLED"}:
            break
        time.sleep(5)
    assert status == "READY", job

    report = job["ai_report"]
    print(f"  model={report.get('model')} provider={report.get('provider')}")
    print(f"  executive_summary={len(report['executive_summary'])} chars")
    print(f"  recommendations={len(report['recommendations'])}")
    assert report["model"] == config.OLLAMA_MODEL
    assert len(report["executive_summary"]) > 80
    assert report["recommendations"]
    # Personal data never reaches the model's output.
    assert "@example.com" not in str(report)

    pdf = client.get(f"/api/reports/{report_id}/export/pdf", headers=analyst)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    print(f"  pdf={len(pdf.content)} bytes")
