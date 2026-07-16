"""
Report Builder Module

Builds the structured business report used by the Reporting Module.
"""

from typing import Any

from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


class ReportBuilder:
    """
    Builds the structured report from the reporting components.
    """

    def build_report(
        self,
        title: str,
        executive_summary: list[str],
        kpis: dict[str, Any],
        analytics: dict[str, Any],
        recommendations: list[str],
    ) -> StructuredReport:
        """
        Build the structured report.

        Args:
            title: Human-readable report title.
            executive_summary: Executive-level business summary.
            kpis: Key performance indicators.
            analytics: Complete analytics results.
            recommendations: Business recommendations.

        Returns:
            StructuredReport instance.
        """

        logger.info("Building structured report.")

        report = StructuredReport(
            title=title,
            executive_summary=executive_summary,
            kpis=kpis,
            analytics=analytics,
            recommendations=recommendations,
        )

        logger.info("Structured report built successfully.")

        return report