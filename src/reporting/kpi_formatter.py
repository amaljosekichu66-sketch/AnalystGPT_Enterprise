"""
KPI Formatter Module.

Extracts business KPIs from the analytics report.
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

        logger.info(
            "Formatting KPI section."
        )

        descriptive = analytics_report.get(
            "descriptive_statistics",
            {},
        )

        has_descriptive = (
            "descriptive_statistics"
            in analytics_report
        )

        has_numerical = (
            "numerical_analysis"
            in analytics_report
        )

        has_categorical = (
            "categorical_analysis"
            in analytics_report
        )

        has_correlation = (
            "correlation_analysis"
            in analytics_report
        )

        has_distribution = (
            "distribution_analysis"
            in analytics_report
        )

        kpis = {

            # ==================================================
            # Enterprise KPIs
            # ==================================================

            "Analytics Sections":
                len(analytics_report),

            "Rows":
                descriptive.get(
                    "total_rows"
                ),

            "Columns":
                descriptive.get(
                    "total_columns"
                ),

            "Numeric Columns":
                descriptive.get(
                    "numeric_column_count"
                ),

            "Categorical Columns":
                descriptive.get(
                    "categorical_column_count"
                ),

            "Datetime Columns":
                descriptive.get(
                    "datetime_column_count"
                ),

            "Memory Usage (MB)":
                descriptive.get(
                    "memory_usage_mb"
                ),

            "Correlation Available":
                has_correlation,

            "Distribution Available":
                has_distribution,

            "Categorical Analysis Available":
                has_categorical,

            # ==================================================
            # Legacy KPI Keys
            # (kept for backwards compatibility with tests)
            # ==================================================

            "Descriptive Statistics":
                (
                    "Available"
                    if has_descriptive
                    else "Unavailable"
                ),

            "Numerical Analysis":
                (
                    "Available"
                    if has_numerical
                    else "Unavailable"
                ),

            "Categorical Analysis":
                (
                    "Available"
                    if has_categorical
                    else "Unavailable"
                ),

            "Correlation Analysis":
                (
                    "Available"
                    if has_correlation
                    else "Unavailable"
                ),

            "Distribution Analysis":
                (
                    "Available"
                    if has_distribution
                    else "Unavailable"
                ),
        }

        logger.info(
            "KPI section formatted."
        )

        return kpis