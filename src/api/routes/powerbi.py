"""
Power BI API routes.

Provides optimized REST endpoints for Power BI dashboards.

Responsibilities
----------------
- Execute the complete AnalystGPT Enterprise pipeline.
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


# ==========================================================
# Internal Helper
# ==========================================================


def _execute_pipeline(
    dataset: str,
    application: Application,
    context: UserContext | None = None,
) -> PipelineResult:
    """
    Execute the enterprise analytics pipeline.

    Uses the cached PipelineResult whenever possible.
    """

    logger.info("=" * 80)
    logger.info("POWER BI REQUEST")
    logger.info("=" * 80)

    logger.info(
        "Dataset : %s",
        dataset,
    )

    try:
        result = application.get_or_run(
            input_path=dataset,
            user_context=context,
        )
    except TypeError:
        result = application.get_or_run(
            input_path=dataset,
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
    dataset: str = Query(
        ...,
        description="Dataset path.",
    ),
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

    result = _execute_pipeline(
        dataset,
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
    dataset: str = Query(..., description="Dataset path."),
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

    result = _execute_pipeline(
        dataset,
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
    dataset: str = Query(..., description="Dataset path."),
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

    result = _execute_pipeline(
        dataset,
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
    dataset: str = Query(..., description="Dataset path."),
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

    result = _execute_pipeline(
        dataset,
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
    dataset: str = Query(..., description="Dataset path."),
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

    result = _execute_pipeline(
        dataset,
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
    dataset: str = Query(..., description="Dataset path."),
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

    result = _execute_pipeline(
        dataset,
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
    dataset: str = Query(..., description="Dataset path."),
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

    result = _execute_pipeline(
        dataset,
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
    dataset: str = Query(..., description="Dataset path."),
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

    result = _execute_pipeline(
        dataset,
        application,
        context=context,
    )

    return _dashboard_service.build_pipeline_summary(
        result,
    )
