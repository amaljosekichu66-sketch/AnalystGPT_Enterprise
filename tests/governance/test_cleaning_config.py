"""
Tests for CleaningConfig model.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import json
import uuid

import pytest

from src.governance.models import CleaningConfig, MissingValuePolicy


def _make_config(**kwargs) -> CleaningConfig:
    defaults = dict(
        config_id=str(uuid.uuid4()),
        missing_value_policy=MissingValuePolicy.DROP_ROWS,
        user_id=1,
    )
    defaults.update(kwargs)
    return CleaningConfig(**defaults)


def test_config_has_uuid_config_id():
    cfg = _make_config()
    uuid.UUID(cfg.config_id)


def test_config_default_version_is_one():
    cfg = _make_config()
    assert cfg.config_version == 1


def test_config_policy_is_enum():
    cfg = _make_config(missing_value_policy=MissingValuePolicy.FILL_NUMERIC_MEAN)
    assert cfg.missing_value_policy == MissingValuePolicy.FILL_NUMERIC_MEAN


def test_config_to_dict_serializable():
    cfg = _make_config(
        missing_value_policy=MissingValuePolicy.FILL_CATEGORICAL_CONSTANT,
        fill_value="N/A",
    )
    d = cfg.to_dict()
    assert d["missing_value_policy"] == "FILL_CATEGORICAL_CONSTANT"
    assert d["fill_value"] == "N/A"
    assert json.dumps(d)


def test_config_affected_columns_json_none_when_all():
    cfg = _make_config(affected_columns=None)
    assert cfg.affected_columns_json() is None


def test_config_affected_columns_json_serialized():
    cfg = _make_config(affected_columns=["col_a", "col_b"])
    j = cfg.affected_columns_json()
    assert j is not None
    assert json.loads(j) == ["col_a", "col_b"]


def test_config_custom_params_json():
    cfg = _make_config(
        missing_value_policy=MissingValuePolicy.CUSTOM_POLICY,
        custom_strategy_name="clip_outliers",
        custom_params={"lower_quantile": 0.05},
    )
    j = cfg.custom_params_json()
    assert j is not None
    assert json.loads(j)["lower_quantile"] == 0.05


def test_config_null_threshold_for_column_drop_policy():
    cfg = _make_config(
        missing_value_policy=MissingValuePolicy.DROP_COLUMNS_ABOVE_THRESHOLD,
        null_threshold=40.0,
    )
    assert cfg.null_threshold == pytest.approx(40.0)


def test_config_is_frozen():
    cfg = _make_config()
    with pytest.raises((AttributeError, TypeError)):
        cfg.config_id = "should-fail"  # type: ignore[misc]


def test_all_9_policies_are_valid_enum_members():
    expected = {
        "PRESERVE_NULLS",
        "DROP_ROWS",
        "DROP_COLUMNS_ABOVE_THRESHOLD",
        "FILL_NUMERIC_MEAN",
        "FILL_NUMERIC_MEDIAN",
        "FILL_NUMERIC_MODE",
        "FILL_CATEGORICAL_MODE",
        "FILL_CATEGORICAL_CONSTANT",
        "CUSTOM_POLICY",
    }
    actual = {p.value for p in MissingValuePolicy}
    assert actual == expected
