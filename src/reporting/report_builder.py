"""
Report Builder Module

Builds the structured business report used by the Reporting Module.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


class ReportBuilder:
    """
    Builds the structured business report from the reporting
    pipeline components.

    Responsibilities
    ----------------
    - Assemble the final StructuredReport.
    - Normalise optional values.
    - Attach report metadata.
    """

    def build_report(
        self,
        title: str,
        executive_summary: str,
        kpis: dict[str, Any],
        analytics: dict[str, Any],
        recommendations: list[str],
    ) -> StructuredReport:
        """
        Build the enterprise structured report.

        Parameters
        ----------
        title:
            Human-readable report title.

        executive_summary:
            Executive-level business summary.

        kpis:
            Key performance indicators.

        analytics:
            Complete analytics results.

        recommendations:
            Business recommendations.

        Returns
        -------
        StructuredReport
        """

        logger.info("Building structured report...")

        report = StructuredReport(
            title=title,
            executive_summary=executive_summary,
            kpis=kpis or {},
            analytics=analytics or {},
            recommendations=recommendations or [],
            generated_at=datetime.now(
                UTC,
            ),
            metadata={
                "builder": "ReportBuilder",
                "version": "Sprint 11",
            },
        )

        logger.info("Structured report built successfully.")

        logger.info(
            "Analytics Sections : %d",
            len(report.analytics),
        )

        logger.info(
            "Recommendations    : %d",
            len(report.recommendations),
        )

        return report
