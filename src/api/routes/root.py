"""
Root API endpoint for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose the API root endpoint.
- Provide basic API discovery information.
- Direct users to the API documentation.

This module intentionally contains no business logic.
"""

from fastapi import APIRouter, status

from src.api.models.response_models import RootResponse

from src.core.constants import (
    APP_NAME,
    APP_VERSION,
    API_DOCS_URL,
    APP_STATUS,
)


# ==========================================================
# Router Configuration
# ==========================================================

router = APIRouter(
    tags=["Root"],
)


# ==========================================================
# Root Endpoint
# ==========================================================

@router.get(
    "/",
    response_model=RootResponse,
    status_code=status.HTTP_200_OK,
    summary="API Root",
    description="Returns basic information about the AnalystGPT Enterprise API.",
)
def get_root() -> RootResponse:
    """
    Return basic API information.
    """

    return RootResponse(
        application=APP_NAME,
        version=APP_VERSION,
        status=APP_STATUS,
        documentation=API_DOCS_URL,
    )