"""
Tests for CustomPolicyRegistry and typed CustomPolicyHandler contracts.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.governance.custom_registry import (
    ClipOutliersCustomHandler,
    ConstantFallbackCustomHandler,
    CustomPolicyHandler,
    CustomPolicyRegistry,
)
from src.governance.models import CleaningConfig, MissingValuePolicy
from src.governance.policies import MissingValuePolicyExecutor


def test_registry_lists_default_strategies():
    registry = CustomPolicyRegistry()
    strategies = registry.list_strategies()
    assert "clip_outliers" in strategies
    assert "domain_fallback" in strategies


def test_clip_outliers_handler():
    handler = ClipOutliersCustomHandler()
    handler.validate_params({"lower_quantile": 0.05, "upper_quantile": 0.95})

    df = pd.DataFrame({"val": [1, 2, 3, 4, 1000]})
    transformed_df, cols_removed, detail = handler.apply(
        df, {"lower_quantile": 0.0, "upper_quantile": 0.8}
    )
    assert transformed_df["val"].max() < 1000
    assert cols_removed == []
    assert "val" in detail


def test_clip_outliers_invalid_params_raises():
    handler = ClipOutliersCustomHandler()
    with pytest.raises(ValueError, match="Invalid quantiles"):
        handler.validate_params({"lower_quantile": 0.9, "upper_quantile": 0.1})


def test_domain_fallback_handler():
    handler = ConstantFallbackCustomHandler()
    df = pd.DataFrame({"city": ["NY", None, "SF"], "country": [None, "USA", "USA"]})
    transformed_df, _, detail = handler.apply(
        df, {"fallbacks": {"city": "Unknown City", "country": "Global"}}
    )
    assert transformed_df["city"].iloc[1] == "Unknown City"
    assert transformed_df["country"].iloc[0] == "Global"


def test_custom_policy_executor_integration():
    registry = CustomPolicyRegistry()
    executor = MissingValuePolicyExecutor(registry=registry)

    df = pd.DataFrame({"num": [10, 20, 30, 40, 500]})
    config = CleaningConfig(
        config_id="test-cfg",
        missing_value_policy=MissingValuePolicy.CUSTOM_POLICY,
        custom_strategy_name="clip_outliers",
        custom_params={"lower_quantile": 0.0, "upper_quantile": 0.8},
    )
    res = executor.execute(df, config)
    assert res.cleaned_df["num"].max() < 500
