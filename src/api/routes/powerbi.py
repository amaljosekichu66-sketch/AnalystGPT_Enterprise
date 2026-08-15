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

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.dependencies.auth_dependencies import (
    require_permission,
)
from src.application.app import Application
from src.application.pipeline_result import PipelineResult
from src.core.logger import logger
from src.identity.context import UserContext
from src.identity.permissions import Permission
from src.integrations.powerbi.dashboard_service import (
    DashboardService,
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
    summary="Dashboard",
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
):
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
    summary="Dashboard Summary",
)
def summary(
    dataset: str = Query(...),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
):
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
    summary="Statistics",
)
def statistics(
    dataset: str = Query(...),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
):
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
    summary="Correlation Analysis",
)
def correlation(
    dataset: str = Query(...),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
):
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
    summary="Distribution Analysis",
)
def distribution(
    dataset: str = Query(...),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
):
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
    summary="Categorical Analysis",
)
def categorical(
    dataset: str = Query(...),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
):
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
    summary="Reporting Output",
)
def report(
    dataset: str = Query(...),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
):
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
    summary="Pipeline Summary",
)
def pipeline(
    dataset: str = Query(...),
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
):
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