"""
AI Data Context contracts for AnalystGPT Enterprise.

Sprint 14 Phase 4 — AI Data Context & Analytical Integrity.

Provides strongly-typed domain representations of source data metrics,
cleaning/transformation records, post-cleaning analytical findings,
and relational lineage pointers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class SourceDataContext:
    """
    Factual observations of the immutable raw dataset prior to cleaning.
    """

    version_id: str | None
    source_filename: str
    row_count: int
    column_count: int
    total_missing: int | None = None
    missing_percentage: float | None = None
    completeness_percentage: float | None = None
    per_column_missing: dict[str, int] = field(default_factory=dict)
    outliers_detected: int | None = None
    column_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CleaningContext:
    """
    Deterministic record of data cleaning and transformation operations.
    """

    config_id: str | None
    missing_value_policy: str | None = None
    rows_removed: int | None = None
    pct_rows_removed: float | None = None
    columns_removed: list[str] = field(default_factory=list)
    values_imputed: int | None = None
    affected_columns: list[str] = field(default_factory=list)
    custom_strategy_name: str | None = None
    transformations_applied: list[str] = field(default_factory=list)

    @property
    def has_row_reduction(self) -> bool:
        """Return True if any rows were eliminated during cleaning."""
        return bool(self.rows_removed and self.rows_removed > 0)

    @property
    def has_column_reduction(self) -> bool:
        """Return True if any columns were dropped during cleaning."""
        return len(self.columns_removed) > 0

    @property
    def has_imputation(self) -> bool:
        """Return True if values were imputed/substituted."""
        return bool(self.values_imputed and self.values_imputed > 0)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalyticalDataContext:
    """
    Post-cleaning analytical metrics and statistical summaries.
    """

    cleaned_version_id: str | None
    row_count: int
    column_count: int
    completeness_percentage: float = 100.0
    kpis: dict[str, Any] = field(default_factory=dict)
    descriptive_statistics: dict[str, Any] = field(default_factory=dict)
    correlations: dict[str, Any] = field(default_factory=dict)
    distributions: dict[str, Any] = field(default_factory=dict)
    categorical_insights: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LineageContext:
    """
    Relational provenance pointers for auditability.
    """

    pipeline_run_id: int | None
    source_version_id: str | None
    cleaned_version_id: str | None
    cleaning_execution_id: str | None
    user_id: int | None = None
    report_id: int | None = None
    context_schema_version: str = "v1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIDataContext:
    """
    Composite domain entity representing complete data context for AI generation.

    Note on Timestamp Semantics:
    -----------------------------
    `created_at` records the in-memory instantiation/reconstruction timestamp of this
    AIDataContext instance. It is NOT a durable provenance identifier. Durable provenance
    is strictly established by the immutable foreign key pointers inside `lineage`
    (`pipeline_run_id`, `source_version_id`, `cleaned_version_id`, `cleaning_execution_id`,
    and `context_schema_version`).
    """

    source: SourceDataContext
    cleaning: CleaningContext
    analytics: AnalyticalDataContext
    lineage: LineageContext
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.to_dict(),
            "cleaning": self.cleaning.to_dict(),
            "analytics": self.analytics.to_dict(),
            "lineage": self.lineage.to_dict(),
            "created_at": self.created_at,
        }
