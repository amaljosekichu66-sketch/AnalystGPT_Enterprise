"""
Reports API routes for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose reporting-related REST endpoints.
- Delegate orchestration to the Application Layer.

This module intentionally contains NO business logic.
"""

from fastapi import APIRouter

from src.api.models.response_models import APIResponse
from src.application.reporting_orchestrator import (
    ReportingOrchestrator,
)

router = APIRouter(
    tags=["Reports"],
)

reporting_orchestrator = ReportingOrchestrator()


@router.get(
    "/reports",
    response_model=APIResponse,
)
def get_reports() -> APIResponse:
    """
    Return available report information.
    """

    report_data = (
        reporting_orchestrator.get_reports()
    )

    return APIResponse(
        success=True,
        message="Reports retrieved successfully.",
        data=report_data,
    )