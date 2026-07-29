"""
Text Report Exporter Module

Exports a StructuredReport as a formatted UTF-8 text report.
"""

from __future__ import annotations

from pathlib import Path
from pprint import pformat

from src.core.config import (
    DEFAULT_REPORT_FILENAME,
    REPORT_OUTPUT_DIRECTORY,
)
from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


class TextReportExporter:
    """
    Exports a StructuredReport to plain-text format.
    """

    SEPARATOR = "=" * 80

    # ==========================================================
    # Public API
    # ==========================================================

    def export(
        self,
        report: StructuredReport,
        output_path: str | Path | None = None,
    ) -> str:
        """
        Export the structured report as a UTF-8 text file.
        """

        logger.info("Exporting structured report...")

        report_path = self._resolve_output_path(
            output_path,
        )

        report_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path.write_text(
            self._build_report(report),
            encoding="utf-8",
        )

        logger.info(
            "Text report exported successfully: %s",
            report_path.resolve(),
        )

        return str(report_path.resolve())

    # ==========================================================
    # Report Builder
    # ==========================================================

    def _build_report(
        self,
        report: StructuredReport,
    ) -> str:
        """
        Build a formatted text report.
        """

        lines: list[str] = [

            self.SEPARATOR,
            report.title,
            self.SEPARATOR,
            "",

            "Generated",
            "-" * 80,
            report.generated_at.isoformat(),
            "",

            "EXECUTIVE SUMMARY",
            "-" * 80,
        ]

        # ======================================================
        # Executive Summary
        # ======================================================

        summary = report.executive_summary

        if summary:

            if isinstance(summary, str):

                lines.append(summary)

            elif isinstance(summary, (list, tuple)):

                for item in summary:

                    lines.append(str(item))

            else:

                lines.append(str(summary))

        else:

            lines.append("No executive summary available.")

        # ======================================================
        # KPI Section
        # ======================================================

        lines.extend(

            [
                "",
                "KEY PERFORMANCE INDICATORS",
                "-" * 80,
            ]

        )

        if report.kpis:

            for key, value in report.kpis.items():

                lines.append(
                    f"{key}: {value}"
                )

        else:

            lines.append(
                "No KPIs available."
            )

        # ======================================================
        # Analytics
        # ======================================================

        lines.extend(

            [
                "",
                "ANALYTICS",
                "-" * 80,
            ]

        )

        if report.analytics:

            for section, values in report.analytics.items():

                lines.append("")
                lines.append(section.upper())
                lines.append("~" * len(section))

                if isinstance(values, dict):

                    lines.append(

                        pformat(
                            values,
                            sort_dicts=False,
                            width=100,
                        )

                    )

                elif isinstance(values, (list, tuple)):

                    for value in values:

                        lines.append(str(value))

                else:

                    lines.append(str(values))

        else:

            lines.append(
                "No analytics available."
            )

        # ======================================================
        # Recommendations
        # ======================================================

        lines.extend(

            [
                "",
                "RECOMMENDATIONS",
                "-" * 80,
            ]

        )

        if report.recommendations:

            for index, recommendation in enumerate(

                report.recommendations,
                start=1,

            ):

                lines.append(
                    f"{index}. {recommendation}"
                )

        else:

            lines.append(
                "No recommendations available."
            )

        # ======================================================
        # Metadata
        # ======================================================

        if report.metadata:

            lines.extend(

                [
                    "",
                    "REPORT METADATA",
                    "-" * 80,
                ]

            )

            for key, value in report.metadata.items():

                if isinstance(value, dict):

                    lines.append(
                        f"{key}:"
                    )

                    lines.append(

                        pformat(
                            value,
                            sort_dicts=False,
                            width=100,
                        )

                    )

                else:

                    lines.append(
                        f"{key}: {value}"
                    )

        # ======================================================
        # Footer
        # ======================================================

        lines.extend(

            [
                "",
                self.SEPARATOR,
                "End of Report",
                self.SEPARATOR,
            ]

        )

        return "\n".join(lines)

    # ==========================================================
    # Path Resolution
    # ==========================================================

    def _resolve_output_path(
        self,
        output_path: str | Path | None,
    ) -> Path:
        """
        Resolve export destination.
        """

        if output_path is None:

            return (
                REPORT_OUTPUT_DIRECTORY
                / DEFAULT_REPORT_FILENAME
            )

        report_path = Path(output_path)

        if report_path.exists() and report_path.is_dir():

            return (
                report_path
                / DEFAULT_REPORT_FILENAME
            )

        if report_path.suffix == "":

            report_path.mkdir(
                parents=True,
                exist_ok=True,
            )

            return (
                report_path
                / DEFAULT_REPORT_FILENAME
            )

        return report_path