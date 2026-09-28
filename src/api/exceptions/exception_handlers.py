"""
Global exception handlers for AnalystGPT Enterprise REST API.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.api.rate_limit import RateLimitExceededError
from src.api.request_context import REQUEST_ID_HEADER, current_request_id
from src.core.exceptions import DatasetNotFoundError, PipelineResultNotFoundError, TooManyConcurrentJobsError
from src.core.logger import logger
from src.core.redaction import redact_server_paths
from src.identity.exceptions import (
    AccountLockedError,
    AdminOperationError,
    AuthenticationError,
    AuthorizationError,
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserDisabledError,
    UserNotFoundError,
)
from src.identity.password_policy import WeakPasswordError
from src.upload.upload_policy import UploadRejectedError


def _error_response(
    status_code: int,
    message: str,
    error: str,
) -> JSONResponse:
    """
    Build a consistent error response.

    Args:
        status_code: HTTP status code.
        message: Human-readable error message.
        error: Technical error details.

    Returns:
        JSONResponse with consistent error structure.

    Every error body passes through here, so this is where server
    filesystem paths are scrubbed from exception text, and where the request
    id (SEC-11) is attached to the body and the `X-Request-ID` header.
    """
    request_id = current_request_id()
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": redact_server_paths(message),
            "error": redact_server_paths(error),
            "request_id": request_id,
        },
        headers={REQUEST_ID_HEADER: request_id} if request_id else None,
    )


def internal_error_message(request_id: str | None = None) -> str:
    """Client-facing text for an unexpected failure; details stay in the server log."""
    request_id = request_id or current_request_id()
    suffix = f" Reference: {request_id}." if request_id else ""
    return f"An unexpected error occurred.{suffix}"


def _log_unexpected(exc: BaseException, where: str) -> None:
    logger.error(
        "Unexpected error in %s [request_id=%s]: %s: %s",
        where,
        current_request_id(),
        type(exc).__name__,
        exc,
        exc_info=exc,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers.
    """

    @app.exception_handler(AccountLockedError)
    async def account_locked_handler(
        _request: Request,
        exc: AccountLockedError,
    ) -> JSONResponse:
        response = _error_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts.",
            str(exc),
        )
        response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @app.exception_handler(RateLimitExceededError)
    async def rate_limited_handler(
        _request: Request,
        exc: RateLimitExceededError,
    ) -> JSONResponse:
        response = _error_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many requests.",
            str(exc),
        )
        response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        _request: Request,
        exc: AuthenticationError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Authentication failed.",
            str(exc),
        )

    @app.exception_handler(UserDisabledError)
    async def user_disabled_error_handler(
        _request: Request,
        exc: UserDisabledError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_403_FORBIDDEN,
            "User account disabled or inactive.",
            str(exc),
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_error_handler(
        _request: Request,
        exc: PermissionDeniedError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_403_FORBIDDEN,
            "Permission denied.",
            str(exc),
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        _request: Request,
        exc: AuthorizationError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_403_FORBIDDEN,
            "Authorization failed.",
            str(exc),
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_error_handler(
        _request: Request,
        exc: UserNotFoundError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            "User not found.",
            str(exc),
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_error_handler(
        _request: Request,
        exc: UserAlreadyExistsError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_409_CONFLICT,
            "User already exists.",
            str(exc),
        )

    @app.exception_handler(DatasetNotFoundError)
    async def dataset_not_found_handler(
        _request: Request,
        exc: DatasetNotFoundError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            "Dataset not found.",
            str(exc),
        )

    @app.exception_handler(PipelineResultNotFoundError)
    async def pipeline_result_not_found_handler(
        _request: Request,
        exc: PipelineResultNotFoundError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            "Pipeline result not found.",
            str(exc),
        )

    @app.exception_handler(TooManyConcurrentJobsError)
    async def too_many_jobs_handler(
        _request: Request,
        exc: TooManyConcurrentJobsError,
    ) -> JSONResponse:
        response = _error_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many jobs in progress.",
            str(exc),
        )
        response.headers["Retry-After"] = "5"
        return response

    @app.exception_handler(UploadRejectedError)
    async def upload_rejected_handler(
        _request: Request,
        exc: UploadRejectedError,
    ) -> JSONResponse:
        return _error_response(
            exc.status_code,
            "Upload rejected.",
            str(exc),
        )

    @app.exception_handler(WeakPasswordError)
    async def weak_password_handler(
        _request: Request,
        exc: WeakPasswordError,
    ) -> JSONResponse:
        # Intentional, user-facing policy message.
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "Password does not meet the password policy.",
            str(exc),
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(
        _request: Request,
        exc: FileNotFoundError,
    ) -> JSONResponse:
        # The message of an OS-level FileNotFoundError names server files.
        _log_unexpected(exc, "file lookup")
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            "Resource not found.",
            internal_error_message(),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        _request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        # A bare ValueError here comes from library or pipeline internals
        # (intentional client errors have their own handlers above), so its
        # text is logged, not returned.
        _log_unexpected(exc, "request validation")
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "Invalid request.",
            internal_error_message(),
        )

    @app.exception_handler(AdminOperationError)
    async def admin_operation_error_handler(
        _request: Request,
        exc: AdminOperationError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "Administrative safety violation.",
            str(exc),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        return _error_response(
            exc.status_code,
            str(exc.detail),
            str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        _log_unexpected(exc, "request handling")
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error.",
            internal_error_message(),
        )
