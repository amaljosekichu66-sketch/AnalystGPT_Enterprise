"""
Tests for CleaningExecution model and serialization.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import json
import uuid

import pytest

from src.governance.models import CleaningExecution, ExecutionStatus


def _execution(**kwargs) -> CleaningExecution:
    defaults = dict(
        execution_id=str(uuid.uuid4()),
        source_version_id=str(uuid.uuid4()),
        config_id=str(uuid.uuid4()),
        execution_status=ExecutionStatus.SUCCESS,
        source_row_count=100,
        user_id=1,
    )
    defaults.update(kwargs)
    return CleaningExecution(**defaults)


def test_execution_success_has_uuid():
    exec_record = _execution()
    uuid.UUID(exec_record.execution_id)


def test_execution_success_to_dict():
    exec_record = _execution(
        cleaned_row_count=80,
        rows_removed=20,
        pct_rows_removed=20.0,
    )
    d = exec_record.to_dict()
    assert d["execution_status"] == "SUCCESS"
    assert d["rows_removed"] == 20
    assert json.dumps(d)


def test_execution_failed_status():
    exec_record = _execution(
        execution_status=ExecutionStatus.FAILED,
        error_message="Deliberate test failure",
    )
    d = exec_record.to_dict()
    assert d["execution_status"] == "FAILED"
    assert d["error_message"] == "Deliberate test failure"


def test_execution_columns_removed_json():
    exec_record = _execution(columns_removed=["colA", "colB"])
    j = exec_record.columns_removed_json()
    assert j is not None
    assert json.loads(j) == ["colA", "colB"]


def test_execution_affected_columns_detail_json():
    detail = {"col_a": "DROP_ROWS", "col_b": "FILL_NUMERIC_MEAN"}
    exec_record = _execution(affected_columns_detail=detail)
    j = exec_record.affected_columns_detail_json()
    assert j is not None
    parsed = json.loads(j)
    assert parsed["col_a"] == "DROP_ROWS"
