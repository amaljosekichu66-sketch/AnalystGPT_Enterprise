"""
Power BI response models.
"""

from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

# ==========================================================
# AI Report
# ==========================================================


class AIReportModel(BaseModel):
    """
    AI Insight Engine output.
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
# Dashboard Response
# ==========================================================


class DashboardResponse(BaseModel):
    """
    Response returned by /powerbi/dashboard.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    success: bool

    execution_time: float | None = None

    report: dict[str, Any] = Field(
        default_factory=dict,
    )

    ai_report: AIReportModel | None = None

    output_path: str | None = None

    ai_job_id: str | None = None

    generated_at: datetime | None = None  # changed from str | None


# ==========================================================
# Pipeline Summary
# ==========================================================


class PipelineSummary(BaseModel):
    """
    Response returned by /powerbi/pipeline.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    success: bool

    execution_time: float | None = None

    output_path: str | None = None

    ai_job_id: str | None = None

    ai_generated: bool = False

    generated_at: datetime | None = None  # changed from str | None


# ==========================================================
# Report Response
# ==========================================================


class ReportResponse(BaseModel):
    """
    Response returned by /powerbi/report.
    """

    model_config = ConfigDict(
        frozen=True,
    )

    report: dict[str, Any] = Field(
        default_factory=dict,
    )

    ai_report: AIReportModel | None = None

    execution_time: float | None = None

    output_path: str | None = None

    generated_at: datetime | None = None  # changed from str | None
