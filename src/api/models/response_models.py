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

    data: Any = Field(
        default_factory=dict,
        description="Endpoint-specific response payload.",
    )


# ==========================================================
# Standard Error Model
# ==========================================================

class ErrorResponse(BaseModel):
    """
    Standard API error response schema.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    detail: str = Field(
        ...,
        description="Human-readable explanation of the error.",
    )

    error_code: str | None = Field(
        default=None,
        description="Machine-readable error classification code.",
    )

    timestamp: str | None = Field(
        default=None,
        description="ISO timestamp when the error occurred.",
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

    key_findings: list[str] = Field(
        default_factory=list,
    )

    business_implications: list[str] = Field(
        default_factory=list,
    )

    risks: list[str] = Field(
        default_factory=list,
    )

    opportunities: list[str] = Field(
        default_factory=list,
    )

    actions: list[str] = Field(
        default_factory=list,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )

    confidence: str = Field(
        default="High (Grounded in Deterministic Analytics)",
    )


# ==========================================================
# Pipeline Response
# ==========================================================

class PipelineResponse(APIResponse):
    """
    Response returned after pipeline execution.
    """

    output_path: str | None = None

    execution_time: float = 0.0

    ai_job_id: str | None = None

    ai_job_status: str | None = None

    ai_report: AIReportResponse | None = None

    error: str | None = None


# ==========================================================
# Report Metadata & Response
# ==========================================================

class ReportSectionItem(BaseModel):
    """
    Metadata for an individual report section.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    name: str = Field(
        ...,
        description="Report section name.",
    )

    status: str = Field(
        default="Available",
        description="Section availability status.",
    )


class ReportDataResponse(BaseModel):
    """
    Report payload returned by reporting endpoints.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    reports: list[ReportSectionItem] = Field(
        default_factory=list,
        description="List of available report sections.",
    )

    report: dict[str, Any] | None = Field(
        default=None,
        description="Structured analytics and KPI reporting payload.",
    )

    ai_report: dict[str, Any] | None = Field(
        default=None,
        description="AI-generated insights and narrative payload.",
    )

    execution_time: float | None = Field(
        default=None,
        description="Pipeline execution duration in seconds.",
    )

    output_path: str | None = Field(
        default=None,
        description="File path of the generated report artifact.",
    )


class ReportsListResponse(APIResponse):
    """
    Response envelope for the latest reports listing.
    """

    data: ReportDataResponse = Field(
        default_factory=ReportDataResponse,
        description="Reporting metadata and result payload.",
    )


# ==========================================================
# Dashboard Status Response
# ==========================================================

class DashboardStatusResponse(BaseModel):
    """
    Response model for dashboard status endpoint.
    """

    model_config = ConfigDict(
        frozen=True,
    )

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
        description="Current dashboard status.",
    )
