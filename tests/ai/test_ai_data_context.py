"""
Unit and contract tests for AIDataContext models and builder.

Sprint 14 Phase 4 — AI Data Context & Analytical Integrity.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from src.ai.context import (
    AIDataContext,
    AnalyticalDataContext,
    CleaningContext,
    LineageContext,
    SourceDataContext,
)
from src.ai.context_builder import AIDataContextBuilder
from src.governance.models import (
    CleaningConfig,
    CleaningExecution,
    DatasetVersion,
    ExecutionStatus,
    MissingValuePolicy,
    QualityComparison,
    QualitySnapshot,
)
from src.reporting.reporting_report import ReportingReport
from src.reporting.structured_report import StructuredReport


def test_ai_data_context_models_immutability():
    """Verify AIDataContext dataclasses are immutable and serializable."""
    src = SourceDataContext(
        version_id="src-123",
        source_filename="test.csv",
        row_count=100,
        column_count=5,
        total_missing=10,
        missing_percentage=2.0,
        completeness_percentage=98.0,
        per_column_missing={"age": 10},
    )
    cln = CleaningContext(
        config_id="cfg-123",
        missing_value_policy="DROP_ROWS",
        rows_removed=10,
        pct_rows_removed=10.0,
        columns_removed=["dropped_col"],
        values_imputed=0,
        affected_columns=["age"],
    )
    ana = AnalyticalDataContext(
        cleaned_version_id="cln-123",
        row_count=90,
        column_count=4,
        completeness_percentage=100.0,
        kpis={"total_sales": 1000.0},
        descriptive_statistics={"sales": {"mean": 100.0}},
        correlations={},
        distributions={},
        categorical_insights={},
        recommendations=["Invest in marketing."],
    )
    lin = LineageContext(
        pipeline_run_id=1,
        source_version_id="src-123",
        cleaned_version_id="cln-123",
        cleaning_execution_id="exec-123",
        user_id=42,
        report_id=10,
        context_schema_version="v1.0",
    )

    ctx = AIDataContext(source=src, cleaning=cln, analytics=ana, lineage=lin)

    # Immutability check
    with pytest.raises(FrozenInstanceError):
        ctx.source.row_count = 50  # type: ignore

    # Serialization check
    d = ctx.to_dict()
    assert d["source"]["row_count"] == 100
    assert d["cleaning"]["rows_removed"] == 10
    assert d["cleaning"]["pct_rows_removed"] == 10.0
    assert d["analytics"]["row_count"] == 90
    assert d["lineage"]["pipeline_run_id"] == 1
    assert "created_at" in d


def test_context_builder_from_pipeline_objects():
    """Verify AIDataContextBuilder constructs context with factual magnitude."""
    source_ver = DatasetVersion(
        version_id="v-source",
        source_filename="raw_sales.csv",
        byte_size=1024,
        checksum_sha256="abc",
        row_count=100,
        column_count=4,
        storage_path="/path/raw.csv",
        is_source=True,
    )
    cleaned_ver = DatasetVersion(
        version_id="v-cleaned",
        source_filename="raw_sales_cleaned.parquet",
        byte_size=2048,
        checksum_sha256="def",
        row_count=85,
        column_count=4,
        storage_path="/path/cleaned.parquet",
        is_source=False,
        parent_version_id="v-source",
    )
    cleaning_exec = CleaningExecution(
        execution_id="exec-001",
        source_version_id="v-source",
        cleaned_version_id="v-cleaned",
        config_id="cfg-001",
        execution_status=ExecutionStatus.SUCCESS,
        source_row_count=100,
        cleaned_row_count=85,
        rows_removed=15,
        pct_rows_removed=15.0,
        source_missing_count=15,
        cleaned_missing_count=0,
        source_completeness_pct=85.0,
        cleaned_completeness_pct=100.0,
    )
    structured = StructuredReport(
        title="Business Report",
        executive_summary="Summary text.",
        kpis={"revenue": 50000},
        analytics={"descriptive_statistics": {"revenue": {"mean": 500}}},
        recommendations=["Scale up."],
    )
    reporting_rep = ReportingReport(
        report=structured,
        export_path="/path/report.txt",
        execution_time=0.1,
    )

    ctx = AIDataContextBuilder.build_from_pipeline_objects(
        source_version=source_ver,
        cleaned_version=cleaned_ver,
        cleaning_execution=cleaning_exec,
        reporting_report=reporting_rep,
        pipeline_run_id=5,
        user_id=1,
    )

    assert ctx.source.row_count == 100
    assert ctx.cleaning.rows_removed == 15
    assert ctx.cleaning.pct_rows_removed == 15.0
    assert ctx.analytics.row_count == 85
    assert ctx.lineage.source_version_id == "v-source"
    assert ctx.lineage.cleaned_version_id == "v-cleaned"
