"""
Governance domain models for AnalystGPT Enterprise.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Decouples DatasetVersion from individual pipeline runs to support dataset reuse,
implements strong typing for cleaning policies and custom strategies,
and provides auditable provenance and quality models.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MissingValuePolicy(str, Enum):
    """
    Supported missing-value treatment strategies.
    """

    PRESERVE_NULLS = "PRESERVE_NULLS"
    DROP_ROWS = "DROP_ROWS"
    DROP_COLUMNS_ABOVE_THRESHOLD = "DROP_COLUMNS_ABOVE_THRESHOLD"
    FILL_NUMERIC_MEAN = "FILL_NUMERIC_MEAN"
    FILL_NUMERIC_MEDIAN = "FILL_NUMERIC_MEDIAN"
    FILL_NUMERIC_MODE = "FILL_NUMERIC_MODE"
    FILL_CATEGORICAL_MODE = "FILL_CATEGORICAL_MODE"
    FILL_CATEGORICAL_CONSTANT = "FILL_CATEGORICAL_CONSTANT"
    CUSTOM_POLICY = "CUSTOM_POLICY"


class ExecutionStatus(str, Enum):
    """Status for cleaning execution records."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass(frozen=True)
class QualitySnapshot:
    """
    Point-in-time quality metrics captured from the existing QualityManager.
    """

    row_count: int
    column_count: int
    total_missing: int
    missing_percentage: float
    completeness_percentage: float
    captured_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    per_column_missing: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_quality_report(
        cls,
        quality_report: Any,
        row_count: int,
        column_count: int,
    ) -> QualitySnapshot:
        completeness = quality_report.report.get("completeness", {})
        return cls(
            row_count=row_count,
            column_count=column_count,
            total_missing=completeness.get("total_missing", 0),
            missing_percentage=completeness.get("missing_percentage", 0.0),
            completeness_percentage=completeness.get("complete_percentage", 100.0),
            per_column_missing=completeness.get("missing_per_column", {}),
        )


@dataclass(frozen=True)
class QualityComparison:
    """
    Before/after quality metrics delta produced by a cleaning execution or preview.
    """

    source: QualitySnapshot
    cleaned: QualitySnapshot

    @property
    def rows_removed(self) -> int:
        return max(0, self.source.row_count - self.cleaned.row_count)

    @property
    def pct_rows_removed(self) -> float:
        if self.source.row_count == 0:
            return 0.0
        return round((self.rows_removed / self.source.row_count) * 100, 4)

    @property
    def missing_values_resolved(self) -> int:
        return max(0, self.source.total_missing - self.cleaned.total_missing)

    @property
    def completeness_gain(self) -> float:
        return round(
            self.cleaned.completeness_percentage - self.source.completeness_percentage,
            4,
        )

    @property
    def has_material_loss(self) -> bool:
        return self.pct_rows_removed >= 5.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.to_dict(),
            "cleaned": self.cleaned.to_dict(),
            "rows_removed": self.rows_removed,
            "pct_rows_removed": self.pct_rows_removed,
            "missing_values_resolved": self.missing_values_resolved,
            "completeness_gain": self.completeness_gain,
            "has_material_loss": self.has_material_loss,
        }


@dataclass(frozen=True)
class DatasetVersion:
    """
    Immutable snapshot of a dataset artifact.
    Decoupled from individual pipeline runs so that source versions can be reused.
    """

    version_id: str  # UUID
    source_filename: str
    byte_size: int
    checksum_sha256: str
    row_count: int
    column_count: int
    storage_path: str
    is_source: bool = True  # True = raw uploaded, False = cleaned analytical
    content_type: str = "text/csv"
    parent_version_id: str | None = None  # Lineage pointer to source if cleaned
    schema_json: str | None = None

    user_id: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CleaningConfig:
    """
    Versioned cleaning parameters configuration.
    """

    config_id: str
    missing_value_policy: MissingValuePolicy
    config_version: int = 1
    null_threshold: float | None = None
    fill_value: str | None = None
    affected_columns: list[str] | None = None
    custom_strategy_name: str | None = None
    custom_params: dict[str, Any] | None = None
    user_id: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def affected_columns_json(self) -> str | None:
        return json.dumps(self.affected_columns) if self.affected_columns else None

    def custom_params_json(self) -> str | None:
        return json.dumps(self.custom_params) if self.custom_params else None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["missing_value_policy"] = self.missing_value_policy.value
        return d


@dataclass(frozen=True)
class CleaningExecution:
    """
    Provenance audit record for a cleaning run.
    """

    execution_id: str
    source_version_id: str
    config_id: str
    execution_status: ExecutionStatus
    source_row_count: int
    cleaned_version_id: str | None = None
    pipeline_run_id: int | None = None
    user_id: int | None = None
    cleaned_row_count: int | None = None
    rows_removed: int | None = None
    pct_rows_removed: float | None = None
    source_missing_count: int | None = None
    cleaned_missing_count: int | None = None
    source_completeness_pct: float | None = None
    cleaned_completeness_pct: float | None = None
    columns_removed: list[str] | None = None
    affected_columns_detail: dict[str, str] | None = None
    error_message: str | None = None
    execution_time_seconds: float | None = None
    executed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def columns_removed_json(self) -> str | None:
        return json.dumps(self.columns_removed) if self.columns_removed else None

    def affected_columns_detail_json(self) -> str | None:
        return json.dumps(self.affected_columns_detail) if self.affected_columns_detail else None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["execution_status"] = self.execution_status.value
        return d
