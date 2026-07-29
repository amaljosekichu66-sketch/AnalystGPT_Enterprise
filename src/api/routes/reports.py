"""
Reports API routes for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose reporting-related REST endpoints.
- Delegate orchestration to the Application Layer.

This module intentionally contains no business logic.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.models.response_models import (
    APIResponse,
)
from src.application.app import Application
from src.application.reporting_orchestrator import (
    ReportingOrchestrator,
)


router = APIRouter(
    tags=["Reports"],
)


@router.get(
    "/reports",
    response_model=APIResponse,
    summary="Latest Reports",
    description=(
        "Return metadata for the most recently "
        "generated reporting and AI results."
    ),
)
def get_reports(
    application: Application = Depends(
        get_application,
    ),
) -> APIResponse:
    """
    Return the latest generated reports.
    """

    orchestrator = ReportingOrchestrator(
        application,
    )

    report_data = orchestrator.get_reports()

    return APIResponse(
        success=True,
        message=(
            "Reports retrieved successfully."
        ),
        data=report_data,
    )