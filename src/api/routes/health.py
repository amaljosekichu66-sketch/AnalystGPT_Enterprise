"""
Health API endpoint for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose the API health endpoint.
- Report the current health status of the API.

This module intentionally contains no business logic.
"""

from fastapi import APIRouter, status

from src.api.models.response_models import HealthResponse

from src.core.constants import (
    HEALTH_STATUS,
)

# ==========================================================
# Router Configuration
# ==========================================================

router = APIRouter(
    tags=["Health"],
)

# ==========================================================
# Health Endpoint
# ==========================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the current health status of the AnalystGPT Enterprise API.",
)
def get_health() -> HealthResponse:
    """
    Return the current API health status.
    """

    return HealthResponse(
        status=HEALTH_STATUS,
    )