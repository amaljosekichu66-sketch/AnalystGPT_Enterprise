"""
Pipeline execution result.

Returned after the complete application
pipeline has finished.
"""

from dataclasses import dataclass

from src.reporting.reporting_report import ReportingReport


@dataclass(frozen=True)
class PipelineResult:
    """
    Immutable result returned by the AnalystGPT
    Enterprise application.

    Represents the final outcome of a complete
    pipeline execution.
    """

    success: bool

    reporting_report: ReportingReport | None = None

    output_path: str | None = None

    execution_time: float | None = None

    error: Exception | None = None