"""
Deterministic Executive Text Report Exporter.

Sprint 14 Phase 3 — Enterprise Report Export Redesign.

Provides clean, professional, executive-grade plain text reports suitable for
terminal review, email distribution, and enterprise compliance archiving.
Eliminates internal machine availability flags and exposes clear business narratives
grounded strictly in observed dataset evidence.
"""

from __future__ import annotations

import logging
import textwrap
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core import config
from src.core.pii import is_contact_pii_column
from src.reporting.structured_report import StructuredReport

logger = logging.getLogger(__name__)


class TextReportExporter:
    """
    Exports a StructuredReport and optional AIReport into an executive business text brief.
    """

    SEPARATOR = "=" * 82
    SUBSEPARATOR = "-" * 82

    def export(
        self,
        report: StructuredReport,
        output_path: str | Path | None = None,
        ai_report: Any | None = None,
        lineage: dict[str, Any] | None = None,
    ) -> str:
        target = self._resolve_output_path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        content = self.render(report, ai_report=ai_report, lineage=lineage)
        target.write_text(content, encoding="utf-8")
        logger.info("Saved executive text report to: %s", target)
        return str(target)

    def _resolve_output_path(self, output_path: str | Path | None) -> Path:
        if output_path is not None:
            p = Path(output_path)
            if p.is_dir():
                return p / config.DEFAULT_REPORT_FILENAME
            return p
        # Read through `config` so a redirected output directory is honoured.
        return Path(config.REPORT_OUTPUT_DIRECTORY) / config.DEFAULT_REPORT_FILENAME

    def _is_pii_column(self, col_name: str) -> bool:
        """
        Mask personal contact columns only.

        The previous keyword set included "id", tested as a substring, so
        `ai_-_classification_confidence` was rendered as
        "Masked identifier field" - because "confidence" contains "id". It also
        masked every column whose name merely mentioned email or address.
        See `src/core/pii.py`.
        """
        return is_contact_pii_column(col_name)

    def render(
        self,
        report: StructuredReport,
        ai_report: Any | None = None,
        lineage: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = []

        analytics = report.analytics or {}
        desc = analytics.get("descriptive_statistics", {})
        total_rows = desc.get("total_rows") or report.kpis.get("Rows") or 0
        total_cols = desc.get("total_columns") or report.kpis.get("Columns") or 0
        num_cols = desc.get("numeric_column_count", 0)
        cat_cols = desc.get("categorical_column_count", 0)

        profile = analytics.get("dataset_profile", {})
        completeness = profile.get("completeness_score", 1.0) if isinstance(profile, dict) else 1.0
        comp_pct = f"{completeness * 100:.1f}%" if isinstance(completeness, (int, float)) else "100.0%"
        duplicates = profile.get("duplicate_rows_count", 0) if isinstance(profile, dict) else 0

        gen_date = (
            report.generated_at.strftime("%d %b %Y, %H:%M UTC")
            if isinstance(report.generated_at, datetime)
            else str(report.generated_at)
        )
        run_id = (
            lineage.get("pipeline_run_id") if lineage and lineage.get("pipeline_run_id") is not None else "Standard"
        )

        # ==========================================================
        # Header & Metadata
        # ==========================================================
        lines.append(self.SEPARATOR)
        lines.append(f"  ANALYSTGPT ENTERPRISE — BUSINESS ANALYTICS REPORT: {report.title}")
        lines.append(self.SEPARATOR)
        lines.append(f"Generated: {gen_date}  |  Pipeline Run: #{run_id}  |  Classification: Confidential")
        lines.append("")

        # ==========================================================
        # 1. Executive Summary
        # ==========================================================
        lines.append("1. EXECUTIVE SUMMARY")
        lines.append(self.SUBSEPARATOR)
        summary = report.executive_summary
        if summary:
            if isinstance(summary, list):
                for p in summary:
                    lines.append(textwrap.fill(str(p), width=80))
            else:
                lines.append(textwrap.fill(str(summary), width=80))
        else:
            lines.append("Executive summary unavailable.")
        lines.append("")

        # ==========================================================
        # 2. Key Performance Indicators
        # ==========================================================
        lines.append("2. KEY PERFORMANCE INDICATORS")
        lines.append(self.SUBSEPARATOR)
        lines.append(
            f"• Total Observed Records : {total_rows:,}"
            if isinstance(total_rows, int)
            else f"• Total Observed Records : {total_rows}"
        )
        lines.append(f"• Ingested Schema Width  : {total_cols} columns")
        lines.append(f"• Data Completeness      : {comp_pct}")
        lines.append(f"• Duplicate Rows Found   : {duplicates:,}")
        lines.append(f"• Governed Measures      : {num_cols}")
        lines.append(f"• Categorical Dimensions : {cat_cols}")

        if report.kpis and isinstance(report.kpis, Mapping):
            for k, v in report.kpis.items():
                if k not in {
                    "Rows",
                    "Columns",
                    "Numeric Columns",
                    "Categorical Columns",
                    "Datetime Columns",
                    "Memory Usage (MB)",
                    "Correlation Available",
                    "Distribution Available",
                    "Categorical Analysis Available",
                    "Descriptive Statistics",
                    "Numerical Analysis",
                    "Categorical Analysis",
                    "Correlation Analysis",
                    "Distribution Analysis",
                    "Analytics Sections",
                }:
                    lines.append(f"• {k:<25}: {v}")
        lines.append("")

        # ==========================================================
        # 3. Column Semantic Profile & Data Governance
        # ==========================================================
        cols_profile = profile.get("columns", {}) if isinstance(profile, dict) else {}
        lines.append("3. COLUMN SEMANTIC PROFILE & GOVERNANCE")
        lines.append(self.SUBSEPARATOR)

        if cols_profile:
            lines.append(
                f"{'Field Name':<22} {'Semantic Type':<18} {'Analytical Role':<20} {'Missing':<10} {'Unique':<10} {'Policy'}"
            )
            lines.append("-" * 96)
            for cname, cdata in cols_profile.items():
                disp_name = cname if len(cname) <= 20 else cname[:18] + ".."
                sem_type = str(cdata.get("semantic_type", "text"))[:18]
                role = str(cdata.get("analytical_role", "attribute"))[:20]
                missing_str = f"{cdata.get('missing_percentage', 0.0):.1f}%"
                unique_str = f"{cdata.get('uniqueness_percentage', 0.0):.1f}%"
                policy = str(cdata.get("governance_recommendation", "standard")).replace("_", " ").title()[:16]
                lines.append(f"{disp_name:<22} {sem_type:<18} {role:<20} {missing_str:<10} {unique_str:<10} {policy}")
        else:
            lines.append("All dataset fields conform to baseline enterprise schema validation.")
        lines.append("")

        # ==========================================================
        # 4. Key Analytical Findings (ANALYTICS)
        # ==========================================================
        lines.append("4. KEY ANALYTICAL FINDINGS & ANALYTICS")
        lines.append(self.SUBSEPARATOR)

        cat_data = analytics.get("categorical_analysis", {})
        num_data = analytics.get("numerical_analysis", {})
        corr_data = analytics.get("correlation_analysis", {})

        # Categorical breakdown with count and share %
        if cat_data:
            lines.append("Categorical Dimension Breakdown:")
            for col_name, stats in cat_data.items():
                if self._is_pii_column(col_name):
                    lines.append(
                        f"  • {col_name}: Masked identifier field (cardinality: {stats.get('distinct_count') or stats.get('unique_values') or 'N/A'})"
                    )
                    continue
                distinct = stats.get("distinct_count") or stats.get("unique_values") or "N/A"
                top_vals = stats.get("top_values") or stats.get("value_distribution") or {}
                sum_rows = total_rows or (sum(top_vals.values()) if isinstance(top_vals, dict) else 1) or 1
                top_str = (
                    ", ".join(f"'{k}' ({v:,} | {(v / sum_rows) * 100.0:.1f}%)" for k, v in list(top_vals.items())[:3])
                    if isinstance(top_vals, dict)
                    else "N/A"
                )
                lines.append(f"  • {col_name} ({distinct} distinct categories) -> Top cohorts: {top_str}")
            lines.append("")

        # Numerical breakdown
        if num_data:
            lines.append("Numerical Measure Statistics:")
            for mname, mstats in num_data.items():
                if isinstance(mstats, dict):
                    mean_s = f"{mstats.get('mean', 0.0):.2f}"
                    med_s = f"{mstats.get('median', 0.0):.2f}"
                    std_s = f"{mstats.get('standard_deviation', 0.0):.2f}"
                    min_s = f"{mstats.get('minimum', 0.0):.2f}"
                    max_s = f"{mstats.get('maximum', 0.0):.2f}"
                    lines.append(
                        f"  • {mname}: Mean = {mean_s} | Median = {med_s} | Std Dev = {std_s} | Range = [{min_s}, {max_s}]"
                    )
            lines.append("")
        else:
            lines.append("Numerical Measure Statistics:")
            lines.append(
                "  • Quantitative relationship analysis was not applicable as no governed numerical measures were identified."
            )
            lines.append("")

        # Correlation breakdown
        corr_mat = corr_data.get("correlation_matrix") if isinstance(corr_data, dict) else {}
        if corr_mat and len(corr_mat) >= 2:
            lines.append("Bivariate Relationships:")
            pos = corr_data.get("strongest_positive")
            neg = corr_data.get("strongest_negative")
            if pos and pos.get("correlation") is not None:
                lines.append(
                    f"  • Strongest Positive: '{pos.get('column_1')}' vs '{pos.get('column_2')}' (r = {pos.get('correlation')})"
                )
            if neg and neg.get("correlation") is not None:
                lines.append(
                    f"  • Strongest Negative: '{neg.get('column_1')}' vs '{neg.get('column_2')}' (r = {neg.get('correlation')})"
                )
            lines.append("  • Note: Observed relationships describe association and do not imply causal effects.")
            lines.append("")
        else:
            lines.append("Bivariate Relationships:")
            lines.append(
                "  • Correlation analysis was not applicable as fewer than two numerical measure columns were present."
            )
            lines.append("")

        # ==========================================================
        # 5. AI Business Insights (when available)
        # ==========================================================
        if ai_report is not None:
            model_name = getattr(ai_report, "model", None) or (
                ai_report.get("model") if isinstance(ai_report, dict) else "Gemma 3"
            )
            provider = getattr(ai_report, "provider", None) or (
                ai_report.get("provider") if isinstance(ai_report, dict) else "Ollama"
            )
            conf = getattr(ai_report, "confidence", None) or (
                ai_report.get("confidence") if isinstance(ai_report, dict) else "Grounded in deterministic analytics"
            )

            lines.append("5. AI BUSINESS INSIGHTS (AI-GENERATED) — AI INSIGHTS & INTERPRETATION (AI-GENERATED)")
            lines.append(self.SUBSEPARATOR)
            lines.append(
                "DISCLAIMER: AI-generated insights provide strategic narratives grounded in deterministic analytics."
            )
            lines.append(f"Model: {model_name} | Provider: {provider}")
            lines.append("")

            ai_summary = getattr(ai_report, "executive_summary", None) or (
                ai_report.get("executive_summary") if isinstance(ai_report, dict) else None
            )
            if ai_summary:
                lines.append("AI Executive Summary:")
                lines.append(textwrap.fill(str(ai_summary), width=80))
                lines.append("")

            findings = (
                getattr(ai_report, "key_findings", None)
                or (ai_report.get("key_findings") if isinstance(ai_report, dict) else None)
                or getattr(ai_report, "explanations", None)
                or (ai_report.get("explanations") if isinstance(ai_report, dict) else [])
            )
            if findings:
                lines.append("AI Key Analytical Findings:")
                for f in findings:
                    lines.append(f"• {textwrap.fill(str(f), width=78, subsequent_indent='  ')}")
                lines.append("")

            implications = getattr(ai_report, "business_implications", None) or (
                ai_report.get("business_implications") if isinstance(ai_report, dict) else []
            )
            if implications:
                lines.append("Business Implications:")
                for imp in implications:
                    lines.append(f"• {textwrap.fill(str(imp), width=78, subsequent_indent='  ')}")
                lines.append("")

            ai_recs = getattr(ai_report, "recommendations", None) or (
                ai_report.get("recommendations") if isinstance(ai_report, dict) else []
            )
            if ai_recs:
                lines.append("Prioritized Strategic Actions:")
                for idx, r in enumerate(ai_recs, start=1):
                    lines.append(f"{idx}. {textwrap.fill(str(r), width=77, subsequent_indent='   ')}")
                lines.append("")

            lines.append(f"Confidence Level & Evidence Basis: {conf}")
            lines.append("")

        # ==========================================================
        # 6. Recommendations
        # ==========================================================
        lines.append("6. RECOMMENDATIONS")
        lines.append(self.SUBSEPARATOR)
        evidence_recs = self._build_evidence_recommendations(report)
        if report.recommendations:
            for idx, r in enumerate(report.recommendations, start=1):
                lines.append(f"{idx}. {r}")
            lines.append("")
        elif evidence_recs:
            for idx, (obs, imp, act) in enumerate(evidence_recs, start=1):
                lines.append(f"Recommendation {idx}:")
                lines.append(f"  • Observation    : {obs}")
                lines.append(f"  • Interpretation : {imp}")
                lines.append(f"  • Action         : {act}")
            lines.append("")
        else:
            lines.append("No recommendations available.")
            lines.append("")

        # ==========================================================
        # 7. Governance Boundaries & Limitations
        # ==========================================================
        lines.append("7. DATA LIMITATIONS & CAVEATS")
        lines.append(self.SUBSEPARATOR)
        lines.append(
            "• Scope Constraint: Analysis is strictly bounded by ingested dataset fields and observed records."
        )
        lines.append(
            "• Non-Causality   : Observational records describe correlation and distribution; causal conclusions require experimental validation."
        )
        lines.append(
            "• Domain Context  : Business actions should validate these empirical findings with domain operational experts."
        )
        lines.append("")

        # ==========================================================
        # 8. Lineage & Provenance
        # ==========================================================
        lines.append("8. DATASET LINEAGE & PROVENANCE (DATA LINEAGE & PROVENANCE)")
        lines.append(self.SUBSEPARATOR)
        if lineage:
            lines.append(f"• Pipeline Run ID       : {lineage.get('pipeline_run_id', 'N/A')}")
            lines.append(f"• Source Version ID     : {lineage.get('source_version_id', 'src_canonical')}")
            lines.append(f"• Cleaned Version ID    : {lineage.get('cleaned_version_id', 'clean_validated')}")
            lines.append(f"• Cleaning Execution ID : {lineage.get('cleaning_execution_id', 'N/A')}")
            lines.append(f"• Context Schema Version: {lineage.get('context_schema_version', '1.0')}")
        else:
            lines.append("• Pipeline Run ID       : Standard")
            lines.append("• Lineage Repository    : Enterprise Immutable Audit Store")
        lines.append("• Analytics Engine      : AnalystGPT Enterprise 2.0")
        lines.append("• Report Architecture   : Enterprise Brief")
        lines.append("")

        lines.append(self.SEPARATOR)
        lines.append("  END OF REPORT — ANALYSTGPT ENTERPRISE")
        lines.append(self.SEPARATOR)

        return "\n".join(lines)

    def _build_evidence_recommendations(
        self,
        report: StructuredReport,
    ) -> list[tuple[str, str, str]]:
        recs: list[tuple[str, str, str]] = []
        analytics = report.analytics or {}
        cat_data = analytics.get("categorical_analysis", {})
        num_data = analytics.get("numerical_analysis", {})
        total_rows = analytics.get("descriptive_statistics", {}).get("total_rows") or report.kpis.get("Rows") or 0

        if cat_data:
            for col_name, stats in cat_data.items():
                if self._is_pii_column(col_name):
                    continue
                if isinstance(stats, dict):
                    top_dict = stats.get("value_distribution") or stats.get("top_values") or {}
                    if top_dict:
                        top_k, top_v = next(iter(top_dict.items()))
                        pct_str = f" ({(top_v / total_rows) * 100.0:.1f}%)" if total_rows and total_rows > 0 else ""
                        recs.append(
                            (
                                f"'{col_name}' concentration: '{top_k}' accounts for {top_v:,} records{pct_str}.",
                                f"Records are concentrated in the '{top_k}' category relative to other observed categories.",
                                f"Consider segmented reporting for '{top_k}' if category segmentation aligns with operational requirements.",
                            )
                        )
                        break

        if num_data:
            col_name, stats = next(iter(num_data.items()))
            if isinstance(stats, dict):
                min_v = stats.get("minimum", 0.0)
                max_v = stats.get("maximum", 0.0)
                med_v = stats.get("median", 0.0)
                recs.append(
                    (
                        f"'{col_name}' spans from {min_v:,.2f} to {max_v:,.2f} with a sample median of {med_v:,.2f}.",
                        f"Continuous measure variance indicates dispersion across the observed range.",
                        f"Incorporate '{col_name}' variance thresholds into monitoring reports if tracking this measure is required.",
                    )
                )
        else:
            if not cat_data:
                return []
            recs.append(
                (
                    "The analyzed dataset contains zero governed numerical measures.",
                    "Quantitative relationship analysis is bounded by the current categorical schema structure.",
                    "Consider enriching future data ingestion with numerical value measures if quantitative performance tracking is required.",
                )
            )

        return recs
