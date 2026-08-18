"""
Pipeline execution result.

Returned after the complete AnalystGPT Enterprise
pipeline has finished.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import Any

from .pipeline_report import PipelineReport


@dataclass(
    frozen=True,
    slots=True,
)
class PipelineResult:
    """
    Immutable result returned by the Application layer.

    Represents the complete outcome of a pipeline
    execution.
    """

    # ==========================================================
    # Status
    # ==========================================================

    success: bool

    # ==========================================================
    # Business Output
    # ==========================================================

    pipeline_report: PipelineReport | None = None

    # ==========================================================
    # Execution Metadata
    # ==========================================================

    output_path: str | None = None

    execution_time: float | None = None

    generated_at: datetime = datetime.now(
        UTC,
    )

    ai_job_id: str | None = None
    ai_job_status: str | None = None

    # ==========================================================
    # Error
    # ==========================================================

    error: Exception | None = None

    # ==========================================================
    # Convenience Properties
    # ==========================================================

    @property
    def has_ai_report(
        self,
    ) -> bool:

        return (
            self.pipeline_report is not None
            and self.pipeline_report.ai_report
            is not None
        )

    @property
    def has_reporting_report(
        self,
    ) -> bool:

        return self.pipeline_report is not None

    # ==========================================================
    # Serialization
    # ==========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "success": self.success,
            "output_path": self.output_path,
            "execution_time": self.execution_time,
            "ai_job_id": self.ai_job_id,
            "ai_job_status": self.ai_job_status,
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "pipeline_report": (
                self.pipeline_report.to_dict()
                if self.pipeline_report
                else None
            ),
            "error": (
                str(self.error)
                if self.error
                else None
            ),
        }