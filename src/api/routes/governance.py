"""
Governance REST API routes for AnalystGPT Enterprise.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Exposes endpoints for:
- Non-destructive cleaning preview (POST /api/governance/preview)
- Dataset version catalog & retrieval
- Cleaning configurations
- Cleaning execution provenance audits
- End-to-end lineage queries
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.application_dependency import get_application
from src.api.dependencies.auth_dependencies import require_permission
from src.api.models.governance_models import (
    CleaningConfigRequest,
    CleaningConfigResponse,
    CleaningExecutionResponse,
    CleaningPreviewRequest,
    CleaningPreviewResponse,
    DatasetVersionResponse,
    LineageResponse,
    QualityComparisonResponse,
)
from src.application.app import Application
from src.governance.models import CleaningConfig, MissingValuePolicy
from src.identity.context import UserContext
from src.identity.permissions import Permission

router = APIRouter(
    prefix="/governance",
    tags=["Governance"],
)


# ==========================================================
# Non-Destructive Preview Endpoint
# ==========================================================


@router.post(
    "/preview",
    response_model=CleaningPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Non-Destructive Cleaning Preview",
    description=(
        "Simulates cleaning transformations and calculates quality metrics "
        "without persisting artifacts or creating pipeline run records."
    ),
)
def preview_cleaning(
    request: CleaningPreviewRequest,
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(get_application),
) -> CleaningPreviewResponse:
    # 1. Resolve source DataFrame from registered immutable DatasetVersion
    if application.persistence.dataset_version_repository is None:
        application.persistence.initialize()

    repo = application.persistence.dataset_version_repository
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Governance repository uninitialized.",
        )
    is_admin = context.has_permission(Permission.USER_MANAGE)
    scoped_uid = None if is_admin else context.user_id

    version_row = repo.get_by_version_id(request.dataset_version_id, user_id=scoped_uid)
    if not version_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DatasetVersion '{request.dataset_version_id}' not found.",
        )
    storage_path = version_row["storage_path"]
    from src.upload.upload_manager import UploadManager
    raw_df = UploadManager().upload(storage_path)

    # 2. Build transient CleaningConfig

    cfg_req = request.cleaning_config
    try:
        policy_enum = MissingValuePolicy(cfg_req.missing_value_policy)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid missing value policy: {cfg_req.missing_value_policy}",
        ) from exc

    config = CleaningConfig(
        config_id=str(uuid.uuid4()),
        missing_value_policy=policy_enum,
        null_threshold=cfg_req.null_threshold,
        fill_value=cfg_req.fill_value,
        affected_columns=cfg_req.affected_columns,
        custom_strategy_name=cfg_req.custom_strategy_name,
        custom_params=cfg_req.custom_params,
        user_id=context.user_id,
    )

    # 3. Execute non-destructive preview
    try:
        preview_res = application.preview_service.preview(
            raw_dataframe=raw_df,
            config=config,
            sample_rows=request.sample_rows,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preview failed: {exc}",
        ) from exc

    cmp = preview_res.quality_comparison
    return CleaningPreviewResponse(
        quality_comparison=QualityComparisonResponse(
            rows_removed=cmp.rows_removed,
            pct_rows_removed=cmp.pct_rows_removed,
            missing_values_resolved=cmp.missing_values_resolved,
            completeness_gain=cmp.completeness_gain,
            has_material_loss=cmp.has_material_loss,
            source_completeness_pct=cmp.source.completeness_percentage,
            cleaned_completeness_pct=cmp.cleaned.completeness_percentage,
        ),
        columns_removed=preview_res.columns_removed,
        affected_columns_detail=preview_res.affected_columns_detail,
        preview_sample_source=preview_res.preview_sample_source,
        preview_sample_cleaned=preview_res.preview_sample_cleaned,
    )


# ==========================================================
# Dataset Version Catalog
# ==========================================================


@router.get(
    "/dataset-versions",
    response_model=list[DatasetVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Dataset Versions",
)
def list_dataset_versions(
    is_source: bool | None = None,
    context: UserContext = Depends(require_permission(Permission.REPORT_VIEW)),
    application: Application = Depends(get_application),
) -> list[DatasetVersionResponse]:
    is_admin = context.has_permission(Permission.USER_MANAGE)
    scoped_user_id = None if is_admin else context.user_id

    repo = application.persistence.dataset_version_repository
    if repo is None:
        return []

    rows = repo.get_all(user_id=scoped_user_id, is_source=is_source)
    return [_dataset_version_row_to_response(r) for r in rows]


@router.get(
    "/dataset-versions/{version_id}",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dataset Version",
)
def get_dataset_version(
    version_id: str,
    context: UserContext = Depends(require_permission(Permission.REPORT_VIEW)),
    application: Application = Depends(get_application),
) -> DatasetVersionResponse:
    is_admin = context.has_permission(Permission.USER_MANAGE)
    scoped_user_id = None if is_admin else context.user_id

    repo = application.persistence.dataset_version_repository
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Governance persistence not initialized.",
        )

    row = repo.get_by_version_id(version_id, user_id=scoped_user_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset version '{version_id}' not found.",
        )
    return _dataset_version_row_to_response(row)


# ==========================================================
# Lineage Endpoints
# ==========================================================


@router.get(
    "/lineage/run/{pipeline_run_id}",
    response_model=LineageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Pipeline Run Lineage",
)
def get_pipeline_run_lineage(
    pipeline_run_id: int,
    context: UserContext = Depends(require_permission(Permission.REPORT_VIEW)),
    application: Application = Depends(get_application),
) -> LineageResponse:
    is_admin = context.has_permission(Permission.USER_MANAGE)
    scoped_user_id = None if is_admin else context.user_id

    dv_repo = application.persistence.dataset_version_repository
    cc_repo = application.persistence.cleaning_config_repository
    ce_repo = application.persistence.cleaning_execution_repository

    if None in (dv_repo, cc_repo, ce_repo):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Governance persistence not initialized.",
        )

    exec_row = ce_repo.get_by_pipeline_run(pipeline_run_id, user_id=scoped_user_id)
    if not exec_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No lineage found for pipeline_run_id {pipeline_run_id}",
        )

    src_row = dv_repo.get_by_version_id(exec_row["source_version_id"], user_id=scoped_user_id)
    clean_row = (
        dv_repo.get_by_version_id(exec_row["cleaned_version_id"], user_id=scoped_user_id)
        if exec_row.get("cleaned_version_id")
        else None
    )
    cfg_row = cc_repo.get_by_config_id(exec_row["config_id"], user_id=scoped_user_id)

    return LineageResponse(
        source_dataset_version=_dataset_version_row_to_response(src_row) if src_row else None,
        cleaned_dataset_version=_dataset_version_row_to_response(clean_row) if clean_row else None,
        cleaning_config=_config_row_to_response(cfg_row) if cfg_row else None,
        cleaning_execution=_execution_row_to_response(exec_row),
    )


# ==========================================================
# Helpers
# ==========================================================


def _dataset_version_row_to_response(row: dict) -> DatasetVersionResponse:
    is_source_val = row.get("is_source", 1)
    return DatasetVersionResponse(
        version_id=row["version_id"],
        source_filename=row.get("source_filename", ""),
        content_type=row.get("content_type", "text/csv"),
        byte_size=row.get("byte_size", 0),
        checksum_sha256=row.get("checksum_sha256", ""),
        row_count=row.get("row_count", 0),
        column_count=row.get("column_count", 0),
        is_source=bool(is_source_val),
        storage_path=row.get("storage_path", ""),
        parent_version_id=row.get("parent_version_id"),
        dataset_schema_json=row.get("schema_json"),
        created_at=str(row.get("created_at", "")),
    )



def _config_row_to_response(row: dict) -> CleaningConfigResponse:
    return CleaningConfigResponse(
        config_id=row["config_id"],
        missing_value_policy=row.get("missing_value_policy", "DROP_ROWS"),
        config_version=row.get("config_version", 1),
        null_threshold=row.get("null_threshold"),
        fill_value=row.get("fill_value"),
        affected_columns=row.get("affected_columns"),
        custom_strategy_name=row.get("custom_strategy_name"),
        custom_params_json=row.get("custom_params_json"),
        created_at=str(row.get("created_at", "")),
    )


def _execution_row_to_response(row: dict) -> CleaningExecutionResponse:
    return CleaningExecutionResponse(
        execution_id=row["execution_id"],
        source_version_id=row.get("source_version_id", ""),
        cleaned_version_id=row.get("cleaned_version_id"),
        config_id=row.get("config_id", ""),
        execution_status=row.get("execution_status", "SUCCESS"),
        source_row_count=row.get("source_row_count", 0),
        pipeline_run_id=row.get("pipeline_run_id"),
        cleaned_row_count=row.get("cleaned_row_count"),
        rows_removed=row.get("rows_removed"),
        pct_rows_removed=row.get("pct_rows_removed"),
        source_missing_count=row.get("source_missing_count"),
        cleaned_missing_count=row.get("cleaned_missing_count"),
        source_completeness_pct=row.get("source_completeness_pct"),
        cleaned_completeness_pct=row.get("cleaned_completeness_pct"),
        columns_removed=row.get("columns_removed"),
        affected_columns_detail=row.get("affected_columns_detail"),
        error_message=row.get("error_message"),
        execution_time_seconds=row.get("execution_time_seconds"),
        executed_at=str(row.get("executed_at", "")),
    )
