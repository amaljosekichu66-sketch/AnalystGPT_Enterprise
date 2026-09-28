"""
Regression tests for Report/PDF Lineage Isolation and Stale Artifact Prevention.

Sprint 14 — Forensic Bug Isolation: Report/PDF Lineage.
"""

from pathlib import Path
from unittest.mock import patch

import httpx
import pandas as pd
import pytest

from src.application.app import Application
from src.application.reporting_orchestrator import ReportingOrchestrator
from src.core.config import (
    DEFAULT_PDF_REPORT_FILENAME,
    DEFAULT_REPORT_FILENAME,
    REPORT_OUTPUT_DIRECTORY,
)
from src.frontend.services.report_service import export_pdf_report, export_text_report
from src.identity.context import UserContext
from src.identity.models import UserRole


@pytest.fixture
def clean_reports_dir(tmp_path):
    """Ensure a simulated historical report exists in reports directory."""
    REPORT_OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    hist_pdf = REPORT_OUTPUT_DIRECTORY / DEFAULT_PDF_REPORT_FILENAME
    hist_txt = REPORT_OUTPUT_DIRECTORY / DEFAULT_REPORT_FILENAME

    # Write synthetic historical markers
    hist_pdf.write_bytes(b"%PDF-1.4 Historical Run #687 Pune Nagpur 394 records")
    hist_txt.write_text("Historical Run #687 Pune Nagpur 394 records", encoding="utf-8")

    yield REPORT_OUTPUT_DIRECTORY


def test_reporting_orchestrator_does_not_leak_stale_disk_artifacts_when_unresolved(clean_reports_dir):
    """
    CRITICAL REGRESSION TEST:
    When no report is resolved in-memory for user_id=None (or unauthenticated request),
    export_pdf_report and export_text_report MUST return success=False and MUST NOT
    return the historical stale files on disk.
    """
    app = Application()
    orchestrator = ReportingOrchestrator(app)

    # Calling export with no pipeline result in memory
    pdf_res = orchestrator.export_pdf_report(user_id=None)
    assert pdf_res["success"] is False, (
        f"CRITICAL BUG: export_pdf_report returned success=True and leaked stale file {pdf_res.get('path')} "
        f"when no report was generated!"
    )
    assert "No generated report" in pdf_res["message"]

    text_res = orchestrator.export_text_report(user_id=None)
    assert text_res["success"] is False, (
        f"CRITICAL BUG: export_text_report returned success=True and leaked stale file {text_res.get('path')} "
        f"when no report was generated!"
    )
    assert "No generated report" in text_res["message"]


def test_report_service_does_not_return_stale_disk_file_in_empty_session(clean_reports_dir):
    """
    CRITICAL REGRESSION TEST:
    When Streamlit session is empty, export_pdf_report() and export_text_report()
    MUST NOT return success=True pointing to historical files on disk.
    """
    # The REST export path is stubbed out explicitly so this regression test
    # asserts on the local fallback deterministically, instead of depending on
    # whether an API server happens to be listening on the developer's machine.
    with (
        patch("streamlit.session_state", {}),
        patch(
            "src.frontend.services.report_service.APIClient",
            side_effect=httpx.ConnectError("API server not running (simulated)"),
        ),
    ):
        pdf_res = export_pdf_report()
        assert (
            pdf_res["success"] is False
        ), f"CRITICAL BUG: Frontend export_pdf_report returned stale file {pdf_res.get('path')} in empty session!"

        text_res = export_text_report()
        assert (
            text_res["success"] is False
        ), f"CRITICAL BUG: Frontend export_text_report returned stale file {text_res.get('path')} in empty session!"


def test_export_pdf_and_text_lineage_matches_active_dataset(tmp_path):
    """
    Test that exporting PDF and TXT for dataset A (1,480 rows) contains dataset A's
    proven identity and does not contain historical dataset B markers.
    """
    # Create dataset A (1,480 unique rows)
    data_a = {
        "ID": list(range(1, 1481)),
        "City": ["Holtsville"] * 1000 + ["Springfield"] * 480,
        "Lead_Status": ["Claim Settled"] * 1480,
    }
    csv_a = tmp_path / "dataset_a.csv"
    pd.DataFrame(data_a).to_csv(csv_a, index=False)

    app = Application()
    user_ctx = UserContext(
        user_id=42,
        username="analyst_42",
        email="analyst_42@example.com",
        role=UserRole.ANALYST,
    )
    res_a = app.run(str(csv_a), user_context=user_ctx)
    assert res_a.success is True

    orchestrator = ReportingOrchestrator(app)
    out_pdf = tmp_path / "export_a.pdf"
    out_txt = tmp_path / "export_a.txt"

    pdf_res = orchestrator.export_pdf_report(user_id=42, output_path=out_pdf)
    assert pdf_res["success"] is True
    assert Path(pdf_res["path"]).exists()

    text_res = orchestrator.export_text_report(user_id=42, output_path=out_txt)
    assert text_res["success"] is True
    assert Path(text_res["path"]).exists()

    txt_content = Path(text_res["path"]).read_text(encoding="utf-8")
    assert "1,480" in txt_content
    assert "Holtsville" in txt_content
    assert "Pune" not in txt_content
    assert "Nagpur" not in txt_content
    assert "394" not in txt_content


