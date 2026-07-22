"""
Response models for AnalystGPT Enterprise REST API.

Responsibilities
----------------
- Define standardized API response schemas.
- Provide strongly typed responses for FastAPI endpoints.
- Improve OpenAPI documentation and response validation.

This module intentionally contains no business logic.
"""

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Base Response Model
# ==========================================================

class APIResponse(BaseModel):
    """
    Base envelope for all API responses.

    Provides a consistent structure for success indicators,
    timestamps, and request tracking.
    """

    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        default=True,
        description="Indicates whether the request completed successfully."
    )


# ==========================================================
# Root Endpoint Response
# ==========================================================

class RootResponse(APIResponse):
    """
    Response model for the API root endpoint.
    """

    application: str = Field(
        ...,
        description="Application name."
    )

    version: str = Field(
        ...,
        description="Current API version."
    )

    status: str = Field(
        ...,
        description="Current application status."
    )

    documentation: str = Field(
        ...,
        description="URL to API documentation."
    )


# ==========================================================
# Health Endpoint Response
# ==========================================================

class HealthResponse(APIResponse):
    """
    Response model for the health endpoint.
    """

    status: str = Field(
        ...,
        description="Current health status of the API."
    )

# ==========================================================
# Pipeline Endpoint Response
# ==========================================================

class PipelineResponse(APIResponse):
    """
    Response model for pipeline execution.
    """

    output_path: str | None = Field(
        default=None,
        description="Location of the generated report."
    )

    execution_time: float = Field(
        ...,
        description="Total pipeline execution time in seconds."
    )

    error: str | None = Field(
        default=None,
        description="Error message if pipeline execution failed."
    )

# ==========================================================
# Version Endpoint Response
# ==========================================================

class VersionResponse(APIResponse):
    """
    Response model for the version endpoint.
    """

    version: str = Field(
        ...,
        description="Current API version."
    )