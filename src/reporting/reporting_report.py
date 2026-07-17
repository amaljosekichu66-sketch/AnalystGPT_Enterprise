"""
Reporting Report Module

Defines the standardized output contract returned by the
Reporting Module.
"""

from typing import Any

from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


class ReportingReport:
    """
    Represents the final output produced by the Reporting Module.

    This object contains the generated report together with
    reporting metadata.
    """

    def __init__(
        self,
        report: StructuredReport,
        export_path: str,
        execution_time: float,
    ) -> None:
        """
        Initialize a ReportingReport instance.

        Args:
            report:
                Structured business report.

            export_path:
                Location of the exported report.

            execution_time:
                Total reporting pipeline execution time.
        """

        logger.info("Creating ReportingReport.")

        self.report = report
        self.export_path = export_path
        self.execution_time = execution_time

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the reporting result into a serializable dictionary.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the reporting result.
        """

        return {
            "report": self.report.to_dict(),
            "export_path": self.export_path,
            "execution_time": round(
                self.execution_time,
                4,
            ),
        }