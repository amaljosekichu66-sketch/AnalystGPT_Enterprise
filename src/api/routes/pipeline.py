"""
Pipeline execution endpoint.

Responsibilities
----------------
- Accept pipeline execution requests.
- Invoke the Application orchestration layer.
- Return standardized API responses.

This module intentionally contains no business logic.
"""

from fastapi import APIRouter, Depends, status

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.models.request_models import PipelineRequest
from src.api.models.response_models import PipelineResponse
from src.application.app import Application


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
        "processing pipeline."
    ),
)
def execute_pipeline(
    request: PipelineRequest,
    application: Application = Depends(get_application),
) -> PipelineResponse:
    """
    Execute the complete analytics pipeline.
    """

    result = application.run(
        input_path=request.input_path,
    )

    return PipelineResponse(
        success=result.success,
        output_path=result.output_path,
        execution_time=result.execution_time,
        error=(
            str(result.error)
            if result.error is not None
            else None
        ),
    )