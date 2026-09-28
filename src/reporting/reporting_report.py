"""
Reporting Report Module

Defines the standardized output contract returned by the
Reporting Module.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


class ReportingReport:
    """
    Represents the final output produced by the Reporting Module.

    This object contains the generated business report together
    with reporting metadata.
    """

    def __init__(
        self,
        report: StructuredReport,
        export_path: str,
        execution_time: float,
        generated_at: datetime | None = None,
    ) -> None:
        """
        Initialise a ReportingReport instance.

        Parameters
        ----------
        report:
            Structured business report.

        export_path:
            Location of the exported report.

        execution_time:
            Total reporting execution time.

        generated_at:
            UTC timestamp when the report was generated.
        """

        logger.info("Creating ReportingReport.")

        self.report = report

        self.export_path = export_path

        self.execution_time = execution_time

        self.generated_at = (
            generated_at
            if generated_at is not None
            else datetime.now(
                UTC,
            )
        )

    # ==========================================================
    # Serialization
    # ==========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the reporting result into a serialisable dictionary.
        """

        return {
            "report": self.report.to_dict(),
            "export_path": self.export_path,
            "execution_time": round(
                self.execution_time,
                4,
            ),
            "generated_at": (self.generated_at.isoformat()),
        }

    # ==========================================================
    # Representation
    # ==========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            "ReportingReport("
            f"export_path={self.export_path!r}, "
            f"execution_time={self.execution_time:.4f}, "
            f"generated_at={self.generated_at.isoformat()}"
            ")"
        )
