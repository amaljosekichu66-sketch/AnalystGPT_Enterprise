"""
Unit and component tests for AI Insights Lifecycle States and Structured Fields.

Sprint 14 Remediation & Phase 2 Quality Gate.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.ai.ai_report import AIReport
from src.ai.confidence_evaluator import compute_evidence_confidence
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.frontend.components.ai_insights import _extract_ai_report
from src.frontend.services.ai_service import get_ai_job_status


def test_ai_report_contains_all_structured_enterprise_fields():
    """AIReport object contains structured business fields and serializes to dict cleanly."""
    report = AIReport(
        executive_summary="Summary of operations.",
        recommendations=["Rec 1", "Rec 2"],
        explanations=["Finding 1", "Finding 2"],
        narrative="Complete story.",
        model="gemma3:4b",
        provider="ollama",
        execution_time=1.45,
        key_findings=["Key finding 1"],
        business_implications=["Implication 1"],
        risks=["Risk 1"],
        opportunities=["Opportunity 1"],
        actions=["Action 1"],
        limitations=["Limitation 1"],
        confidence="Medium — Findings are grounded in observed categorical distributions, but the dataset contains no governed numerical measures or outcome variable.",
    )

    data = report.to_dict()
    assert data["executive_summary"] == "Summary of operations."
    assert data["key_findings"] == ["Key finding 1"]
    assert data["business_implications"] == ["Implication 1"]
    assert data["risks"] == ["Risk 1"]
    assert data["opportunities"] == ["Opportunity 1"]
    assert data["actions"] == ["Action 1"]
    assert data["limitations"] == ["Limitation 1"]
    assert "Medium" in data["confidence"]
    assert data["model"] == "gemma3:4b"


def test_evidence_based_confidence_computation():
    """Confidence dynamically adjusts based on governed numerical measures, completeness, and volume."""
    # 1. 0 Numerical measures, categorical dataset -> Medium with exact rationale
    conf_cat = compute_evidence_confidence({
        "descriptive_statistics": {"total_rows": 1480, "numeric_column_count": 0, "categorical_column_count": 10},
    })
    assert "Medium — Findings are grounded in observed categorical distributions" in conf_cat

    # 2. Empty dataset / 0 rows -> Not Assessable
    conf_empty = compute_evidence_confidence({
        "descriptive_statistics": {"total_rows": 0, "numeric_column_count": 0},
    })
    assert "Not Assessable" in conf_empty

    # 3. Small volume (<10 rows) -> Low
    conf_small = compute_evidence_confidence({
        "descriptive_statistics": {"total_rows": 5, "numeric_column_count": 2},
    })
    assert "Low — Sample size is too small" in conf_small

    # 4. Governed numerical measures with correlation analysis & sufficient rows -> High
    conf_high = compute_evidence_confidence({
        "descriptive_statistics": {"total_rows": 200, "numeric_column_count": 3},
        "correlation_analysis": {"correlation_matrix": {"sales": {"price": -0.8}, "price": {"sales": -0.8}}},
    })
    assert "High — Grounded in governed numerical measures" in conf_high


def test_structured_fields_persistence_and_retrieval_without_reclassification():
    """Structured AI report fields survive database persistence and deserialization exactly."""
    db = SQLiteConnection(":memory:")
    db.connect()
    SchemaManager(db).initialize_schema()
    repo = AIReportRepository(db)

    # Create dummy pipeline run and ai job
    raw_conn = db.get_connection()
    cur = raw_conn.cursor()
    cur.execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    run_id = int(cur.lastrowid)
    cur.execute(
        "INSERT INTO ai_jobs (job_id, pipeline_run_id, status) VALUES ('job_audit_1', ?, 'READY');",
        (run_id,),
    )
    raw_conn.commit()
    cur.close()

    ai_report = AIReport(
        executive_summary="Executive interpretation.",
        recommendations=["Action A", "Action B"],
        explanations=["Finding 1", "Finding 2"],
        narrative="Complete story.",
        model="gemma3:4b",
        provider="ollama",
        execution_time=1.23,
        key_findings=["Structured Key Finding 1", "Structured Key Finding 2"],
        business_implications=["Implication A"],
        risks=["Operational Risk 1"],
        opportunities=["Growth Opportunity 1"],
        actions=["Action A", "Action B"],
        limitations=["Domain Boundary 1"],
        confidence="Medium — Findings are grounded in observed categorical distributions, but the dataset contains no governed numerical measures or outcome variable.",
    )

    report_id = repo.save_ai_report(
        job_id="job_audit_1",
        pipeline_run_id=run_id,
        ai_report=ai_report,
    )
    assert report_id > 0

    retrieved = repo.get_by_job_id("job_audit_1")
    assert retrieved is not None
    assert retrieved["key_findings"] == ["Structured Key Finding 1", "Structured Key Finding 2"]
    assert retrieved["business_implications"] == ["Implication A"]
    assert retrieved["risks"] == ["Operational Risk 1"]
    assert retrieved["opportunities"] == ["Growth Opportunity 1"]
    assert retrieved["actions"] == ["Action A", "Action B"]
    assert retrieved["limitations"] == ["Domain Boundary 1"]
    assert "Medium — Findings are grounded in observed categorical distributions" in retrieved["confidence"]


def test_extract_ai_report_handles_various_input_structures():
    """_extract_ai_report successfully normalizes dict, object, or nested payloads."""
    # 1. Direct dict
    raw = {"executive_summary": "Direct summary", "recommendations": ["A"]}
    assert _extract_ai_report(raw) == raw

    # 2. Nested under ai_report
    nested = {"ai_report": {"executive_summary": "Nested summary"}}
    assert _extract_ai_report(nested) == {"executive_summary": "Nested summary"}

    # 3. None
    assert _extract_ai_report(None) is None


@patch("src.frontend.services.ai_service.APIClient")
def test_get_ai_job_status_fetches_and_persists_job_id(mock_client_cls):
    """get_ai_job_status resolves specific job and caches job_id in session state."""
    mock_instance = MagicMock()
    mock_instance.get_ai_job.return_value = {
        "job_id": "ai_job_custom_999",
        "status": "READY",
        "provider": "ollama",
        "model": "gemma3:4b",
        "ai_report": {"executive_summary": "Ready report"},
    }
    mock_client_cls.return_value = mock_instance

    res = get_ai_job_status("ai_job_custom_999")
    assert res["success"] is True
    assert res["status"] == "READY"
    assert res["job_id"] == "ai_job_custom_999"
    assert res["ai_report"] == {"executive_summary": "Ready report"}
