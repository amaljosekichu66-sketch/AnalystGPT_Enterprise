"""
Global exception handlers for AnalystGPT Enterprise REST API.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse


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
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error": error,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers.
    """

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(
        _request: Request,
        exc: FileNotFoundError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            "Dataset not found.",
            str(exc),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        _request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "Invalid request.",
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
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error.",
            str(exc),
        )