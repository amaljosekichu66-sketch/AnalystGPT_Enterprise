"""
Power BI API routes.

Provides optimized REST endpoints for Power BI dashboards.

Responsibilities
----------------
- Serve the latest pipeline result for an uploaded dataset. READ-ONLY:
  these routes need only view permissions (which VIEWER holds), so they must
  never execute the pipeline. Execution is `POST /api/pipeline`, gated on
  PIPELINE_EXECUTE.
- Delegate response construction to DashboardService.
- Expose dashboard-friendly analytics and AI insights.

This module intentionally contains no business logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.dependencies.auth_dependencies import (
    require_permission,
)
from src.api.models.request_models import DATASET_VERSION_ID_PATTERN
from src.api.models.response_models import (
    ErrorResponse,
)
from src.application.app import Application
from src.application.pipeline_result import PipelineResult
from src.core.logger import logger
from src.identity.context import UserContext
from src.identity.permissions import Permission
from src.integrations.powerbi.dashboard_categorical import (
    DashboardCategorical,
)
from src.integrations.powerbi.dashboard_correlation import (
    DashboardCorrelation,
)
from src.integrations.powerbi.dashboard_distribution import (
    DashboardDistribution,
)
from src.integrations.powerbi.dashboard_service import (
    DashboardService,
)
from src.integrations.powerbi.dashboard_statistics import (
    DashboardStatistics,
)
from src.integrations.powerbi.dashboard_summary import (
    DashboardSummary,
)
from src.integrations.powerbi.powerbi_models import (
    DashboardResponse,
    PipelineSummary,
    ReportResponse,
)

router = APIRouter(
    prefix="/powerbi",
    tags=["Power BI"],
)

_dashboard_service = DashboardService()

_DATASET_QUERY_HELP = "Identifier returned by POST /api/datasets."


# ==========================================================
# Internal Helper
# ==========================================================


def _load_result(
    dataset_version_id: str,
    application: Application,
    context: UserContext | None = None,
) -> PipelineResult:
    """
    Return the stored pipeline result for this dataset. Never executes.

    404 when the dataset is not the caller's, or has not been run yet.
    """

    logger.info("=" * 80)
    logger.info("POWER BI REQUEST")
    logger.info("=" * 80)

    logger.info(
        "Dataset : %s",
        dataset_version_id,
    )

    result = application.get_result_for_dataset(
        dataset_version_id,
        user_context=context,
    )

    logger.info(
        "Pipeline Success : %s",
        result.success,
    )

    logger.info("=" * 80)

    return result


# ==========================================================
# Dashboard
# ==========================================================


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Dashboard",
    description="Return the complete dashboard response including analytics, reporting, and AI insights.",
)
def dashboard(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.DASHBOARD_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> DashboardResponse:
    """
    Return the complete dashboard response.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_dashboard_response(
        result,
    )


# ==========================================================
# Summary
# ==========================================================


@router.get(
    "/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Dashboard Summary",
    description="Return high-level dashboard metrics (rows, columns, memory usage).",
)
def summary(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> DashboardSummary:
    """
    Return dashboard summary.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_dashboard_summary(
        result,
    )


# ==========================================================
# Statistics
# ==========================================================


@router.get(
    "/statistics",
    response_model=DashboardStatistics,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Statistics",
    description="Return descriptive statistics for numerical columns.",
)
def statistics(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> DashboardStatistics:
    """
    Return descriptive statistics.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_statistics(
        result,
    )


# ==========================================================
# Correlation
# ==========================================================


@router.get(
    "/correlation",
    response_model=DashboardCorrelation,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Correlation Analysis",
    description="Return correlation matrix and strong correlations across numerical columns.",
)
def correlation(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> DashboardCorrelation:
    """
    Return correlation analysis.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_correlation(
        result,
    )


# ==========================================================
# Distribution
# ==========================================================


@router.get(
    "/distribution",
    response_model=DashboardDistribution,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Distribution Analysis",
    description="Return distribution analysis including skewness and kurtosis.",
)
def distribution(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> DashboardDistribution:
    """
    Return distribution analysis.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_distribution(
        result,
    )


# ==========================================================
# Categorical
# ==========================================================


@router.get(
    "/categorical",
    response_model=DashboardCategorical,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Categorical Analysis",
    description="Return unique value counts, top categories, and frequency profiles.",
)
def categorical(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> DashboardCategorical:
    """
    Return categorical analysis.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_categorical(
        result,
    )


# ==========================================================
# Report
# ==========================================================


@router.get(
    "/report",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Reporting Output",
    description="Return full reporting outputs including KPIs, analytical summaries, and AI insights.",
)
def report(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> ReportResponse:
    """
    Return reporting and AI results.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_report(
        result,
    )


# ==========================================================
# Pipeline
# ==========================================================


@router.get(
    "/pipeline",
    response_model=PipelineSummary,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Pipeline Summary",
    description="Return pipeline execution status and metadata.",
)
def pipeline(
    dataset_version_id: str = Query(..., pattern=DATASET_VERSION_ID_PATTERN, description=_DATASET_QUERY_HELP),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> PipelineSummary:
    """
    Return pipeline execution summary.
    """

    result = _load_result(
        dataset_version_id,
        application,
        context=context,
    )

    return _dashboard_service.build_pipeline_summary(
        result,
    )
