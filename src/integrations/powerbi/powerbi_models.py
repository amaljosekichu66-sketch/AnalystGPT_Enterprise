"""
Power BI response models.
"""

from typing import Any

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    success: bool
    execution_time: float | None
    report: dict[str, Any]
    output_path: str | None


class PipelineSummary(BaseModel):
    success: bool
    execution_time: float | None
    output_path: str | None


class ReportResponse(BaseModel):
    report: dict[str, Any]