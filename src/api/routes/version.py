"""
Version API endpoint for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose the API version endpoint.
- Return the current API version.

This module intentionally contains no business logic.
"""

from fastapi import APIRouter, status

from src.api.models.response_models import VersionResponse

from src.core.constants import APP_VERSION


# ==========================================================
# Router Configuration
# ==========================================================

router = APIRouter(
    tags=["Version"],
)


# ==========================================================
# Version Endpoint
# ==========================================================

@router.get(
    "/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="API Version",
    description="Returns the current AnalystGPT Enterprise API version.",
)
def get_version() -> VersionResponse:
    """
    Return the current API version.
    """

    return VersionResponse(
        version=APP_VERSION,
    )