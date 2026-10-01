"""
Reporting Report Module

Defines the standardized output contract returned by the
Reporting Module.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "tolist"):
        return value.tolist()
    return str(value)


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

    def to_payload(self) -> str:
        """
        JSON a later process can rebuild this report from (P2-01, P2-02).

        An AI job runs from its pipeline's ReportingReport. It used to exist
        only in memory, so a manual retry or a restart could never run the job
        again. numpy scalars become plain numbers; anything else that JSON
        cannot carry becomes its string form.
        """
        return json.dumps(self.to_dict(), default=_json_default)

    @classmethod
    def from_payload(cls, payload: str) -> ReportingReport:
        data = json.loads(payload)
        generated_at = data.get("generated_at")
        return cls(
            report=StructuredReport.from_dict(data["report"]),
            export_path=data.get("export_path", ""),
            execution_time=float(data.get("execution_time") or 0.0),
            generated_at=datetime.fromisoformat(generated_at) if generated_at else None,
        )

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
