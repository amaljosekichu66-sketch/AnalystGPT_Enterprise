"""
Response models for AnalystGPT Enterprise REST API.

Responsibilities
----------------
- Define standardized API response schemas.
- Provide strongly typed responses for FastAPI endpoints.
- Improve OpenAPI documentation and response validation.

This module intentionally contains no business logic.
"""

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ==========================================================
# Base Response Model
# ==========================================================

class APIResponse(BaseModel):
    """
    Standard API response envelope.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    success: bool = Field(
        default=True,
        description=(
            "Indicates whether the request "
            "completed successfully."
        ),
    )

    message: str = Field(
        default="Request completed successfully.",
        description="Human-readable response message.",
    )

    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Endpoint-specific response payload.",
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
        description="Application name.",
    )

    version: str = Field(
        ...,
        description="Current application version.",
    )

    status: str = Field(
        ...,
        description="Current application status.",
    )

    documentation: str = Field(
        ...,
        description="URL to API documentation.",
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
        description="Current API health status.",
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
        description="Current application version.",
    )


# ==========================================================
# AI Report Response
# ==========================================================

class AIReportResponse(BaseModel):
    """
    AI-generated business insights.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    executive_summary: str

    recommendations: list[str] = Field(
        default_factory=list,
    )

    explanations: list[str] = Field(
        default_factory=list,
    )

    narrative: str

    model: str

    provider: str

    execution_time: float


# ==========================================================
# Pipeline Response
# ==========================================================

class PipelineResponse(APIResponse):
    """
    Response returned after pipeline execution.
    """

    output_path: str | None = None

    execution_time: float = 0.0

    ai_report: AIReportResponse | None = None

    error: str | None = None