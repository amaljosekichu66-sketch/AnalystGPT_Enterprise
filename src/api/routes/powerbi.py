"""
Power BI API routes.

Provides optimized endpoints for Power BI dashboards.
"""

from fastapi import APIRouter, Depends, Query

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.application.app import Application
from src.integrations.powerbi.dashboard_service import (
    DashboardService,
)

router = APIRouter(
    prefix="/powerbi",
    tags=["Power BI"],
)

dashboard_service = DashboardService()


def execute_pipeline(
    dataset: str,
    application: Application,
):
    """
    Execute the complete analytics pipeline.
    """

    return application.run(
        input_path=dataset,
    )


@router.get("/dashboard")
def dashboard(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_dashboard_response(
        result,
    )


@router.get("/summary")
def summary(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_dashboard_summary(
        result,
    )


@router.get("/statistics")
def statistics(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_statistics(
        result,
    )


@router.get("/correlation")
def correlation(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_correlation(
        result,
    )


@router.get("/distribution")
def distribution(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_distribution(
        result,
    )


@router.get("/categorical")
def categorical(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_categorical(
        result,
    )


@router.get("/report")
def report(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_report(
        result,
    )


@router.get("/pipeline")
def pipeline(
    dataset: str = Query(...),
    application: Application = Depends(
        get_application,
    ),
):

    result = execute_pipeline(
        dataset,
        application,
    )

    return dashboard_service.build_pipeline_summary(
        result,
    )