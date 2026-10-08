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
