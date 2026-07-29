"""
Serialises ReportingReport objects into concise structured text
for Large Language Model prompts.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.reporting.reporting_report import ReportingReport


class ReportSerializer:
    """
    Convert ReportingReport into a structured prompt context.

    The serializer exposes the important analytical information
    while keeping prompts compact.
    """

    # Reduced from 2500 to avoid overwhelming the LLM
    MAX_SECTION_LENGTH = 600

    # Maximum recursion depth when formatting nested mappings
    _MAX_RECURSION_DEPTH = 2

    @classmethod
    def serialize(
        cls,
        reporting_report: ReportingReport | None,
    ) -> str:
        """
        Convert a ReportingReport into structured text.
        """

        if reporting_report is None:
            return "No reporting data available."

        lines: list[str] = [
            "ANALYSTGPT ENTERPRISE REPORT",
            "=" * 70,
            "",
        ]

        lines.extend(
            cls._pipeline_section(
                reporting_report,
            )
        )

        structured_report = reporting_report.report

        lines.extend(
            cls._simple_section(
                "EXECUTIVE SUMMARY",
                structured_report.executive_summary,
            )
        )

        lines.extend(
            cls._mapping_section(
                "KPIS",
                structured_report.kpis,
            )
        )

        lines.extend(
            cls._list_section(
                "RECOMMENDATIONS",
                structured_report.recommendations,
            )
        )

        analytics = structured_report.analytics

        if isinstance(
            analytics,
            Mapping,
        ):

            # Only include analytics sections that are essential.
            for title, key in (
                (
                    "DESCRIPTIVE STATISTICS",
                    "descriptive_statistics",
                ),
                (
                    "CORRELATION ANALYSIS",
                    "correlation_analysis",
                ),
                (
                    "DISTRIBUTION ANALYSIS",
                    "distribution_analysis",
                ),
                (
                    "CATEGORICAL ANALYSIS",
                    "categorical_analysis",
                ),
            ):
                lines.extend(
                    cls._mapping_section(
                        title,
                        analytics.get(key),
                    )
                )

        return "\n".join(lines).strip()

    # ==========================================================
    # Section builders
    # ==========================================================

    @classmethod
    def _pipeline_section(
        cls,
        report: ReportingReport,
    ) -> list[str]:
        lines = [
            "PIPELINE",
            "-" * 70,
            f"Execution Time : {report.execution_time:.4f} seconds",
            "Status         : Completed",
            "",
        ]
        return lines

    @classmethod
    def _simple_section(
        cls,
        title: str,
        value: object,
    ) -> list[str]:
        if not value:
            return []

        text = str(value)[: cls.MAX_SECTION_LENGTH]
        return [
            title,
            "-" * len(title),
            text,
            "",
        ]

    @classmethod
    def _list_section(
        cls,
        title: str,
        values: list[str] | None,
    ) -> list[str]:
        if not values:
            return []

        lines = [
            title,
            "-" * len(title),
        ]
        lines.extend(f"- {item}" for item in values)
        lines.append("")
        return lines

    @classmethod
    def _mapping_section(
        cls,
        title: str,
        value: Mapping | None,
    ) -> list[str]:
        """
        Produce a concise bulleted summary from a mapping (dict).
        The summary is truncated to MAX_SECTION_LENGTH.
        """
        if not value:
            return []

        # Generate a clean summary without Python dict syntax
        summary = cls._format_mapping_summary(value, depth=0)
        # Truncate to limit
        if len(summary) > cls.MAX_SECTION_LENGTH:
            summary = summary[: cls.MAX_SECTION_LENGTH] + "..."

        return [
            title,
            "-" * len(title),
            summary,
            "",
        ]

    # ==========================================================
    # Mapping summarisation helpers
    # ==========================================================

    @classmethod
    def _format_mapping_summary(
        cls,
        obj: Any,
        depth: int = 0,
        max_items: int = 8,
    ) -> str:
        """
        Recursively convert a dict/list into a bulleted text summary.
        Only includes primitive values and flattens nested structures
        up to a maximum depth of _MAX_RECURSION_DEPTH.
        """
        if obj is None:
            return "Not available."

        # If we've exceeded max depth, summarise as count/size
        if depth > cls._MAX_RECURSION_DEPTH:
            if isinstance(obj, dict):
                return f"<{len(obj)} entries>"
            elif isinstance(obj, list):
                return f"<{len(obj)} items>"
            else:
                return str(obj)

        if isinstance(obj, dict):
            items = list(obj.items())
            # Filter out large internal structures
            items = [
                (k, v) for k, v in items
                if k not in ("index", "columns", "dtype", "correlation_matrix")
            ]
            if len(items) > max_items:
                items = items[:max_items]
                truncated = True
            else:
                truncated = False

            lines = []
            for key, val in items:
                if isinstance(val, (dict, list)):
                    nested_summary = cls._format_mapping_summary(
                        val, depth=depth + 1, max_items=4
                    )
                    lines.append(f"- {key}: {nested_summary}")
                else:
                    lines.append(f"- {key}: {val}")
            if truncated:
                lines.append(f"- ... (and more)")
            return "\n".join(lines) if lines else "Empty."

        elif isinstance(obj, list):
            if not obj:
                return "Empty list."
            items = obj[:max_items]
            truncated = len(obj) > max_items
            lines = [
                f"- {cls._format_mapping_summary(item, depth=depth + 1, max_items=4)}"
                for item in items
            ]
            if truncated:
                lines.append(f"- ... (and {len(obj) - max_items} more)")
            return "\n".join(lines)

        else:
            # Primitive value
            return str(obj)