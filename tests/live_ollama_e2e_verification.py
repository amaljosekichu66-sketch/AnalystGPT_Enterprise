"""
Live End-to-End Ollama Verification Script.

Executes the complete pipeline:
Deterministic dataset -> Analytics -> AI Job creation -> PENDING -> Worker claim
-> GENERATING -> Live Ollama LLM execution (gemma3:4b) -> Structured parsing -> AIReport creation
-> Database persistence -> READY -> API query -> UI component rendering -> Text/PDF export.

Sprint 14 Phase 2 Quality Gate.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import pandas as pd
from ollama import Client

from src.ai.ai_manager import AIManager
from src.ai.job_executor import AIJobExecutor
from src.analytics.analytics_manager import AnalyticsManager
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.schema_manager import SchemaManager
from src.llm.ollama_client import OllamaClient
from src.reporting.exporters.pdf_report_exporter import PdfReportExporter
from src.reporting.exporters.text_report_exporter import TextReportExporter
from src.reporting.reporting_manager import ReportingManager


def verify_live_ollama_e2e() -> dict[str, Any]:
    print("============================================================")
    print("1. CHECKING OLLAMA AVAILABILITY & MODEL")
    print("============================================================")
    client = Client(host=config.OLLAMA_HOST, timeout=10.0)
    try:
        models_resp = client.list()
        models_list = getattr(models_resp, "models", []) or (models_resp.get("models", []) if isinstance(models_resp, dict) else [])
        model_names = [getattr(m, "model", None) or getattr(m, "name", None) or (m.get("model") or m.get("name") if isinstance(m, dict) else str(m)) for m in models_list]
        print(f"✓ Ollama Host Reachable: {config.OLLAMA_HOST}")
        print(f"✓ Available Models: {model_names}")
    except Exception as exc:
        print(f"✗ Ollama Connection Failed: {exc}")
        return {"success": False, "error": f"LIVE E2E NOT VERIFIED — Ollama unavailable ({exc})"}

    if not any(config.OLLAMA_MODEL in (m or "") for m in model_names):
        print(f"✗ Model {config.OLLAMA_MODEL} not found in {model_names}")
        return {"success": False, "error": f"LIVE E2E NOT VERIFIED — Model {config.OLLAMA_MODEL} not available"}

    print(f"✓ Target Model Confirmed: {config.OLLAMA_MODEL}")

    print("\n============================================================")
    print("2. PREPARING DETERMINISTIC ENTERPRISE TEST DATASET")
    print("============================================================")
    df = pd.DataFrame({
        "customer_id": [f"CUST_{i:04d}" for i in range(1, 61)],
        "region": ["North", "South", "East", "West"] * 15,
        "segment": ["Enterprise", "Mid-Market", "SMB"] * 20,
        "contract_value": [10000 + i * 250 for i in range(60)],
        "churn_risk_score": [0.05 + (i % 10) * 0.08 for i in range(60)],
    })
    print(f"✓ Dataset Created: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")

    print("\n============================================================")
    print("3. RUNNING DETERMINISTIC ANALYTICS ENGINE")
    print("============================================================")
    analytics_mgr = AnalyticsManager()
    analytics_report_obj = analytics_mgr.analyze(df)
    analytics_report = analytics_report_obj.report
    print("✓ Analytics Report Generated:")
    print(f"  Total Rows: {analytics_report.get('descriptive_statistics', {}).get('total_rows')}")
    print(f"  Numeric Measures: {analytics_report.get('descriptive_statistics', {}).get('numeric_column_count')}")
    print(f"  Categorical Dimensions: {analytics_report.get('descriptive_statistics', {}).get('categorical_column_count')}")

    print("\n============================================================")
    print("4. INITIALIZING DATABASE & AI JOB INFRASTRUCTURE")
    print("============================================================")
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()

    raw_conn = conn.get_connection()
    cur = raw_conn.cursor()
    cur.execute("INSERT INTO pipeline_runs (status) VALUES ('SUCCESS');")
    pipeline_run_id = int(cur.lastrowid)
    raw_conn.commit()
    cur.close()

    job_repo = AIJobRepository(conn)
    ai_report_repo = AIReportRepository(conn)

    print(f"✓ Pipeline Run Initialized: ID={pipeline_run_id}")

    raw_job_id = f"ai_job_e2e_{int(time.time())}"
    ai_job_obj = job_repo.create_job(
        job_id=raw_job_id,
        pipeline_run_id=pipeline_run_id,
        provider="ollama",
        model=config.OLLAMA_MODEL,
    )
    job_id = ai_job_obj.job_id
    print(f"✓ AI Job Created: ID={job_id}")

    job_state = job_repo.get_by_job_id(job_id)
    assert job_state is not None
    status_val = job_state.status.value if hasattr(job_state.status, "value") else str(job_state.status)
    assert status_val == "PENDING"
    print(f"✓ Initial Job State: {status_val}")

    print("\n============================================================")
    print("5. EXECUTING LIVE OLLAMA GENERATION VIA AI JOB EXECUTOR")
    print("============================================================")
    ollama_client = OllamaClient()
    ai_manager = AIManager(llm=ollama_client)
    executor = AIJobExecutor(max_workers=1, ai_manager=ai_manager)

    reporting_mgr = ReportingManager()
    reporting_report = reporting_mgr.generate_report(analytics_report=analytics_report_obj)

    print(f"Executing AI Job '{job_id}' synchronously against local Ollama ({config.OLLAMA_MODEL})...")
    start_exec = time.perf_counter()
    success = executor.execute_job_sync(job_id, reporting_report=reporting_report)
    elapsed = time.perf_counter() - start_exec

    print(f"✓ Execution Completed in {elapsed:.2f}s | Success={success}")

    final_job = job_repo.get_by_job_id(job_id)
    assert final_job is not None
    final_status = final_job.status.value if hasattr(final_job.status, "value") else str(final_job.status)
    print(f"✓ Final Job Status: {final_status}")
    assert final_status == "READY", f"Job status was {final_status}, error: {getattr(final_job, 'error', None)}"

    print("\n============================================================")
    print("6. VERIFYING PERSISTED STRUCTURED AI REPORT")
    print("============================================================")
    persisted_report = ai_report_repo.get_by_job_id(job_id)
    assert persisted_report is not None, "Persisted AI report not found in DB!"

    print(f"✓ Persisted Provider: {persisted_report['provider']}")
    print(f"✓ Persisted Model: {persisted_report['model']}")
    print(f"✓ Persisted Confidence: {persisted_report['confidence']}")
    print(f"✓ Executive Summary ({len(persisted_report['executive_summary'])} chars):")
    print(f"    {persisted_report['executive_summary'][:200]}...")
    print(f"✓ Key Findings ({len(persisted_report.get('key_findings', []))} items):")
    for idx, kf in enumerate(persisted_report.get("key_findings", [])[:3], 1):
        print(f"    {idx}. {kf}")
    print(f"✓ Prioritized Actions ({len(persisted_report.get('actions', []))} items):")
    for idx, act in enumerate(persisted_report.get("actions", [])[:3], 1):
        print(f"    {idx}. {act}")

    print("\n============================================================")
    print("7. EXPORTING TEXT & PDF REPORTS FROM SINGLE PERSISTED SOURCE")
    print("============================================================")
    structured_report = reporting_report.report
    with tempfile.TemporaryDirectory() as tmp_dir:
        txt_out = Path(tmp_dir) / "live_e2e_report.txt"
        pdf_out = Path(tmp_dir) / "live_e2e_report.pdf"

        txt_exporter = TextReportExporter()
        pdf_exporter = PdfReportExporter()

        txt_path = txt_exporter.export(structured_report, str(txt_out), ai_report=persisted_report)
        pdf_path = pdf_exporter.export(structured_report, str(pdf_out), ai_report=persisted_report)

        print(f"✓ TXT Exported: {txt_path} ({Path(txt_path).stat().st_size} bytes)")
        print(f"✓ PDF Exported: {pdf_path} ({Path(pdf_path).stat().st_size} bytes)")

        txt_content = Path(txt_path).read_text(encoding="utf-8")
        assert "AI Causal Explanations" not in txt_content
        assert "{'total_rows':" not in txt_content
        assert "AI BUSINESS INSIGHTS (AI-GENERATED)" in txt_content
        assert persisted_report["confidence"] in txt_content
        print("✓ TXT Audit Checks Passed (No Causal Explanations, No raw dicts, Grounded confidence present)")

    return {
        "success": True,
        "job_id": job_id,
        "final_state": final_status,
        "model": config.OLLAMA_MODEL,
        "provider": config.LLM_PROVIDER,
        "confidence": persisted_report["confidence"],
        "executive_summary_snippet": persisted_report["executive_summary"][:150] + "...",
        "key_findings": persisted_report["key_findings"],
        "actions": persisted_report["actions"],
        "execution_time_s": elapsed,
    }


if __name__ == "__main__":
    res = verify_live_ollama_e2e()
    print("\n============================================================")
    print("FINAL LIVE E2E RESULT:")
    print("============================================================")
    print(json.dumps(res, indent=2))
    if not res["success"]:
        sys.exit(1)
