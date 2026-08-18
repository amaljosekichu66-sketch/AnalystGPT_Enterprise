"""
Analytical integrity and prompt boundary tests for Sprint 14 Phase 4.

Verifies:
1. Source vs Cleaned distinction in prompt serialization
2. Handling of untrusted dataset content
3. Anti-hallucination boundary checks
"""

from __future__ import annotations

from src.ai.context import (
    AIDataContext,
    AnalyticalDataContext,
    CleaningContext,
    LineageContext,
    SourceDataContext,
)
from src.llm.prompt_builder import PromptBuilder
from src.llm.report_serializer import ReportSerializer
from src.reporting.reporting_report import ReportingReport
from src.reporting.structured_report import StructuredReport


def test_prompt_serialization_includes_all_four_sections():
    """Verify serializer includes explicit source, cleaning, analytics, and lineage sections."""
    src = SourceDataContext(
        version_id="src-999",
        source_filename="untrusted_dataset.csv",
        row_count=500,
        column_count=10,
        total_missing=50,
        missing_percentage=1.0,
        completeness_percentage=90.0,
        per_column_missing={"malicious_instruction_col": 50},
    )
    cln = CleaningContext(
        config_id="cfg-999",
        missing_value_policy="DROP_ROWS",
        rows_removed=50,
        pct_rows_removed=10.0,
        columns_removed=[],
        values_imputed=0,
        affected_columns=["malicious_instruction_col"],
    )
    ana = AnalyticalDataContext(
        cleaned_version_id="cln-999",
        row_count=450,
        column_count=10,
        completeness_percentage=100.0,
        kpis={"metric_a": 123.45},
        descriptive_statistics={"metric_a": {"mean": 12.3}},
        correlations={},
        distributions={},
        categorical_insights={},
        recommendations=["Action A"],
    )
    lin = LineageContext(
        pipeline_run_id=99,
        source_version_id="src-999",
        cleaned_version_id="cln-999",
        cleaning_execution_id="exec-999",
        user_id=1,
    )
    ctx = AIDataContext(source=src, cleaning=cln, analytics=ana, lineage=lin)

    structured = StructuredReport(
        title="Analysis",
        executive_summary="Baseline summary.",
        kpis={"metric_a": 123.45},
        analytics={"descriptive_statistics": {"metric_a": {"mean": 12.3}}},
        recommendations=["Action A"],
    )
    rep = ReportingReport(report=structured, export_path="/tmp/rep.txt", execution_time=0.05)

    serialized = ReportSerializer.serialize(rep, data_context=ctx)

    # Check distinct section delimiters
    assert "=== SECTION 1: SOURCE DATA OBSERVATIONS (RAW DATASET) ===" in serialized
    assert "Raw Ingested Rows     : 500" in serialized
    assert "=== SECTION 2: DATA CLEANING & TRANSFORMATION RECORD ===" in serialized
    assert "Rows Removed          : 50 (10.00%)" in serialized
    assert "=== SECTION 3: POST-CLEANING ANALYTICAL FINDINGS ===" in serialized
    assert "Cleaned Row Count     : 450" in serialized
    assert "=== SECTION 4: DATASET LINEAGE & PROVENANCE ===" in serialized
    assert "Source Version ID     : src-999" in serialized

    # Check prompt builder anti-hallucination rules
    prompt = PromptBuilder.full_report(rep, data_context=ctx)
    assert "ANALYTICAL INTEGRITY & SOURCE DATA RULES" in prompt
    assert "SOURCE VS CLEANED DATA DISTINCTION" in prompt
    assert "UNTRUSTED DATA DELIMITER" in prompt
    assert "REPORT START" in prompt
    assert "REPORT END" in prompt
