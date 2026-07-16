"""
Text Report Exporter Module

Exports a StructuredReport as a plain text file.
"""

from pathlib import Path

from src.core.config import (
    REPORT_OUTPUT_DIRECTORY,
    DEFAULT_REPORT_FILENAME,
)
from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


class TextReportExporter:
    """
    Exports a StructuredReport to text format.
    """

    def export(
        self,
        report: StructuredReport,
        output_path: str | Path | None = None,
    ) -> str:
        """
        Export the structured report as a text file.

        If output_path is:

            None
                -> saves to the default reports directory using the
                   default filename.

            A directory
                -> saves into that directory using the default filename.

            A file path
                -> saves exactly to that file.

        Args:
            report:
                Structured report to export.

            output_path:
                Optional output file or directory.

        Returns:
            Absolute path to the exported report.
        """

        logger.info("Exporting text report.")

        lines = [
            "=" * 60,
            report.title,
            "=" * 60,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 60,
        ]

        lines.extend(report.executive_summary)

        lines.extend(
            [
                "",
                "KEY PERFORMANCE INDICATORS",
                "-" * 60,
            ]
        )

        for key, value in report.kpis.items():
            lines.append(f"{key}: {value}")

        lines.extend(
            [
                "",
                "ANALYTICS RESULTS",
                "-" * 60,
            ]
        )

        for key, value in report.analytics.items():
            lines.append(f"{key}: {value}")

        lines.extend(
            [
                "",
                "RECOMMENDATIONS",
                "-" * 60,
            ]
        )

        if report.recommendations:
            lines.extend(report.recommendations)
        else:
            lines.append("No recommendations available.")

        report_content = "\n".join(lines)

        # ---------------------------------------------------------
        # Determine destination
        # ---------------------------------------------------------

        if output_path is None:

            report_path = (
                REPORT_OUTPUT_DIRECTORY
                / DEFAULT_REPORT_FILENAME
            )

        else:

            report_path = Path(output_path)

            # If caller passed a directory
            if report_path.exists() and report_path.is_dir():

                report_path = (
                    report_path
                    / DEFAULT_REPORT_FILENAME
                )

            # If caller passed something without a suffix,
            # treat it as a directory.
            elif report_path.suffix == "":

                report_path.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                report_path = (
                    report_path
                    / DEFAULT_REPORT_FILENAME
                )

        # ---------------------------------------------------------
        # Ensure parent folder exists
        # ---------------------------------------------------------

        report_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path.write_text(
            report_content,
            encoding="utf-8",
        )

        logger.info(
            "Text report exported successfully: %s",
            report_path.resolve(),
        )

        return str(report_path.resolve())