"""
Pipeline execution endpoint.

Responsibilities
----------------
- Accept pipeline execution requests.
- Invoke the Application orchestration layer.
- Return standardized API responses.

This module intentionally contains no business logic.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.dependencies.auth_dependencies import (
    require_permission,
)
from src.api.models.request_models import (
    PipelineRequest,
)
from src.api.models.response_models import (
    AIReportResponse,
    PipelineResponse,
)
from src.application.app import Application
from src.identity.context import UserContext
from src.identity.permissions import Permission


router = APIRouter(
    tags=["Pipeline"],
)


@router.post(
    "/pipeline",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Pipeline",
    description=(
        "Execute the complete AnalystGPT Enterprise "
        "analytics pipeline."
    ),
)
def execute_pipeline(
    request: PipelineRequest,
    context: UserContext = Depends(
        require_permission(Permission.PIPELINE_EXECUTE),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> PipelineResponse:
    """
    Execute the complete analytics pipeline.
    """

    result = application.run(
        input_path=request.input_path,
        user_context=context,
    )

    ai_response: AIReportResponse | None = None

    if (
        result.pipeline_report is not None
        and result.pipeline_report.ai_report is not None
    ):

        ai = result.pipeline_report.ai_report

        ai_response = AIReportResponse(
            executive_summary=ai.executive_summary,
            recommendations=ai.recommendations,
            explanations=ai.explanations,
            narrative=ai.narrative,
            model=ai.model,
            provider=ai.provider,
            execution_time=ai.execution_time,
        )

    return PipelineResponse(
        success=result.success,
        output_path=result.output_path,
        execution_time=result.execution_time or 0.0,
        ai_report=ai_response,
        error=(
            str(result.error)
            if result.error
            else None
        ),
    )