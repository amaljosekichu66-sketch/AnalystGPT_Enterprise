"""
Custom Policy Strategy Registry for AnalystGPT Enterprise.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Provides typed, safe extension contract for CUSTOM_POLICY strategies.
Prohibits eval/exec or arbitrary code execution.
"""

from __future__ import annotations

import abc
from typing import Any

from pandas import DataFrame

from src.core.logger import logger


class CustomPolicyHandler(abc.ABC):
    """
    Abstract base class for custom cleaning strategy handlers.
    """

    @property
    @abc.abstractmethod
    def strategy_name(self) -> str:
        """Unique strategy name identifier."""
        raise NotImplementedError

    @abc.abstractmethod
    def validate_params(self, params: dict[str, Any]) -> None:
        """Validate input parameters against expected schema."""
        raise NotImplementedError

    @abc.abstractmethod
    def apply(
        self,
        dataframe: DataFrame,
        params: dict[str, Any],
    ) -> tuple[DataFrame, list[str], dict[str, str]]:
        """
        Execute custom transformation on DataFrame copy.
        Returns: (transformed_df, columns_removed, affected_columns_detail)
        """
        raise NotImplementedError


class ClipOutliersCustomHandler(CustomPolicyHandler):
    """
    Example registered custom strategy: Impute/clip extreme numeric outliers using quantiles.
    """

    @property
    def strategy_name(self) -> str:
        return "clip_outliers"

    def validate_params(self, params: dict[str, Any]) -> None:
        lower = params.get("lower_quantile", 0.01)
        upper = params.get("upper_quantile", 0.99)
        if not (0.0 <= lower < upper <= 1.0):
            raise ValueError(f"Invalid quantiles: lower={lower}, upper={upper}")

    def apply(
        self,
        dataframe: DataFrame,
        params: dict[str, Any],
    ) -> tuple[DataFrame, list[str], dict[str, str]]:
        df = dataframe.copy()
        lower_q = params.get("lower_quantile", 0.01)
        upper_q = params.get("upper_quantile", 0.99)
        detail: dict[str, str] = {}

        num_cols = df.select_dtypes(include=["number"]).columns
        for col in num_cols:
            low_val = df[col].quantile(lower_q)
            high_val = df[col].quantile(upper_q)
            df[col] = df[col].clip(lower=low_val, upper=high_val)
            detail[col] = f"CUSTOM (clip_outliers): clipped to [{low_val:.4g}, {high_val:.4g}]"

        return df, [], detail


class ConstantFallbackCustomHandler(CustomPolicyHandler):
    """
    Example registered custom strategy: Type-aware domain fallbacks for missing values.
    """

    @property
    def strategy_name(self) -> str:
        return "domain_fallback"

    def validate_params(self, params: dict[str, Any]) -> None:
        if "fallbacks" in params and not isinstance(params["fallbacks"], dict):
            raise ValueError("Parameter 'fallbacks' must be a dictionary of col -> val")

    def apply(
        self,
        dataframe: DataFrame,
        params: dict[str, Any],
    ) -> tuple[DataFrame, list[str], dict[str, str]]:
        df = dataframe.copy()
        fallbacks = params.get("fallbacks", {})
        detail: dict[str, str] = {}

        for col, val in fallbacks.items():
            if col in df.columns:
                n_missing = int(df[col].isnull().sum())
                if n_missing > 0:
                    df[col] = df[col].fillna(val)
                    detail[col] = f"CUSTOM (domain_fallback): filled {n_missing} nulls with '{val}'"

        return df, [], detail


class CustomPolicyRegistry:
    """
    Registry for managing available custom policy strategy handlers.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, CustomPolicyHandler] = {}
        # Register built-in default strategies
        self.register(ClipOutliersCustomHandler())
        self.register(ConstantFallbackCustomHandler())

    def register(self, handler: CustomPolicyHandler) -> None:
        logger.info("Registering custom policy handler: %s", handler.strategy_name)
        self._handlers[handler.strategy_name] = handler

    def get(self, strategy_name: str) -> CustomPolicyHandler:
        if strategy_name not in self._handlers:
            raise KeyError(
                f"Unknown custom strategy '{strategy_name}'. " f"Available strategies: {list(self._handlers.keys())}"
            )
        return self._handlers[strategy_name]

    def list_strategies(self) -> list[str]:
        return list(self._handlers.keys())
