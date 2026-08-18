"""
Missing Value Policy Execution Engine.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Applies the 9 named missing value policies deterministically on DataFrame copies.
Dispatches CUSTOM_POLICY to the CustomPolicyRegistry.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas import DataFrame

from src.core.logger import logger
from src.governance.custom_registry import CustomPolicyRegistry
from src.governance.models import CleaningConfig, MissingValuePolicy


class PolicyExecutionResult:
    """Carries transformation output and detail."""

    def __init__(
        self,
        cleaned_df: DataFrame,
        columns_removed: list[str],
        affected_columns_detail: dict[str, str],
    ) -> None:
        self.cleaned_df = cleaned_df
        self.columns_removed = columns_removed
        self.affected_columns_detail = affected_columns_detail


class MissingValuePolicyExecutor:
    """
    Stateless executor for missing value policies.
    """

    def __init__(self, registry: CustomPolicyRegistry | None = None) -> None:
        self.registry = registry or CustomPolicyRegistry()

    def execute(
        self,
        dataframe: DataFrame,
        config: CleaningConfig,
    ) -> PolicyExecutionResult:
        policy = config.missing_value_policy
        df = dataframe.copy()

        logger.info("Executing missing-value policy: %s", policy.value)

        if policy == MissingValuePolicy.PRESERVE_NULLS:
            return PolicyExecutionResult(
                cleaned_df=df,
                columns_removed=[],
                affected_columns_detail={"_all_columns": "PRESERVE_NULLS — no transformation applied"},
            )

        if policy == MissingValuePolicy.DROP_ROWS:
            subset = config.affected_columns or None
            cleaned = df.dropna(subset=subset)
            detail = {
                (col if subset else "_all_columns"): "DROP_ROWS — removed rows with missing values"
                for col in (subset or ["_all_columns"])
            }
            return PolicyExecutionResult(cleaned, [], detail)

        if policy == MissingValuePolicy.DROP_COLUMNS_ABOVE_THRESHOLD:
            threshold = config.null_threshold if config.null_threshold is not None else 50.0
            n_rows = len(df)
            cols_to_drop: list[str] = []
            detail = {}
            if n_rows > 0:
                for col in df.columns:
                    null_pct = (df[col].isnull().sum() / n_rows) * 100
                    if null_pct > threshold:
                        cols_to_drop.append(col)
                        detail[col] = f"DROP_COLUMNS_ABOVE_THRESHOLD ({null_pct:.1f}% > {threshold:.1f}%)"
            cleaned = df.drop(columns=cols_to_drop)
            return PolicyExecutionResult(cleaned, cols_to_drop, detail)

        if policy in (
            MissingValuePolicy.FILL_NUMERIC_MEAN,
            MissingValuePolicy.FILL_NUMERIC_MEDIAN,
            MissingValuePolicy.FILL_NUMERIC_MODE,
        ):
            method = policy.value.split("_")[-1].lower()
            num_cols = df.select_dtypes(include=["number"]).columns.tolist()
            target_cols = [c for c in (config.affected_columns or num_cols) if c in num_cols]
            detail = {}
            for col in target_cols:
                n_miss = int(df[col].isnull().sum())
                if n_miss > 0:
                    if method == "mean":
                        val = df[col].mean()
                    elif method == "median":
                        val = df[col].median()
                    else:
                        modes = df[col].mode()
                        val = modes.iloc[0] if len(modes) > 0 else 0
                    df[col] = df[col].fillna(val)
                    detail[col] = f"FILL_NUMERIC_{method.upper()} — filled {n_miss} with {val:.4g}"
            return PolicyExecutionResult(df, [], detail)

        if policy == MissingValuePolicy.FILL_CATEGORICAL_MODE:
            cat_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
            target_cols = [c for c in (config.affected_columns or cat_cols) if c in cat_cols]
            detail = {}
            for col in target_cols:
                n_miss = int(df[col].isnull().sum())
                if n_miss > 0:
                    modes = df[col].mode()
                    if len(modes) > 0:
                        val = modes.iloc[0]
                        df[col] = df[col].fillna(val)
                        detail[col] = f"FILL_CATEGORICAL_MODE — filled {n_miss} with '{val}'"
            return PolicyExecutionResult(df, [], detail)

        if policy == MissingValuePolicy.FILL_CATEGORICAL_CONSTANT:
            fill_val = config.fill_value if config.fill_value is not None else "UNKNOWN"
            cat_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
            target_cols = [c for c in (config.affected_columns or cat_cols) if c in cat_cols]
            detail = {}
            for col in target_cols:
                n_miss = int(df[col].isnull().sum())
                if n_miss > 0:
                    df[col] = df[col].fillna(fill_val)
                    detail[col] = f"FILL_CATEGORICAL_CONSTANT — filled {n_miss} with '{fill_val}'"
            return PolicyExecutionResult(df, [], detail)

        if policy == MissingValuePolicy.CUSTOM_POLICY:
            strategy_name = config.custom_strategy_name or "clip_outliers"
            params = config.custom_params or {}
            handler = self.registry.get(strategy_name)
            handler.validate_params(params)
            cleaned, cols_removed, detail = handler.apply(df, params)
            return PolicyExecutionResult(cleaned, cols_removed, detail)

        raise ValueError(f"Unsupported MissingValuePolicy: {policy}")
