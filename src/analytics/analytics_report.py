"""
Analytics Report Module

Defines the standardized output contract returned by the
Analytics Module.
"""

from typing import Any

from src.core.logger import logger


class AnalyticsReport:
    """
    Represents the final output produced by the Analytics Module.
    """

    def __init__(
        self,
        report: dict[str, Any],
        execution_time: float,
    ) -> None:
        """
        Initialize an AnalyticsReport instance.

        Args:
            report:
                Consolidated analytics results.

            execution_time:
                Total analytics execution time.
        """

        logger.info("Creating AnalyticsReport.")

        self.report = report
        self.execution_time = execution_time

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the analytics report into a serializable dictionary.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the analytics report.
        """

        return {
            "report": self.report,
            "execution_time": round(
                self.execution_time,
                4,
            ),
        }