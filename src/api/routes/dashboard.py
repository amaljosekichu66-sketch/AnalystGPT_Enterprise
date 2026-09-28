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
from src.api.dependencies.auth_dependencies import (
    require_permission,
)
from src.api.exceptions.exception_handlers import internal_error_message
from src.api.models.request_models import DATASET_VERSION_ID_PATTERN
from src.api.models.response_models import (
    DashboardStatusResponse,
)
from src.api.request_context import current_request_id
from src.application.app import Application
from src.application.dashboard_orchestrator import (
    DashboardOrchestrator,
)
from src.core.exceptions import DatasetNotFoundError, PipelineResultNotFoundError
from src.core.logger import logger
from src.identity.context import UserContext
from src.identity.exceptions import IdentityError
from src.identity.permissions import Permission
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
        "Return the complete enterprise dashboard for an already-processed dataset. "
        "Read-only: never executes the pipeline (use POST /api/pipeline)."
    ),
)
async def get_dashboard(
    dataset_version_id: str = Query(
        ...,
        pattern=DATASET_VERSION_ID_PATTERN,
        description="Identifier returned by POST /api/datasets.",
    ),
    context: UserContext = Depends(
        require_permission(Permission.DASHBOARD_VIEW),
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
            dataset_version_id,
            user_context=context,
        )

        pipeline = dashboard["pipeline"]

        return DashboardResponse(
            success=True,
            execution_time=pipeline["execution_time"],
            report=dashboard["report"],
            output_path=pipeline["output_path"],
            ai_report=dashboard["ai_report"],
        )

    except (DatasetNotFoundError, PipelineResultNotFoundError, IdentityError):
        # Ownership / authorization outcomes keep their own status codes.
        raise

    except Exception as exc:

        logger.error("Dashboard failed [request_id=%s]: %s", current_request_id(), exc, exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=internal_error_message(),
        ) from exc


# ==========================================================
# Status
# ==========================================================


@router.get(
    "/status",
    response_model=DashboardStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Dashboard Status",
    description="Return lightweight application and dashboard status.",
)
async def dashboard_status(
    orchestrator: DashboardOrchestrator = Depends(
        get_dashboard_orchestrator,
    ),
) -> DashboardStatusResponse:
    """
    Return dashboard status.
    """

    status_data = orchestrator.get_status()
    return DashboardStatusResponse(
        application=status_data["application"],
        version=status_data["version"],
        status=status_data["status"],
    )
