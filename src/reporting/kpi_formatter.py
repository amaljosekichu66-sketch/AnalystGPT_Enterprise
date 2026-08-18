"""
KPI Formatter Module.

Extracts business KPIs from the analytics report with semantic and numerical integrity.

Sprint 14 Remediation — AI Insights + Enterprise Reporting Reliability Remediation.
"""

from __future__ import annotations

from typing import Any

from src.core.logger import logger


class KPIFormatter:
    """
    Formats business KPIs for reporting.
    """

    def format_kpis(
        self,
        analytics_report: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract reporting KPIs.
        """
        logger.info("Formatting KPI section.")

        descriptive = analytics_report.get("descriptive_statistics", {})
        numeric_count = descriptive.get("numeric_column_count")

        has_descriptive = "descriptive_statistics" in analytics_report

        # Check for actual numerical findings vs empty section
        if numeric_count == 0:
            has_numerical = False
            has_correlation = False
        else:
            num_data = analytics_report.get("numerical_analysis")
            has_numerical = bool(num_data) or ("numerical_analysis" in analytics_report and numeric_count is None)

            corr_data = analytics_report.get("correlation_analysis", {})
            corr_mat = corr_data.get("correlation_matrix") if isinstance(corr_data, dict) else None
            has_correlation = bool(corr_mat) or ("correlation_analysis" in analytics_report and numeric_count is None)

        has_categorical = "categorical_analysis" in analytics_report and (
            bool(analytics_report.get("categorical_analysis")) or descriptive.get("categorical_column_count") is None
        )
        has_distribution = "distribution_analysis" in analytics_report and (
            bool(analytics_report.get("distribution_analysis")) or numeric_count is None
        )

        kpis = {
            # ==================================================
            # Enterprise KPIs
            # ==================================================
            "Analytics Sections": len(analytics_report),
            "Rows": descriptive.get("total_rows"),
            "Columns": descriptive.get("total_columns"),
            "Numeric Columns": descriptive.get("numeric_column_count"),
            "Categorical Columns": descriptive.get("categorical_column_count"),
            "Datetime Columns": descriptive.get("datetime_column_count"),
            "Memory Usage (MB)": descriptive.get("memory_usage_mb"),
            "Correlation Available": has_correlation,
            "Distribution Available": has_distribution,
            "Categorical Analysis Available": has_categorical,
            # ==================================================
            # Legacy KPI Keys (backwards compatible)
            # ==================================================
            "Descriptive Statistics": "Available" if has_descriptive else "Unavailable",
            "Numerical Analysis": "Available" if has_numerical else "Unavailable",
            "Categorical Analysis": "Available" if has_categorical else "Unavailable",
            "Correlation Analysis": "Available" if has_correlation else "Unavailable",
            "Distribution Analysis": "Available" if has_distribution else "Unavailable",
        }

        logger.info("KPI section formatted.")
        return kpis
