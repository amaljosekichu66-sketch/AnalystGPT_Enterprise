"""
Reports API routes for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose reporting-related REST endpoints.
- Provide secure text and PDF export streaming.
- Enforce Role-Based Access Control and multi-user tenant scoping.
- Delegate orchestration to the Application Layer.

This module intentionally contains no business logic.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.dependencies.auth_dependencies import (
    require_permission,
)
from src.api.models.response_models import (
    ErrorResponse,
    ReportDataResponse,
    ReportsListResponse,
)
from src.application.app import Application
from src.application.reporting_orchestrator import (
    ReportingOrchestrator,
)
from src.identity.audit import get_audit_service
from src.identity.context import UserContext
from src.identity.exceptions import AuthenticationError
from src.identity.models import AuditEventType
from src.identity.permissions import Permission

_UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]")


def _serve_export(result: dict, media_type: str, context: UserContext) -> Response:
    """
    Return an export's bytes, delete a per-request file at once, and audit it.

    FileResponse deleted the per-request file (SEC-12) in a BackgroundTask,
    which never ran when the client sent a malformed Range header or
    disconnected: export_<uuid> files piled up outside the account purge
    (L15). Reports are small text and PDF files, so they are read into
    memory and the file is removed before the response is sent. Every
    export is recorded in the audit trail (L13).
    """
    file_path = Path(result["path"])
    try:
        content = file_path.read_bytes()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exported report file not found on disk.",
        ) from exc
    finally:
        if result.get("ephemeral"):
            file_path.unlink(missing_ok=True)

    get_audit_service().record_event(
        event_type=AuditEventType.REPORT_EXPORTED,
        action="REPORT_EXPORT",
        actor_id=context.user_id,
        actor_username=context.username,
        target_id=result.get("report_id"),
        target_resource="REPORT",
        outcome="SUCCESS",
        details={"format": media_type, "bytes": len(content)},
    )

    filename = _UNSAFE_FILENAME.sub("_", str(result.get("filename") or file_path.name))
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


router = APIRouter(
    tags=["Reports"],
)


@router.get(
    "/reports",
    response_model=ReportsListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
    summary="Latest Reports",
    description=("Return metadata for the most recently " "generated reporting and AI results."),
)
def get_reports(
    context: UserContext = Depends(
        require_permission(Permission.REPORT_VIEW),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> ReportsListResponse:
    """
    Return the latest generated reports.
    """
    # Never unscoped (I16): None used to mean "everyone's latest report".
    if not context.is_authenticated or context.user_id is None:
        raise AuthenticationError("Authentication required to access this resource.")

    orchestrator = ReportingOrchestrator(
        application,
    )

    report_data = orchestrator.get_reports(
        user_id=context.user_id,
    )

    return ReportsListResponse(
        success=True,
        message=("Reports retrieved successfully."),
        data=ReportDataResponse(
            reports=report_data.get("reports", []),
            report=report_data.get("report"),
            ai_report=report_data.get("ai_report"),
            execution_time=report_data.get("execution_time"),
            output_path=report_data.get("output_path"),
        ),
    )


@router.get(
    "/reports/export/text",
    responses={
        200: {
            "content": {"text/plain": {}},
            "description": "Plain-text report file stream",
        },
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "No generated report found"},
    },
    summary="Export Latest Text Report",
    description="Stream the plain-text report artifact for the latest pipeline execution.",
)
@router.get(
    "/reports/latest/export/text",
    responses={
        200: {
            "content": {"text/plain": {}},
            "description": "Plain-text report file stream",
        },
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "No generated report found"},
    },
    summary="Export Latest Text Report (Alias)",
    description="Stream the plain-text report artifact for the latest pipeline execution.",
)
def export_latest_text_report(
    context: UserContext = Depends(
        require_permission(Permission.REPORT_EXPORT),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> Response:
    """
    Export and stream the latest text report artifact.
    """
    user_id = context.user_id if context.is_authenticated else None
    orchestrator = ReportingOrchestrator(application)

    # Rendering an export (PDF especially) is heavy: hold a job slot (P2-12).
    with application.job_slot(context):
        result = orchestrator.export_text_report(
            user_id=user_id,
        )

    if not result.get("success") or not result.get("path"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "No generated report found to export."),
        )

    return _serve_export(result, "text/plain", context)


@router.get(
    "/reports/{report_id}/export/text",
    responses={
        200: {
            "content": {"text/plain": {}},
            "description": "Plain-text report file stream",
        },
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Report not found or access denied"},
    },
    summary="Export Text Report by ID",
    description="Stream the plain-text report artifact for a specific report ID.",
)
def export_text_report_by_id(
    report_id: int,
    context: UserContext = Depends(
        require_permission(Permission.REPORT_EXPORT),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> Response:
    """
    Export and stream a text report artifact for an identified report.
    """
    user_id = context.user_id if context.is_authenticated else None
    orchestrator = ReportingOrchestrator(application)

    # Rendering an export (PDF especially) is heavy: hold a job slot (P2-12).
    with application.job_slot(context):
        result = orchestrator.export_text_report(
            user_id=user_id,
            report_id=report_id,
        )

    if not result.get("success") or not result.get("path"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Report not found or access denied."),
        )

    return _serve_export(result, "text/plain", context)


@router.get(
    "/reports/export/pdf",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Formatted PDF report file stream",
        },
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "No generated report found"},
    },
    summary="Export Latest PDF Report",
    description="Stream the formatted PDF report artifact for the latest pipeline execution.",
)
@router.get(
    "/reports/latest/export/pdf",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Formatted PDF report file stream",
        },
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "No generated report found"},
    },
    summary="Export Latest PDF Report (Alias)",
    description="Stream the formatted PDF report artifact for the latest pipeline execution.",
)
def export_latest_pdf_report(
    context: UserContext = Depends(
        require_permission(Permission.REPORT_EXPORT),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> Response:
    """
    Export and stream the latest PDF report artifact.
    """
    user_id = context.user_id if context.is_authenticated else None
    orchestrator = ReportingOrchestrator(application)

    # Rendering an export (PDF especially) is heavy: hold a job slot (P2-12).
    with application.job_slot(context):
        result = orchestrator.export_pdf_report(
            user_id=user_id,
        )

    if not result.get("success") or not result.get("path"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "No generated report was found to export as PDF."),
        )

    return _serve_export(result, "application/pdf", context)


@router.get(
    "/reports/{report_id}/export/pdf",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Formatted PDF report file stream",
        },
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Report not found or access denied"},
    },
    summary="Export PDF Report by ID",
    description="Stream the formatted PDF report artifact for a specific report ID.",
)
def export_pdf_report_by_id(
    report_id: int,
    context: UserContext = Depends(
        require_permission(Permission.REPORT_EXPORT),
    ),
    application: Application = Depends(
        get_application,
    ),
) -> Response:
    """
    Export and stream a PDF report artifact for an identified report.
    """
    user_id = context.user_id if context.is_authenticated else None
    orchestrator = ReportingOrchestrator(application)

    # Rendering an export (PDF especially) is heavy: hold a job slot (P2-12).
    with application.job_slot(context):
        result = orchestrator.export_pdf_report(
            user_id=user_id,
            report_id=report_id,
        )

    if not result.get("success") or not result.get("path"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Report not found or access denied."),
        )

    return _serve_export(result, "application/pdf", context)