def test_api_export_by_report_id_isolation_between_multiple_runs(tmp_path):
    """
    CRITICAL API LINEAGE REGRESSION TEST:
    When a user runs Pipeline Run 1 (Report A, Dallas) and then Pipeline Run 2 (Report B, Miami),
    requesting export explicitly for Report A by report_id MUST yield Report A (Dallas) and
    MUST NOT leak Report B (Miami) or stale files.
    """
    import uuid

    from starlette.testclient import TestClient

    from src.api.dependencies.auth_dependencies import (
        get_user_service,
        set_user_service_instance,
    )
    from src.api.server import app as fastapi_app
    from src.identity.models import UserCreate, UserLogin
    from src.persistence.persistence_manager import PersistenceManager

    set_user_service_instance(None)
    user_service = get_user_service()
    unique_username = f"auditor_{uuid.uuid4().hex[:6]}"
    user = user_service.register_user(
        UserCreate(
            username=unique_username,
            email=f"{unique_username}@corp.local",
            password="Password123!",
            role=UserRole.ANALYST,
        )
    )
    _, token, _ = user_service.login(UserLogin(username=unique_username, password="Password123!"))
    user_id = user.id

    # Dataset A (Dallas)
    df_a = pd.DataFrame(
        {
            "city": ["Dallas", "Dallas", "Austin"],
            "cat": ["Alpha", "Alpha", "Beta"],
        }
    )
    csv_a = tmp_path / "data_a.csv"
    df_a.to_csv(csv_a, index=False)

    # Dataset B (Miami)
    df_b = pd.DataFrame(
        {
            "city": ["Miami", "Orlando", "Tampa"],
            "prod": ["Xenon", "Yttrium", "Zinc"],
        }
    )
    csv_b = tmp_path / "data_b.csv"
    df_b.to_csv(csv_b, index=False)

    client = TestClient(fastapi_app)
    headers = {"Authorization": f"Bearer {token}"}

    # Execute Pipeline A
    res_a = client.post("/api/pipeline", json={"input_path": str(csv_a)}, headers=headers)
    assert res_a.status_code == 200

    from src.database.connection_factory import ConnectionFactory
    from src.database.repositories.report_repository import ReportRepository

    conn = ConnectionFactory.create_connection()
    conn.connect()
    rep_repo = ReportRepository(conn)

    reports_after_a = rep_repo.get_all(user_id=user_id)
    assert len(reports_after_a) >= 1
    report_id_a = reports_after_a[0]["id"]

    # Execute Pipeline B
    res_b = client.post("/api/pipeline", json={"input_path": str(csv_b)}, headers=headers)
    assert res_b.status_code == 200

    reports_after_b = rep_repo.get_all(user_id=user_id)
    report_id_b = [r["id"] for r in reports_after_b if r["id"] != report_id_a][0]

    # Explicitly request Report A text (historical run)
    exp_a_txt = client.get(f"/api/reports/{report_id_a}/export/text", headers=headers)
    assert exp_a_txt.status_code == 200
    assert "Dallas" in exp_a_txt.text, "Report A text export must contain Dallas"
    assert "Miami" not in exp_a_txt.text, "Report A text export must NOT leak Report B (Miami)"

    # Explicitly request Report B text (latest run)
    exp_b_txt = client.get(f"/api/reports/{report_id_b}/export/text", headers=headers)
    assert exp_b_txt.status_code == 200
    assert "Miami" in exp_b_txt.text, "Report B text export must contain Miami"
    assert "Dallas" not in exp_b_txt.text, "Report B text export must NOT leak Report A (Dallas)"

    # Explicitly request Report A PDF
    exp_a_pdf = client.get(f"/api/reports/{report_id_a}/export/pdf", headers=headers)
    assert exp_a_pdf.status_code == 200
    assert exp_a_pdf.content.startswith(b"%PDF-")

    # Explicitly request Report B PDF
    exp_b_pdf = client.get(f"/api/reports/{report_id_b}/export/pdf", headers=headers)
    assert exp_b_pdf.status_code == 200
    assert exp_b_pdf.content.startswith(b"%PDF-")
