"""
Dashboard API routes for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose dashboard-related REST endpoints.
- Delegate orchestration to the Application Layer.

This module intentionally contains NO business logic.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.application.app import Application
from src.application.dashboard_orchestrator import (
    DashboardOrchestrator,
)
from src.integrations.powerbi.powerbi_models import (
    DashboardResponse,
)

router = APIRouter(
    prefix="/powerbi",
    tags=["Dashboard"],
)


# ==========================================================
# Dependencies
# ==========================================================

def get_dashboard_orchestrator(
    application: Application = Depends(
        get_application,
    ),
) -> DashboardOrchestrator:
    """
    Return the dashboard orchestrator using the shared
    Application singleton.
    """

    return DashboardOrchestrator(
        application=application,
    )


# ==========================================================
# Dashboard
# ==========================================================

@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard",
    description=(
        "Return the complete enterprise dashboard, "
        "including analytics, reporting and AI insights."
    ),
)
async def get_dashboard(
    dataset: str = Query(
        ...,
        description="Absolute path of the dataset.",
    ),
    orchestrator: DashboardOrchestrator = Depends(
        get_dashboard_orchestrator,
    ),
) -> DashboardResponse:
    """
    Return dashboard information.
    """

    try:

        dashboard = orchestrator.get_dashboard(
            dataset,
        )

        pipeline = dashboard["pipeline"]

        return DashboardResponse(
            success=True,
            execution_time=pipeline[
                "execution_time"
            ],
            report=dashboard[
                "report"
            ],
            output_path=pipeline[
                "output_path"
            ],
            ai_report=dashboard[
                "ai_report"
            ],
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ==========================================================
# Status
# ==========================================================

@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Dashboard Status",
)
async def dashboard_status(
    orchestrator: DashboardOrchestrator = Depends(
        get_dashboard_orchestrator,
    ),
) -> dict[str, str]:
    """
    Return dashboard status.
    """

    return orchestrator.get_status()