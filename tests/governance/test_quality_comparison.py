"""
Tests for QualitySnapshot and QualityComparison models.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.governance.models import QualityComparison, QualitySnapshot
from src.quality.quality_manager import QualityManager


def _snapshot(row_count, column_count, total_missing, missing_pct, complete_pct):
    return QualitySnapshot(
        row_count=row_count,
        column_count=column_count,
        total_missing=total_missing,
        missing_percentage=missing_pct,
        completeness_percentage=complete_pct,
    )


def test_quality_snapshot_from_quality_report():
    """QualitySnapshot can be built from QualityManager output."""
    qm = QualityManager()
    df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", None]})
    report = qm.assess(df)
    snap = QualitySnapshot.from_quality_report(report, row_count=3, column_count=2)
    assert snap.row_count == 3
    assert snap.column_count == 2
    assert snap.total_missing == 2
    assert 0.0 <= snap.missing_percentage <= 100.0
    assert 0.0 <= snap.completeness_percentage <= 100.0


def test_quality_snapshot_to_dict_is_json_serializable():
    import json
    snap = _snapshot(10, 3, 2, 6.67, 93.33)
    d = snap.to_dict()
    json.dumps(d)  # Must not raise


def test_quality_comparison_rows_removed():
    source = _snapshot(100, 5, 20, 4.0, 96.0)
    cleaned = _snapshot(80, 5, 0, 0.0, 100.0)
    cmp = QualityComparison(source=source, cleaned=cleaned)
    assert cmp.rows_removed == 20
    assert cmp.pct_rows_removed == pytest.approx(20.0)


def test_quality_comparison_no_rows_removed():
    source = _snapshot(100, 5, 20, 4.0, 96.0)
    cleaned = _snapshot(100, 5, 0, 0.0, 100.0)
    cmp = QualityComparison(source=source, cleaned=cleaned)
    assert cmp.rows_removed == 0
    assert cmp.pct_rows_removed == pytest.approx(0.0)


def test_quality_comparison_material_loss_threshold():
    """Material loss is >= 5% of rows removed."""
    source = _snapshot(100, 5, 0, 0.0, 100.0)
    just_under = _snapshot(96, 5, 0, 0.0, 100.0)
    exactly_at = _snapshot(95, 5, 0, 0.0, 100.0)
    over = _snapshot(90, 5, 0, 0.0, 100.0)

    assert not QualityComparison(source=source, cleaned=just_under).has_material_loss
    assert QualityComparison(source=source, cleaned=exactly_at).has_material_loss
    assert QualityComparison(source=source, cleaned=over).has_material_loss


def test_quality_comparison_missing_values_resolved():
    source = _snapshot(100, 5, 50, 10.0, 90.0)
    cleaned = _snapshot(100, 5, 10, 2.0, 98.0)
    cmp = QualityComparison(source=source, cleaned=cleaned)
    assert cmp.missing_values_resolved == 40


def test_quality_comparison_completeness_gain():
    source = _snapshot(100, 5, 20, 4.0, 96.0)
    cleaned = _snapshot(100, 5, 0, 0.0, 100.0)
    cmp = QualityComparison(source=source, cleaned=cleaned)
    assert cmp.completeness_gain == pytest.approx(4.0)


def test_quality_comparison_to_dict():
    import json
    source = _snapshot(100, 5, 20, 4.0, 96.0)
    cleaned = _snapshot(80, 5, 0, 0.0, 100.0)
    cmp = QualityComparison(source=source, cleaned=cleaned)
    d = cmp.to_dict()
    assert "rows_removed" in d
    assert "pct_rows_removed" in d
    assert "has_material_loss" in d
    json.dumps(d)  # Must not raise


def test_quality_comparison_empty_source():
    """Edge case: source has 0 rows."""
    source = _snapshot(0, 3, 0, 0.0, 100.0)
    cleaned = _snapshot(0, 3, 0, 0.0, 100.0)
    cmp = QualityComparison(source=source, cleaned=cleaned)
    assert cmp.pct_rows_removed == pytest.approx(0.0)
    assert not cmp.has_material_loss
