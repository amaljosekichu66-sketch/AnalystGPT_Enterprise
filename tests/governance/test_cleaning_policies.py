"""
Tests for all 9 MissingValuePolicy implementations.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import uuid

import pandas as pd
import pytest

from src.governance.models import CleaningConfig, MissingValuePolicy
from src.governance.policies import MissingValuePolicyExecutor


def _config(
    policy: MissingValuePolicy,
    null_threshold: float | None = None,
    fill_value: str | None = None,
    affected_columns: list[str] | None = None,
    custom_strategy_name: str | None = None,
    custom_params: dict | None = None,
) -> CleaningConfig:
    return CleaningConfig(
        config_id=str(uuid.uuid4()),
        missing_value_policy=policy,
        null_threshold=null_threshold,
        fill_value=fill_value,
        affected_columns=affected_columns,
        custom_strategy_name=custom_strategy_name,
        custom_params=custom_params,
        user_id=1,
    )


@pytest.fixture
def executor() -> MissingValuePolicyExecutor:
    return MissingValuePolicyExecutor()


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Alice", None, "Bob", None],
            "age": [25, None, 30, None],
            "salary": [50000.0, 60000.0, None, None],
            "city": ["NY", "LA", None, None],
        }
    )


def test_preserve_nulls_makes_no_change(executor, sample_df):
    config = _config(MissingValuePolicy.PRESERVE_NULLS)
    result = executor.execute(sample_df, config)
    assert result.cleaned_df.isnull().sum().sum() == sample_df.isnull().sum().sum()
    assert result.columns_removed == []


def test_preserve_nulls_does_not_mutate_input(executor, sample_df):
    config = _config(MissingValuePolicy.PRESERVE_NULLS)
    original_nulls = sample_df.isnull().sum().sum()
    executor.execute(sample_df, config)
    assert sample_df.isnull().sum().sum() == original_nulls


def test_drop_rows_removes_all_rows_with_nulls(executor, sample_df):
    config = _config(MissingValuePolicy.DROP_ROWS)
    result = executor.execute(sample_df, config)
    assert result.cleaned_df.isnull().sum().sum() == 0
    assert len(result.cleaned_df) < len(sample_df)


def test_drop_rows_targeted_column(executor, sample_df):
    config = _config(MissingValuePolicy.DROP_ROWS, affected_columns=["age"])
    result = executor.execute(sample_df, config)
    assert result.cleaned_df["age"].isnull().sum() == 0
    assert len(result.cleaned_df) < len(sample_df)


def test_drop_rows_does_not_mutate_input(executor, sample_df):
    original_len = len(sample_df)
    config = _config(MissingValuePolicy.DROP_ROWS)
    executor.execute(sample_df, config)
    assert len(sample_df) == original_len


def test_drop_columns_above_threshold_drops_high_null_columns(executor):
    df = pd.DataFrame(
        {
            "good_col": [1, 2, 3, 4, 5],
            "mostly_null": [None, None, None, None, 1],
        }
    )
    config = _config(MissingValuePolicy.DROP_COLUMNS_ABOVE_THRESHOLD, null_threshold=50.0)
    result = executor.execute(df, config)
    assert "mostly_null" in result.columns_removed
    assert "mostly_null" not in result.cleaned_df.columns
    assert "good_col" in result.cleaned_df.columns


def test_drop_columns_retains_columns_below_threshold(executor):
    df = pd.DataFrame({"mostly_good": [1, None, 3, 4, 5]})
    config = _config(MissingValuePolicy.DROP_COLUMNS_ABOVE_THRESHOLD, null_threshold=50.0)
    result = executor.execute(df, config)
    assert result.columns_removed == []
    assert "mostly_good" in result.cleaned_df.columns


def test_drop_columns_empty_dataframe(executor):
    df = pd.DataFrame({"a": []})
    config = _config(MissingValuePolicy.DROP_COLUMNS_ABOVE_THRESHOLD, null_threshold=50.0)
    result = executor.execute(df, config)
    assert result.columns_removed == []


def test_drop_columns_default_threshold_is_50(executor):
    df = pd.DataFrame({"col": [None, None, None, 1]})
    config = _config(MissingValuePolicy.DROP_COLUMNS_ABOVE_THRESHOLD)
    result = executor.execute(df, config)
    assert "col" in result.columns_removed


def test_fill_numeric_mean_fills_nulls_with_mean(executor, sample_df):
    config = _config(MissingValuePolicy.FILL_NUMERIC_MEAN)
    result = executor.execute(sample_df, config)
    assert result.cleaned_df["age"].isnull().sum() == 0
    assert result.cleaned_df["salary"].isnull().sum() == 0
    assert result.cleaned_df["age"].iloc[1] == pytest.approx(27.5)


def test_fill_numeric_mean_does_not_touch_string_cols(executor, sample_df):
    config = _config(MissingValuePolicy.FILL_NUMERIC_MEAN)
    result = executor.execute(sample_df, config)
    assert result.cleaned_df["name"].isnull().sum() > 0


def test_fill_numeric_mean_targeted_column(executor, sample_df):
    config = _config(MissingValuePolicy.FILL_NUMERIC_MEAN, affected_columns=["age"])
    result = executor.execute(sample_df, config)
    assert result.cleaned_df["age"].isnull().sum() == 0
    assert result.cleaned_df["salary"].isnull().sum() > 0


def test_fill_numeric_median_fills_with_median(executor):
    df = pd.DataFrame({"value": [1, 2, 3, None, 5]})
    config = _config(MissingValuePolicy.FILL_NUMERIC_MEDIAN)
    result = executor.execute(df, config)
    assert result.cleaned_df["value"].isnull().sum() == 0
    assert result.cleaned_df["value"].iloc[3] == pytest.approx(2.5)


def test_fill_numeric_mode_fills_with_mode(executor):
    df = pd.DataFrame({"value": [1, 1, 2, None]})
    config = _config(MissingValuePolicy.FILL_NUMERIC_MODE)
    result = executor.execute(df, config)
    assert result.cleaned_df["value"].isnull().sum() == 0
    assert result.cleaned_df["value"].iloc[3] == 1


def test_fill_categorical_mode_fills_with_mode(executor):
    df = pd.DataFrame({"category": ["A", "A", "B", None]})
    config = _config(MissingValuePolicy.FILL_CATEGORICAL_MODE)
    result = executor.execute(df, config)
    assert result.cleaned_df["category"].isnull().sum() == 0
    assert result.cleaned_df["category"].iloc[3] == "A"


def test_fill_categorical_mode_does_not_touch_numeric_cols(executor, sample_df):
    config = _config(MissingValuePolicy.FILL_CATEGORICAL_MODE)
    result = executor.execute(sample_df, config)
    assert result.cleaned_df["age"].isnull().sum() > 0


def test_fill_categorical_constant_fills_with_value(executor):
    df = pd.DataFrame({"status": ["active", None, "active", None]})
    config = _config(MissingValuePolicy.FILL_CATEGORICAL_CONSTANT, fill_value="UNKNOWN")
    result = executor.execute(df, config)
    assert result.cleaned_df["status"].isnull().sum() == 0
    assert (result.cleaned_df["status"] == "UNKNOWN").sum() == 2


def test_fill_categorical_constant_default_is_UNKNOWN(executor):
    df = pd.DataFrame({"col": ["a", None]})
    config = _config(MissingValuePolicy.FILL_CATEGORICAL_CONSTANT)
    result = executor.execute(df, config)
    assert result.cleaned_df["col"].iloc[1] == "UNKNOWN"


def test_custom_policy_execution(executor, sample_df):
    config = _config(
        MissingValuePolicy.CUSTOM_POLICY,
        custom_strategy_name="clip_outliers",
        custom_params={"lower_quantile": 0.0, "upper_quantile": 1.0},
    )
    result = executor.execute(sample_df, config)
    assert result.columns_removed == []


def test_no_policy_mutates_original_dataframe(executor, sample_df):
    original_nulls = int(sample_df.isnull().sum().sum())
    for policy in MissingValuePolicy:
        df_copy = sample_df.copy()
        if policy == MissingValuePolicy.FILL_CATEGORICAL_CONSTANT:
            config = _config(policy, fill_value="X")
        elif policy == MissingValuePolicy.DROP_COLUMNS_ABOVE_THRESHOLD:
            config = _config(policy, null_threshold=90.0)
        elif policy == MissingValuePolicy.CUSTOM_POLICY:
            config = _config(policy, custom_strategy_name="clip_outliers")
        else:
            config = _config(policy)
        executor.execute(df_copy, config)
    assert int(sample_df.isnull().sum().sum()) == original_nulls
