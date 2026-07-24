"""
Dashboard API routes for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose dashboard-related REST endpoints.
- Delegate orchestration to the Application Layer.

This module intentionally contains NO business logic.
"""

from fastapi import APIRouter

from src.api.models.response_models import APIResponse
from src.application.dashboard_orchestrator import (
    DashboardOrchestrator,
)

router = APIRouter(
    tags=["Dashboard"],
)

dashboard_orchestrator = DashboardOrchestrator()


@router.get(
    "/dashboard",
    response_model=APIResponse,
)
def get_dashboard() -> APIResponse:
    """
    Return dashboard information.
    """

    dashboard_data = (
        dashboard_orchestrator.get_dashboard()
    )

    return APIResponse(
        success=True,
        message="Dashboard data retrieved successfully.",
        data=dashboard_data,
    )