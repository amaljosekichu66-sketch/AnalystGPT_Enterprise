"""
Pipeline report.

Represents the complete business output produced by the
AnalystGPT Enterprise pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.ai.ai_report import AIReport
from src.reporting.reporting_report import ReportingReport


@dataclass(
    frozen=True,
    slots=True,
)
class PipelineReport:
    """
    Immutable pipeline report.

    Canonical business output shared across the
    Application Layer, REST API, Power BI,
    Streamlit and future React frontend.
    """

    # ==========================================================
    # Reports
    # ==========================================================

    reporting_report: ReportingReport

    ai_report: AIReport | None = None

    # ==========================================================
    # Metadata
    # ==========================================================

    generated_at: datetime = datetime.now(
        UTC,
    )

    # ==========================================================
    # Serialization
    # ==========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "generated_at": (self.generated_at.isoformat()),
            "reporting_report": (self.reporting_report.to_dict()),
            "ai_report": (self.ai_report.to_dict() if self.ai_report else None),
        }
