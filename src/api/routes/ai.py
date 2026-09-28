"""
AI API routes for AnalystGPT Enterprise.

Exposes REST endpoints for asynchronous AI job status checking,
report retrieval, and retry execution.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
Sprint 14 Remediation — AI Insights + Enterprise Reporting Reliability Remediation.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.application_dependency import get_application
from src.api.dependencies.auth_dependencies import require_permission
from src.api.models.ai_models import AIJobResponse, AIJobRetryResponse
from src.api.models.response_models import AIReportResponse
from src.application.app import Application
from src.identity.context import UserContext
from src.identity.permissions import Permission

router = APIRouter(
    prefix="/ai",
    tags=["AI Insights"],
)


def _map_ai_report(rep: dict[str, Any] | None) -> AIReportResponse | None:
    if rep is None:
        return None
    return AIReportResponse(
        executive_summary=rep.get("executive_summary", ""),
        recommendations=rep.get("recommendations", []),
        explanations=rep.get("explanations", []),
        narrative=rep.get("narrative", ""),
        model=rep.get("model", ""),
        provider=rep.get("provider", ""),
        execution_time=rep.get("execution_time", 0.0),
        key_findings=rep.get("key_findings", []),
        business_implications=rep.get("business_implications", []),
        risks=rep.get("risks", []),
        opportunities=rep.get("opportunities", []),
        actions=rep.get("actions", []),
        limitations=rep.get("limitations", []),
        confidence=rep.get("confidence") or "Medium — Supported by observed dataset distribution.",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=AIJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI Job Status & Report",
    description=(
        "Retrieve the lifecycle status, attempt count, and generated " "AI insight report for a given AI job ID."
    ),
)
def get_ai_job(
    job_id: str,
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> AIJobResponse:
    """
    Retrieve AI job details by job_id with ownership scoping.
    """
    is_admin = context.has_permission(Permission.USER_MANAGE)
    scoped_user_id = None if is_admin else context.user_id

    job_data = application.ai_job_service.get_job_with_report(
        job_id=job_id,
        user_id=scoped_user_id,
    )

    if job_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI job '{job_id}' not found.",
        )

    return AIJobResponse(
        job_id=job_data["job_id"],
        pipeline_run_id=job_data["pipeline_run_id"],
        status=job_data["status"],
        provider=job_data["provider"],
        model=job_data["model"],
        attempt_count=job_data.get("attempt_count", 0),
        max_attempts=job_data.get("max_attempts", 3),
        error=job_data.get("error"),
        failure_category=job_data.get("failure_category"),
        created_at=job_data.get("created_at"),
        started_at=job_data.get("started_at"),
        completed_at=job_data.get("completed_at"),
        ai_report=_map_ai_report(job_data.get("ai_report")),
    )


@router.get(
    "/jobs/latest/status",
    response_model=AIJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Latest AI Job",
    description="Retrieve the latest AI generation job for the authenticated user.",
)
def get_latest_ai_job(
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> AIJobResponse:
    """
    Retrieve latest AI job for the active user context.
    """
    user_id = context.user_id if context.is_authenticated else None

    job_data = application.ai_job_service.get_latest_job_for_user(
        user_id=user_id,
    )

    if job_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI jobs found for the active user.",
        )

    return AIJobResponse(
        job_id=job_data["job_id"],
        pipeline_run_id=job_data["pipeline_run_id"],
        status=job_data["status"],
        provider=job_data["provider"],
        model=job_data["model"],
        attempt_count=job_data.get("attempt_count", 0),
        max_attempts=job_data.get("max_attempts", 3),
        error=job_data.get("error"),
        failure_category=job_data.get("failure_category"),
        created_at=job_data.get("created_at"),
        started_at=job_data.get("started_at"),
        completed_at=job_data.get("completed_at"),
        ai_report=_map_ai_report(job_data.get("ai_report")),
    )


@router.post(
    "/jobs/{job_id}/retry",
    response_model=AIJobRetryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retry Failed AI Job",
    description="Re-queue a FAILED AI insight generation job for background processing.",
)
def retry_ai_job(
    job_id: str,
    context: UserContext = Depends(
        require_permission(Permission.PIPELINE_EXECUTE),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> AIJobRetryResponse:
    """
    Retry a failed AI generation job.
    """
    is_admin = context.has_permission(Permission.USER_MANAGE)
    scoped_user_id = None if is_admin else context.user_id

    try:
        updated_job = application.ai_job_service.retry_job(
            job_id=job_id,
            user_id=scoped_user_id,
        )
        return AIJobRetryResponse(
            success=True,
            job_id=updated_job.job_id,
            status=updated_job.status.value,
            message="AI job re-queued for execution.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retry AI job: {exc}",
        )
