"""
Executive Summary Module.

Generates a concise executive summary from the analytics report.

Sprint 14 Phase 3 — Enterprise Report Export Redesign.
"""

from __future__ import annotations

from typing import Any

from src.core.logger import logger


class ExecutiveSummary:
    """
    Generates an executive-level business summary.
    """

    def generate_summary(
        self,
        analytics_report: dict[str, Any],
    ) -> list[str]:
        """
        Generate an executive summary as a list of bullet points.
        """
        logger.info("Generating executive summary.")

        descriptive = analytics_report.get("descriptive_statistics", {})
        total_rows = descriptive.get("total_rows", "Unknown")
        total_columns = descriptive.get("total_columns", "Unknown")
        numeric_columns = descriptive.get("numeric_column_count", 0)
        categorical_columns = descriptive.get("categorical_column_count", 0)

        summary: list[str] = []

        if analytics_report:
            row_str = f"{total_rows:,}" if isinstance(total_rows, int) else str(total_rows)
            summary.append(
                f"The dataset of {row_str} records and {total_columns} columns was verified "
                f"and processed with full semantic classification."
            )
            summary.append(
                f"The dataset includes {numeric_columns} numeric and {categorical_columns} categorical columns."
            )
        else:
            summary.append("No analytics results were available to summarize.")

        # Completed sections narrative
        if "descriptive_statistics" in analytics_report:
            summary.append("Descriptive statistics were generated successfully.")

        if "numerical_analysis" in analytics_report:
            if numeric_columns == 0 and descriptive:
                summary.append(
                    "Numerical variables were reviewed: no governed numerical measure columns were identified for statistical calculations."
                )
            else:
                summary.append(
                    "Numerical variables were analysed."
                )

        if "categorical_analysis" in analytics_report:
            summary.append(
                "Categorical variables were analysed."
            )

        if "correlation_analysis" in analytics_report:
            if numeric_columns < 2 and descriptive:
                summary.append(
                    "Correlation analysis was evaluated: skipped as fewer than two numerical measure columns were present."
                )
            else:
                summary.append(
                    "Correlation analysis was completed."
                )

        if "distribution_analysis" in analytics_report:
            summary.append(
                "Distribution analysis was completed."
            )

        if len(summary) == 1 and not analytics_report:
            summary.append("Additional analytical sections were not available.")

        logger.info("Executive summary generated.")
        return summary
