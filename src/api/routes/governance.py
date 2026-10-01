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
from src.api.exceptions.exception_handlers import internal_error_message
from src.api.models.governance_models import (
    CleaningConfigRequest,
    CleaningConfigResponse,
    CleaningExecutionResponse,
    CleaningPreviewRequest,
    CleaningPreviewResponse,
    DatasetVersionResponse,
    LineageResponse,
    PolicyModifyRequest,
    PolicyProposalRequest,
    PolicyProposalResponse,
    PolicyReviewRequest,
    QualityComparisonResponse,
)
from src.api.rate_limit import rate_limit
from src.api.request_context import current_request_id
from src.application.app import Application
from src.core import config as core_config
from src.core.exceptions import DatasetNotFoundError
from src.core.logger import logger
from src.governance.models import CleaningConfig, MissingValuePolicy
from src.governance.policy_approval import PolicyApprovalService
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
    dependencies=[Depends(rate_limit("governance_preview", lambda: core_config.GOVERNANCE_PREVIEW_RATE_LIMIT))],
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
    # 1. Resolve source DataFrame from registered immutable DatasetVersion.
    #    Ownership and managed-store containment are enforced by the resolver.
    try:
        source_version = application.resolve_source_version(request.dataset_version_id, user_context=context)
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DatasetVersion '{request.dataset_version_id}' not found.",
        ) from exc

    # Parsing and cleaning the whole dataset is as expensive as a pipeline
    # stage: hold one of the caller's job slots for it (M6).
    with application.job_slot(context):
        return _run_preview(request, context, application, source_version)


def _run_preview(
    request: CleaningPreviewRequest,
    context: UserContext,
    application: Application,
    source_version,
) -> CleaningPreviewResponse:
    raw_df = application.load_source_dataframe(source_version)

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
        logger.error("Cleaning preview failed [request_id=%s]: %s", current_request_id(), exc, exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preview failed. {internal_error_message()}",
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

    with application.persistence_session() as persistence:
        rows = persistence.dataset_version_repository.get_all(user_id=scoped_user_id, is_source=is_source)
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

    with application.persistence_session() as persistence:
        row = persistence.dataset_version_repository.get_by_version_id(version_id, user_id=scoped_user_id)
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

    with application.persistence_session() as persistence:
        dv_repo = persistence.dataset_version_repository
        cc_repo = persistence.cleaning_config_repository
        ce_repo = persistence.cleaning_execution_repository

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
        proposal_id=row.get("proposal_id"),
        approved_by=row.get("approved_by"),
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
        # Rows written before P2-13 may hold raw exception text: never return it.
        error_message="Cleaning failed." if row.get("error_message") else None,
        execution_time_seconds=row.get("execution_time_seconds"),
        executed_at=str(row.get("executed_at", "")),
    )


# ==========================================================
# Cleaning policy proposals and approval (P2-04)
# ==========================================================

_policy_service = PolicyApprovalService()


def _policy(value: str) -> MissingValuePolicy:
    try:
        return MissingValuePolicy(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown cleaning policy: {value}"
        ) from exc


def _proposal_response(row: dict) -> PolicyProposalResponse:
    return PolicyProposalResponse(
        proposal_id=row["proposal_id"],
        dataset_version_id=row["dataset_version_id"],
        missing_value_policy=row["missing_value_policy"],
        null_threshold=row.get("null_threshold"),
        fill_value=row.get("fill_value"),
        status=row["status"],
        proposed_by=row.get("user_id"),
        modified_by=row.get("modified_by"),
        reviewed_by=row.get("reviewed_by"),
        review_note=row.get("review_note"),
        created_at=row.get("created_at"),
        reviewed_at=row.get("reviewed_at"),
    )


@router.post(
    "/policies",
    response_model=PolicyProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Propose a Cleaning Policy",
    description="Propose a cleaning policy for one of your datasets. It runs only once approved.",
)
def propose_policy(
    request: PolicyProposalRequest,
    context: UserContext = Depends(require_permission(Permission.PIPELINE_EXECUTE)),
    application: Application = Depends(get_application),
) -> PolicyProposalResponse:
    # Ownership: an unknown or foreign dataset is a 404 (DatasetNotFoundError).
    application.resolve_source_version(request.dataset_version_id, user_context=context)
    row = _policy_service.propose(
        request.dataset_version_id,
        _policy(request.missing_value_policy),
        context,
        null_threshold=request.null_threshold,
        fill_value=request.fill_value,
    )
    return _proposal_response(row)


@router.get(
    "/policies",
    response_model=list[PolicyProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="List Cleaning Policy Proposals",
)
def list_policies(
    dataset_version_id: str | None = None,
    context: UserContext = Depends(require_permission(Permission.REPORT_VIEW)),
) -> list[PolicyProposalResponse]:
    return [_proposal_response(row) for row in _policy_service.list_for(context, dataset_version_id)]


@router.patch(
    "/policies/{proposal_id}",
    response_model=PolicyProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Modify a Proposed Cleaning Policy",
)
def modify_policy(
    proposal_id: str,
    request: PolicyModifyRequest,
    context: UserContext = Depends(require_permission(Permission.PIPELINE_EXECUTE)),
) -> PolicyProposalResponse:
    row = _policy_service.modify(
        proposal_id,
        _policy(request.missing_value_policy),
        context,
        null_threshold=request.null_threshold,
        fill_value=request.fill_value,
    )
    return _proposal_response(row)


@router.post(
    "/policies/{proposal_id}/approve",
    response_model=PolicyProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a Cleaning Policy",
)
def approve_policy(
    proposal_id: str,
    request: PolicyReviewRequest | None = None,
    context: UserContext = Depends(require_permission(Permission.PIPELINE_EXECUTE)),
) -> PolicyProposalResponse:
    return _proposal_response(_policy_service.approve(proposal_id, context, note=request.note if request else None))


@router.post(
    "/policies/{proposal_id}/reject",
    response_model=PolicyProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a Cleaning Policy",
)
def reject_policy(
    proposal_id: str,
    request: PolicyReviewRequest | None = None,
    context: UserContext = Depends(require_permission(Permission.PIPELINE_EXECUTE)),
) -> PolicyProposalResponse:
    return _proposal_response(_policy_service.reject(proposal_id, context, note=request.note if request else None))
