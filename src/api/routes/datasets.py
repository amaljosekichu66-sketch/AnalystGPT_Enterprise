"""
Dataset upload endpoint.

Endpoints
---------
- POST /api/datasets : Upload a dataset file (multipart/form-data, field `file`)

The client sends bytes, never a server path. The server validates the file
type and size, stores the bytes in the managed artifact store, registers an
owned source DatasetVersion, and returns its `dataset_version_id`. Every
downstream call (pipeline, dashboard, governance preview) refers to the
dataset by that identifier and the server resolves it internally.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from src.api.body_limit import MULTIPART_OVERHEAD_BYTES
from src.api.dependencies.application_dependency import get_application
from src.api.dependencies.auth_dependencies import require_permission
from src.api.models.response_models import (
    DatasetAnalysisResponse,
    DatasetDeleteResponse,
    DatasetUploadResponse,
    ErrorResponse,
)
from src.application.app import Application
from src.identity.audit import get_audit_service
from src.identity.context import UserContext
from src.identity.models import AuditEventType
from src.identity.permissions import Permission
from src.upload.upload_policy import (
    UploadRejectedError,
    check_archive_safety,
    check_declared_size,
    read_bounded,
    require_declared_length,
    validate_upload_filename,
)

router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)

#: Allowance for multipart boundaries and part headers on top of the file itself.
_MULTIPART_OVERHEAD_BYTES = MULTIPART_OVERHEAD_BYTES

_UPLOAD_REQUEST_BODY = {
    "required": True,
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "required": ["file"],
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Dataset file (.csv, .xlsx, .json).",
                    }
                },
            }
        }
    },
}


@router.post(
    "",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
    },
    summary="Upload Dataset",
    description="Upload a dataset file and receive a server-issued dataset_version_id.",
    openapi_extra={"requestBody": _UPLOAD_REQUEST_BODY},
)
async def upload_dataset(
    request: Request,
    context: UserContext = Depends(require_permission(Permission.DATASET_UPLOAD)),
    application: Application = Depends(get_application),
) -> DatasetUploadResponse:
    """
    Accept one uploaded file.

    The body is read here rather than through an `UploadFile` parameter so
    that authorization (the dependency above) and the declared-size check
    both run BEFORE the multipart body is parsed.
    """
    declared = request.headers.get("content-length")
    require_declared_length(declared)
    check_declared_size(int(declared or 0) - _MULTIPART_OVERHEAD_BYTES)

    # The per-user job slot is taken before the body is read (M3), so parallel
    # uploads beyond the cap are refused before they cost memory or disk.
    with application.job_slot(context):
        form = await request.form(max_files=1, max_fields=1)
        try:
            upload = form.get("file")
            if not isinstance(upload, UploadFile):
                raise UploadRejectedError("Expected a multipart form field named 'file'.")

            # Type and size are checked before anything is persisted or parsed.
            filename = validate_upload_filename(upload.filename)
            check_declared_size(upload.size)
            content = await run_in_threadpool(read_bounded, upload.file)
        finally:
            await form.close()

        # Zip-bomb check on the archive directory, before persisting or parsing.
        check_archive_safety(content, filename)

        source_version = await run_in_threadpool(
            application.register_upload,
            content,
            filename,
            context,
            hold_slot=False,
        )

    get_audit_service().record_event(
        event_type=AuditEventType.DATASET_UPLOADED,
        action="DATASET_UPLOAD",
        actor_id=context.user_id,
        actor_username=context.username,
        target_resource="DATASET",
        outcome="SUCCESS",
        details={
            "dataset_version_id": source_version.version_id,
            "byte_size": source_version.byte_size,
            "checksum_sha256": source_version.checksum_sha256,
        },
    )

    return DatasetUploadResponse(
        success=True,
        message="Dataset uploaded.",
        dataset_version_id=source_version.version_id,
        filename=source_version.source_filename,
        content_type=source_version.content_type,
        byte_size=source_version.byte_size,
        checksum_sha256=source_version.checksum_sha256,
        row_count=source_version.row_count,
        column_count=source_version.column_count,
    )


@router.delete(
    "/{dataset_version_id}",
    response_model=DatasetDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Dataset not found"},
    },
    summary="Delete Dataset",
    description="Delete an uploaded dataset and its cleaned versions. Existing reports are kept.",
)
def delete_dataset(
    dataset_version_id: str,
    context: UserContext = Depends(require_permission(Permission.DATASET_UPLOAD)),
    application: Application = Depends(get_application),
) -> DatasetDeleteResponse:
    """
    Delete one of the caller's uploads (an administrator may delete any).
    """
    application.delete_dataset(dataset_version_id, user_context=context)

    get_audit_service().record_event(
        event_type=AuditEventType.DATASET_DELETED,
        action="DATASET_DELETE",
        actor_id=context.user_id,
        actor_username=context.username,
        target_resource="DATASET",
        outcome="SUCCESS",
        details={"dataset_version_id": dataset_version_id},
    )

    return DatasetDeleteResponse(success=True, message="Dataset deleted.", dataset_version_id=dataset_version_id)


@router.get(
    "/{dataset_version_id}/analysis",
    response_model=DatasetAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse, "description": "Dataset not found"}},
    summary="Dataset Analysis",
    description="Semantic profile, planned charts and cleaning-policy recommendation for an uploaded dataset.",
)
def dataset_analysis(
    dataset_version_id: str,
    context: UserContext = Depends(require_permission(Permission.REPORT_VIEW)),
    application: Application = Depends(get_application),
) -> DatasetAnalysisResponse:
    """
    Profile the dataset server-side (P2-05). Holds a job slot: profiling
    parses the whole dataset.
    """
    with application.job_slot(context):
        return DatasetAnalysisResponse(**application.analyse_dataset(dataset_version_id, user_context=context))
