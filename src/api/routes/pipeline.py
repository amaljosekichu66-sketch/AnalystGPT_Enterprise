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

from fastapi import APIRouter, Depends, status

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.dependencies.auth_dependencies import (
    require_permission,
)
from src.api.exceptions.exception_handlers import internal_error_message
from src.api.models.request_models import (
    PipelineRequest,
)
from src.api.models.response_models import (
    AIReportResponse,
    PipelineResponse,
)
from src.api.rate_limit import rate_limit
from src.application.app import Application
from src.core import config
from src.core.redaction import public_artifact_name, redact_server_paths
from src.governance.policy_approval import PolicyApprovalService
from src.identity.audit import get_audit_service
from src.identity.context import UserContext
from src.identity.models import AuditEventType
from src.identity.permissions import Permission

router = APIRouter(
    tags=["Pipeline"],
)


@router.post(
    "/pipeline",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Pipeline",
    description=("Execute the complete AnalystGPT Enterprise " "analytics pipeline."),
    # Every run queues an AI insight job, so it also needs AI_GENERATE (I10).
    dependencies=[
        Depends(rate_limit("pipeline", lambda: config.PIPELINE_RATE_LIMIT)),
        Depends(require_permission(Permission.AI_GENERATE)),
    ],
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
    Execute the complete analytics pipeline on an uploaded dataset.

    The dataset is resolved server-side from `dataset_version_id`, with
    ownership enforced; an unknown or foreign id is a 404.
    """

    # Only an APPROVED proposal for this dataset changes the policy (P2-04).
    cleaning_config = (
        PolicyApprovalService().approved_config(
            request.cleaning_policy_proposal_id, request.dataset_version_id, context
        )
        if request.cleaning_policy_proposal_id
        else None
    )

    result = application.run_dataset_version(
        request.dataset_version_id,
        user_context=context,
        cleaning_config=cleaning_config,
    )

    # Defined since Sprint 13 but never emitted (L13).
    get_audit_service().record_event(
        event_type=AuditEventType.PIPELINE_EXECUTED,
        action="PIPELINE_EXECUTE",
        actor_id=context.user_id,
        actor_username=context.username,
        target_id=result.pipeline_run_id,
        target_resource="PIPELINE_RUN",
        outcome="SUCCESS" if result.success else "FAILED",
        details={"dataset_version_id": request.dataset_version_id},
    )

    ai_response: AIReportResponse | None = None

    if result.pipeline_report is not None and result.pipeline_report.ai_report is not None:

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
        dataset_version_id=result.dataset_version_id or request.dataset_version_id,
        output_path=public_artifact_name(result.output_path),
        execution_time=result.execution_time or 0.0,
        ai_job_id=result.ai_job_id,
        ai_job_status=result.ai_job_status,
        pipeline_run_id=result.pipeline_run_id,
        report_id=result.report_id,
        ai_report=ai_response,
        # The pipeline's exception text (already logged with its traceback)
        # is internal; the caller gets a reference id instead (SEC-11).
        error=(internal_error_message() if result.error else None),
    )
