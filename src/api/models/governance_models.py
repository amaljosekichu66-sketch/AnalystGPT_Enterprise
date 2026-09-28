"""
Governance API models for AnalystGPT Enterprise.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Typed Pydantic request/response models for governance endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ==========================================================
# Requests
# ==========================================================


class CleaningConfigRequest(BaseModel):
    """Request model for creating/configuring cleaning policies."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    missing_value_policy: str = Field(
        default="DROP_ROWS",
        description="Named missing value strategy (e.g. DROP_ROWS, FILL_NUMERIC_MEAN, CUSTOM_POLICY)",
    )
    null_threshold: float | None = Field(
        default=None,
        description="Null percentage threshold for DROP_COLUMNS_ABOVE_THRESHOLD",
    )
    fill_value: str | None = Field(
        default=None,
        description="Constant fill value for FILL_CATEGORICAL_CONSTANT",
    )
    affected_columns: list[str] | None = Field(
        default=None,
        description="Specific columns to target. If null, applies across all eligible columns.",
    )
    custom_strategy_name: str | None = Field(
        default=None,
        description="Name of registered custom strategy handler if policy is CUSTOM_POLICY",
    )
    custom_params: dict[str, Any] | None = Field(
        default=None,
        description="Validated parameters dictionary for custom strategy",
    )


class CleaningPreviewRequest(BaseModel):
    """
    Request model for non-destructive cleaning preview.
    Requires a registered immutable dataset_version_id reference.
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    dataset_version_id: str = Field(
        ...,
        description="UUID of registered source dataset version to preview",
    )
    cleaning_config: CleaningConfigRequest = Field(
        default_factory=CleaningConfigRequest,
        description="Proposed cleaning configuration to test",
    )
    sample_rows: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of sample rows to return in before/after preview comparison",
    )


# ==========================================================
# Responses
# ==========================================================


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    version_id: str
    source_filename: str
    content_type: str
    byte_size: int
    checksum_sha256: str
    row_count: int
    column_count: int
    is_source: bool
    storage_path: str
    parent_version_id: str | None = None
    dataset_schema_json: str | None = None
    created_at: str | None = None


class CleaningConfigResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    config_id: str
    missing_value_policy: str
    config_version: int
    null_threshold: float | None = None
    fill_value: str | None = None
    affected_columns: str | None = None
    custom_strategy_name: str | None = None
    custom_params_json: str | None = None
    created_at: str | None = None


class CleaningExecutionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    source_version_id: str
    config_id: str
    execution_status: str
    source_row_count: int
    cleaned_version_id: str | None = None
    pipeline_run_id: int | None = None
    cleaned_row_count: int | None = None
    rows_removed: int | None = None
    pct_rows_removed: float | None = None
    source_missing_count: int | None = None
    cleaned_missing_count: int | None = None
    source_completeness_pct: float | None = None
    cleaned_completeness_pct: float | None = None
    columns_removed: str | None = None
    affected_columns_detail: str | None = None
    error_message: str | None = None
    execution_time_seconds: float | None = None
    executed_at: str | None = None


class QualityComparisonResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    rows_removed: int
    pct_rows_removed: float
    missing_values_resolved: int
    completeness_gain: float
    has_material_loss: bool
    source_completeness_pct: float
    cleaned_completeness_pct: float


class CleaningPreviewResponse(BaseModel):
    """
    Response model returned by non-destructive preview endpoint.
    """

    model_config = ConfigDict(frozen=True)

    quality_comparison: QualityComparisonResponse
    columns_removed: list[str]
    affected_columns_detail: dict[str, str]
    preview_sample_source: list[dict[str, Any]]
    preview_sample_cleaned: list[dict[str, Any]]


class LineageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_dataset_version: DatasetVersionResponse | None = None
    cleaned_dataset_version: DatasetVersionResponse | None = None
    cleaning_config: CleaningConfigResponse | None = None
    cleaning_execution: CleaningExecutionResponse | None = None
