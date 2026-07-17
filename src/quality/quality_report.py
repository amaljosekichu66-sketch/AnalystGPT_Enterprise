"""
Quality Report Module

Defines the standardized output contract returned by the
Quality Module.
"""

from typing import Any

from src.core.logger import logger


class QualityReport:
    """
    Represents the final output produced by the Quality Module.

    This object stores the complete quality assessment together
    with execution metadata.
    """

    def __init__(
        self,
        report: dict[str, Any],
        execution_time: float,
    ) -> None:
        """
        Initialize a QualityReport instance.

        Args:
            report:
                Consolidated quality assessment.

            execution_time:
                Total quality assessment execution time.
        """

        logger.info("Creating QualityReport.")

        self.report = report
        self.execution_time = execution_time

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the quality report into a serializable dictionary.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the quality report.
        """

        return {
            "report": self.report,
            "execution_time": round(
                self.execution_time,
                4,
            ),
        }