"""
Serialises ReportingReport objects into concise structured text
for Large Language Model prompts with PII masking and analytical integrity.

Sprint 14 Remediation — AI Insights + Enterprise Reporting Reliability Remediation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.reporting.reporting_report import ReportingReport


class ReportSerializer:
    """
    Convert ReportingReport into a structured prompt context.

    The serializer exposes the important analytical information
    while keeping prompts compact and masking raw PII.
    """

    MAX_SECTION_LENGTH = 600
    _MAX_RECURSION_DEPTH = 2

    # PII keywords to mask
    _PII_KEYWORDS = {"phone", "email", "ssn", "passport", "credit_card"}

    @classmethod
    def serialize(
        cls,
        reporting_report: ReportingReport | None,
        data_context: Any | None = None,
    ) -> str:
        """
        Convert a ReportingReport and optional AIDataContext into structured text.
        """
        if reporting_report is None and data_context is None:
            return "No reporting data available."

        lines: list[str] = [
            "ANALYSTGPT ENTERPRISE REPORT",
            "=" * 70,
            "",
        ]

        if data_context is not None:
            lines.extend(cls._data_context_sections(data_context))

        if reporting_report is not None:
            lines.extend(cls._pipeline_section(reporting_report))

            structured_report = reporting_report.report

            lines.extend(
                cls._simple_section(
                    "EXECUTIVE SUMMARY (DETERMINISTIC BASELINE)",
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

            if isinstance(analytics, Mapping):
                total_rows = structured_report.kpis.get("Rows") if structured_report.kpis else None
                if total_rows is None and isinstance(analytics.get("descriptive_statistics"), Mapping):
                    total_rows = analytics["descriptive_statistics"].get("total_rows")

                for title, key in (
                    ("DESCRIPTIVE STATISTICS", "descriptive_statistics"),
                    ("CORRELATION ANALYSIS", "correlation_analysis"),
                    ("DISTRIBUTION ANALYSIS", "distribution_analysis"),
                ):
                    if key in analytics and analytics.get(key) is not None:
                        lines.extend(cls._mapping_section(title, analytics.get(key)))

                if "categorical_analysis" in analytics and analytics.get("categorical_analysis") is not None:
                    lines.extend(
                        cls._categorical_section(
                            "CATEGORICAL ANALYSIS",
                            analytics.get("categorical_analysis"),
                            total_rows=total_rows if isinstance(total_rows, int) else None,
                        )
                    )

        return "\n".join(lines).strip()

    @classmethod
    def _data_context_sections(cls, context: Any) -> list[str]:
        """
        Format AIDataContext into distinct, delimited prompt sections.
        """
        lines: list[str] = []

        # SECTION 1: SOURCE DATA OBSERVATIONS
        if hasattr(context, "source"):
            s = context.source
            total_missing_str = str(s.total_missing) if s.total_missing is not None else "Not recorded"
            completeness_str = f"{s.completeness_percentage:.2f}%" if s.completeness_percentage is not None else "Not recorded"
            lines.extend([
                "=== SECTION 1: SOURCE DATA OBSERVATIONS (RAW DATASET) ===",
                f"Source Filename       : {s.source_filename}",
                f"Raw Ingested Rows     : {s.row_count}",
                f"Raw Columns           : {s.column_count}",
                f"Total Missing Cells   : {total_missing_str}",
                f"Initial Completeness  : {completeness_str}",
            ])
            if s.per_column_missing:
                missing_str = ", ".join(f"{k}: {v}" for k, v in s.per_column_missing.items() if v > 0)
                lines.append(f"Column Missingness    : {missing_str or 'None'}")
            lines.append("")

        # SECTION 2: DATA CLEANING & TRANSFORMATION RECORD
        if hasattr(context, "cleaning"):
            c = context.cleaning
            policy_str = str(c.missing_value_policy) if c.missing_value_policy is not None else "Not recorded"
            if c.rows_removed is not None and c.pct_rows_removed is not None:
                rows_removed_str = f"{c.rows_removed} ({c.pct_rows_removed:.2f}%)"
            elif c.rows_removed is not None:
                rows_removed_str = f"{c.rows_removed}"
            else:
                rows_removed_str = "Not recorded"

            values_imputed_str = str(c.values_imputed) if c.values_imputed is not None else "Not recorded"

            lines.extend([
                "=== SECTION 2: DATA CLEANING & TRANSFORMATION RECORD ===",
                f"Missing Value Policy  : {policy_str}",
                f"Rows Removed          : {rows_removed_str}",
                f"Columns Removed       : {', '.join(c.columns_removed) if c.columns_removed else 'None'}",
                f"Values Imputed        : {values_imputed_str}",
            ])
            if c.affected_columns:
                lines.append(f"Affected Columns      : {', '.join(c.affected_columns)}")
            lines.append("")

        # SECTION 3: POST-CLEANING ANALYTICAL DATA
        if hasattr(context, "analytics"):
            a = context.analytics
            cleaned_comp_str = f"{a.completeness_percentage:.2f}%" if a.completeness_percentage is not None else "Not recorded"
            lines.extend([
                "=== SECTION 3: POST-CLEANING ANALYTICAL FINDINGS ===",
                f"Cleaned Row Count     : {a.row_count}",
                f"Cleaned Column Count  : {a.column_count}",
                f"Cleaned Completeness  : {cleaned_comp_str}",
                "",
            ])

        # SECTION 4: LINEAGE & PROVENANCE
        if hasattr(context, "lineage"):
            lin = context.lineage
            lines.extend([
                "=== SECTION 4: DATASET LINEAGE & PROVENANCE ===",
                f"Pipeline Run ID       : {lin.pipeline_run_id}",
                f"Source Version ID     : {lin.source_version_id}",
                f"Cleaned Version ID    : {lin.cleaned_version_id}",
                f"Cleaning Execution ID : {lin.cleaning_execution_id}",
                f"Schema Version        : {lin.context_schema_version}",
                "",
            ])

        return lines

    @classmethod
    def _pipeline_section(
        cls,
        report: ReportingReport,
    ) -> list[str]:
        return [
            "PIPELINE",
            "-" * 70,
            f"Execution Time : {report.execution_time:.4f} seconds",
            "Status         : Completed",
            "",
        ]

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
        if not value:
            return []

        summary = cls._format_mapping_summary(value, depth=0)
        if len(summary) > cls.MAX_SECTION_LENGTH:
            summary = summary[: cls.MAX_SECTION_LENGTH] + "..."

        return [
            title,
            "-" * len(title),
            summary,
            "",
        ]

    @classmethod
    def _categorical_section(
        cls,
        title: str,
        value: Mapping | None,
        total_rows: int | None = None,
    ) -> list[str]:
        if not value:
            return []

        lines = [
            title,
            "-" * len(title),
        ]

        for col_name, stats in value.items():
            if cls._is_pii_field(col_name):
                lines.append(f"- {col_name}: <masked identifier column>")
                continue

            if isinstance(stats, Mapping):
                count = stats.get("count")
                unique_cnt = stats.get("unique_values") or stats.get("distinct_category_count")
                top_val = stats.get("top_value") or stats.get("top_category")
                top_freq = stats.get("top_frequency") or stats.get("top_value_count")
                dist = stats.get("value_distribution") or stats.get("top_values") or {}

                rows_base = count if isinstance(count, int) and count > 0 else (total_rows if total_rows and total_rows > 0 else None)

                # Check if this has standard categorical analysis fields
                if count is not None or unique_cnt is not None or (top_val is not None and top_freq is not None):
                    lines.append(f"- {col_name}:")
                    if unique_cnt is not None:
                        lines.append(f"  - distinct_category_count: {unique_cnt} (distinct categories / cardinality count, NOT percentage)")
                    if count is not None:
                        lines.append(f"  - row_count: {count}")
                    if top_val is not None:
                        lines.append("  - top_category:")
                        lines.append(f"    - value: \"{top_val}\"")
                        if top_freq is not None:
                            lines.append(f"    - count: {top_freq} records")
                            if rows_base:
                                pct = (top_freq / rows_base) * 100.0
                                lines.append(f"    - percentage: {pct:.1f}%")
                    if dist and isinstance(dist, Mapping):
                        lines.append("  - category_distribution (count | percentage):")
                        for idx, (cat_k, cat_v) in enumerate(dist.items()):
                            if idx >= 5:
                                lines.append(f"    - ... (and {len(dist) - 5} more categories)")
                                break
                            if rows_base and isinstance(cat_v, (int, float)):
                                cat_pct = (cat_v / rows_base) * 100.0
                                lines.append(f"    - \"{cat_k}\": {cat_v} records | {cat_pct:.1f}%")
                            else:
                                lines.append(f"    - \"{cat_k}\": {cat_v} records")
                else:
                    # Fallback for simple/custom stubs (e.g. {"top_category": "Electronics"})
                    summary = cls._format_mapping_summary(stats, depth=1, max_items=4)
                    lines.append(f"- {col_name}: {summary}")
            else:
                lines.append(f"- {col_name}: {stats}")

        lines.append("")
        return lines

    @classmethod
    def _is_pii_field(cls, key: str) -> bool:
        low = key.lower()
        return any(p in low for p in cls._PII_KEYWORDS)

    @classmethod
    def _format_mapping_summary(
        cls,
        obj: Any,
        depth: int = 0,
        max_items: int = 8,
    ) -> str:
        if obj is None:
            return "Not available."

        if depth > cls._MAX_RECURSION_DEPTH:
            if isinstance(obj, dict):
                return f"<{len(obj)} entries>"
            elif isinstance(obj, list):
                return f"<{len(obj)} items>"
            else:
                return str(obj)

        if isinstance(obj, dict):
            items = list(obj.items())
            items = [
                (k, v) for k, v in items
                if k not in ("index", "columns", "dtype")
            ]
            if len(items) > max_items:
                items = items[:max_items]
                truncated = True
            else:
                truncated = False

            lines = []
            for key, val in items:
                if cls._is_pii_field(key):
                    if isinstance(val, (dict, list)):
                        count = len(val)
                        lines.append(f"- {key}: <{count} masked identifier entries>")
                    else:
                        lines.append(f"- {key}: <masked identifier>")
                    continue

                if isinstance(val, (dict, list)):
                    nested_summary = cls._format_mapping_summary(
                        val, depth=depth + 1, max_items=4
                    )
                    lines.append(f"- {key}: {nested_summary}")
                else:
                    lines.append(f"- {key}: {val}")
            if truncated:
                lines.append("- ... (and more)")
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
            return str(obj)
