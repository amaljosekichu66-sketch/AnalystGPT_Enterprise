"""
Enterprise PDF Report Exporter Module.

Exports a StructuredReport and optional AIReport as a publication-grade,
executive-ready PDF business analytics brief.

Features:
- Professional corporate visual design system (A4 portrait, 150 DPI)
- Executive Cover & Brief with styled KPI cards
- Structured Column Governance & Data Quality Table
- Deterministic, evidence-based visual analytics (Empirical categorical bars with shares, Statistical measure cards, Missingness & Correlation checks)
- Never plots synthetic Gaussian curves as empirical distributions
- Dedicated AI Insights section with grounded evidence basis
- Evidence-linked recommendations (Observation -> Interpretation -> Conditional Action)
- Natural business language limitations and provenance metadata
- Multi-page pagination with running headers, footers, and page numbers

Sprint 14 Phase 3 — Enterprise Report Export Redesign.
"""

from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

from src.core import config
from src.core.logger import logger
from src.core.pii import is_contact_pii_column
from src.reporting.structured_report import StructuredReport

matplotlib.use("Agg")  # Non-interactive backend


class PdfReportExporter:
    """
    Exports a StructuredReport to a polished, publication-grade PDF document.
    """

    PAGE_WIDTH = 8.27  # A4 width in inches
    PAGE_HEIGHT = 11.69  # A4 height in inches
    DPI = 150

    # Color Palette
    COLOR_PRIMARY = "#0F172A"  # Deep Navy / Slate 900
    COLOR_SECONDARY = "#1E293B"  # Slate 800
    COLOR_ACCENT = "#2563EB"  # Royal Blue
    COLOR_ACCENT_LIGHT = "#EFF6FF"  # Blue 50
    COLOR_TEXT_MAIN = "#0F172A"  # Dark Slate
    COLOR_TEXT_MUTED = "#64748B"  # Slate 500
    COLOR_BG_CARD = "#F8FAFC"  # Slate 50
    COLOR_BORDER = "#E2E8F0"  # Slate 200
    COLOR_SUCCESS = "#059669"  # Emerald 600
    COLOR_WARNING = "#D97706"  # Amber 600
    COLOR_AI_PURPLE = "#7C3AED"  # Violet 600
    COLOR_AI_BG = "#F5F3FF"  # Violet 50

    def export(
        self,
        report: StructuredReport,
        output_path: str | Path | None = None,
        ai_report: Any | None = None,
        lineage: dict[str, Any] | None = None,
    ) -> str:
        """
        Export the structured report and optional AI insights as an executive PDF file.
        """
        logger.info("Exporting executive enterprise PDF report...")

        report_path = self._resolve_output_path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        pages = self._build_report_pages(report, ai_report=ai_report, lineage=lineage)

        with PdfPages(str(report_path.resolve())) as pdf:
            total_pages = len(pages)
            for page_idx, render_fn in enumerate(pages, start=1):
                fig = plt.figure(
                    figsize=(self.PAGE_WIDTH, self.PAGE_HEIGHT),
                    dpi=self.DPI,
                    facecolor="#FFFFFF",
                )
                self._draw_page_decorations(fig, page_idx, total_pages, report.title)
                render_fn(fig, page_idx, total_pages)
                pdf.savefig(fig, dpi=self.DPI)
                plt.close(fig)

        logger.info("Executive PDF report exported successfully: %s (%d pages)", report_path.resolve(), total_pages)
        return str(report_path.resolve())

    def _resolve_output_path(self, output_path: str | Path | None) -> Path:
        if output_path is not None:
            p = Path(output_path)
            if p.is_dir():
                return p / config.DEFAULT_PDF_REPORT_FILENAME
            return p
        # Read through `config` so a redirected output directory is honoured.
        return Path(config.REPORT_OUTPUT_DIRECTORY) / config.DEFAULT_PDF_REPORT_FILENAME

    # ==========================================================
    # Page Orchestration
    # ==========================================================

    def _build_report_pages(
        self,
        report: StructuredReport,
        ai_report: Any | None = None,
        lineage: dict[str, Any] | None = None,
    ) -> list[Any]:
        """
        Build the sequence of page rendering callables based on available data.
        """
        pages: list[Any] = []

        analytics = report.analytics or {}
        dataset_profile = analytics.get("dataset_profile", {})
        cols_profile = dataset_profile.get("columns", {}) if isinstance(dataset_profile, dict) else {}
        num_data = analytics.get("numerical_analysis", {})
        cat_data = analytics.get("categorical_analysis", {})
        corr_data = analytics.get("correlation_analysis", {})
        dist_data = analytics.get("distribution_analysis", {})

        # Page 1: Executive Cover & Brief
        pages.append(lambda fig, p_num, p_tot: self._render_page_executive_brief(fig, report, ai_report, lineage))

        # Page 2: Dataset Profile & Governance Table
        pages.append(lambda fig, p_num, p_tot: self._render_page_dataset_governance(fig, report, cols_profile, lineage))

        # If columns exceed standard table size, add continuation table pages
        if len(cols_profile) > 14:
            pages.append(
                lambda fig, p_num, p_tot: self._render_page_governance_continuation(
                    fig, report, cols_profile, start_idx=14
                )
            )

        # Page 3: Visual Analytics & Key Findings
        has_visuals = bool(cat_data or num_data or corr_data or dataset_profile)
        if has_visuals:
            pages.append(
                lambda fig, p_num, p_tot: self._render_page_visual_analytics(
                    fig, report, cat_data, num_data, corr_data, dist_data, dataset_profile
                )
            )

        # Page 4: AI Insights (if available)
        if ai_report is not None:
            pages.append(lambda fig, p_num, p_tot: self._render_page_ai_insights(fig, report, ai_report))

        # Page 5: Recommendations, Governance Limitations & Provenance
        pages.append(
            lambda fig, p_num, p_tot: self._render_page_recommendations_and_lineage(fig, report, ai_report, lineage)
        )

        return pages

    # ==========================================================
    # Global Page Frame (Header & Footer)
    # ==========================================================

    def _draw_page_decorations(
        self,
        fig: plt.Figure,
        page_num: int,
        total_pages: int,
        report_title: str,
    ) -> None:
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
        ax.axis("off")

        # Running Header (pages > 1)
        if page_num > 1:
            ax.text(
                0.08,
                0.965,
                "ANALYSTGPT ENTERPRISE",
                fontsize=8,
                fontweight="bold",
                color=self.COLOR_ACCENT,
                va="top",
            )
            ax.text(
                0.28,
                0.965,
                f"|  {report_title}",
                fontsize=8,
                color=self.COLOR_TEXT_MUTED,
                va="top",
            )
            ax.plot([0.08, 0.92], [0.952, 0.952], color=self.COLOR_BORDER, linewidth=0.75)

        # Running Footer (all pages)
        ax.plot([0.08, 0.92], [0.048, 0.048], color=self.COLOR_BORDER, linewidth=0.75)
        ax.text(
            0.08,
            0.032,
            "Confidential / Internal — AnalystGPT Enterprise Governance Subsystem",
            fontsize=7.5,
            color=self.COLOR_TEXT_MUTED,
            va="bottom",
        )
        ax.text(
            0.92,
            0.032,
            f"Page {page_num} of {total_pages}",
            fontsize=7.5,
            fontweight="bold",
            color=self.COLOR_TEXT_MUTED,
            ha="right",
            va="bottom",
        )

    # ==========================================================
    # Page 1: Executive Cover & Brief
    # ==========================================================

    def _render_page_executive_brief(
        self,
        fig: plt.Figure,
        report: StructuredReport,
        ai_report: Any | None,
        lineage: dict[str, Any] | None,
    ) -> None:
        ax = fig.add_axes((0.08, 0.06, 0.84, 0.88))
        ax.axis("off")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)

        # 1. Top Header Banner Box
        banner_rect = patches.FancyBboxPatch(
            (0.0, 0.84),
            1.0,
            0.16,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            facecolor=self.COLOR_PRIMARY,
            edgecolor="none",
        )
        ax.add_patch(banner_rect)

        ax.text(
            0.04,
            0.96,
            "ANALYSTGPT ENTERPRISE",
            fontsize=10,
            fontweight="bold",
            color=self.COLOR_ACCENT_LIGHT,
            va="top",
        )
        ax.text(
            0.04,
            0.92,
            "Business Analytics & Executive Brief",
            fontsize=18,
            fontweight="bold",
            color="#FFFFFF",
            va="top",
        )

        gen_date = (
            report.generated_at.strftime("%d %b %Y, %H:%M UTC")
            if isinstance(report.generated_at, datetime)
            else str(report.generated_at)
        )
        run_id_str = (
            f"Run: #{lineage.get('pipeline_run_id')}"
            if lineage and lineage.get("pipeline_run_id") is not None
            else "Run: Standard"
        )
        meta_str = (
            f"Dataset: {report.title}   |   {run_id_str}   |   Generated: {gen_date}   |   Classification: Confidential"
        )
        ax.text(
            0.04,
            0.865,
            meta_str,
            fontsize=8,
            color="#94A3B8",
            va="top",
        )

        # 2. Executive Snapshot KPI Cards (Grid of 6 Cards)
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

        kpi_defs = [
            (
                "TOTAL RECORDS",
                f"{total_rows:,}" if isinstance(total_rows, int) else str(total_rows),
                "Verified dataset size",
            ),
            ("TOTAL COLUMNS", str(total_cols), "Ingested schema width"),
            ("COMPLETENESS", comp_pct, "Non-null data ratio"),
            ("DUPLICATE ROWS", f"{duplicates:,}", "Identified duplicate records"),
            ("GOVERNED MEASURES", str(num_cols), "Quantitative metrics"),
            ("DIMENSIONS", str(cat_cols), "Categorical segments"),
        ]

        card_w, card_h = 0.31, 0.085
        spacing_x, spacing_y = 0.035, 0.02
        start_y = 0.72

        for i, (k_label, k_val, k_sub) in enumerate(kpi_defs):
            row = i // 3
            col = i % 3
            cx = col * (card_w + spacing_x)
            cy = start_y - row * (card_h + spacing_y)

            card_patch = patches.FancyBboxPatch(
                (cx, cy),
                card_w,
                card_h,
                boxstyle="round,pad=0.01,rounding_size=0.015",
                facecolor=self.COLOR_BG_CARD,
                edgecolor=self.COLOR_BORDER,
                linewidth=0.75,
            )
            ax.add_patch(card_patch)

            ax.text(
                cx + 0.02,
                cy + card_h - 0.018,
                k_label,
                fontsize=7.5,
                fontweight="bold",
                color=self.COLOR_TEXT_MUTED,
                va="top",
            )
            ax.text(
                cx + 0.02,
                cy + card_h - 0.042,
                k_val,
                fontsize=14,
                fontweight="bold",
                color=self.COLOR_PRIMARY,
                va="top",
            )
            ax.text(cx + 0.02, cy + 0.014, k_sub, fontsize=6.5, color="#94A3B8", va="bottom")

        # 3. Executive Summary Section
        curr_y = 0.52
        ax.text(0.0, curr_y, "EXECUTIVE SUMMARY", fontsize=11, fontweight="bold", color=self.COLOR_PRIMARY, va="top")
        ax.plot([0.0, 1.0], [curr_y - 0.012, curr_y - 0.012], color=self.COLOR_ACCENT, linewidth=1.5)
        curr_y -= 0.03

        summary_text = (
            report.executive_summary
            or "The analytics pipeline completed deterministic data verification and semantic structure analysis."
        )
        if isinstance(summary_text, list):
            summary_text = " ".join(summary_text)

        wrapped_summary = textwrap.fill(summary_text, width=95)
        ax.text(0.0, curr_y, wrapped_summary, fontsize=8.5, color=self.COLOR_TEXT_MAIN, va="top", linespacing=1.4)
        summary_lines_cnt = len(wrapped_summary.split("\n"))
        curr_y -= summary_lines_cnt * 0.022 + 0.03

        # 4. AI-Assisted Analytical Interpretation (if available)
        if ai_report is not None:
            ai_box_top = curr_y
            ai_summary = getattr(ai_report, "executive_summary", None) or (
                ai_report.get("executive_summary") if isinstance(ai_report, dict) else ""
            )
            ai_model = getattr(ai_report, "model", None) or (
                ai_report.get("model") if isinstance(ai_report, dict) else "LLM"
            )
            ai_conf = getattr(ai_report, "confidence", None) or (
                ai_report.get("confidence") if isinstance(ai_report, dict) else "Grounded in deterministic analytics"
            )

            wrapped_ai = textwrap.fill(str(ai_summary), width=90)
            ai_lines_cnt = len(wrapped_ai.split("\n"))
            ai_box_h = min(0.20, ai_lines_cnt * 0.020 + 0.065)

            ai_patch = patches.FancyBboxPatch(
                (0.0, ai_box_top - ai_box_h),
                1.0,
                ai_box_h,
                boxstyle="round,pad=0.01,rounding_size=0.015",
                facecolor=self.COLOR_AI_BG,
                edgecolor=self.COLOR_AI_PURPLE,
                linewidth=0.75,
            )
            ax.add_patch(ai_patch)

            ax.text(
                0.02,
                ai_box_top - 0.015,
                f"AI-ASSISTED ANALYTICAL INTERPRETATION ({ai_model})",
                fontsize=8.5,
                fontweight="bold",
                color=self.COLOR_AI_PURPLE,
                va="top",
            )
            ax.text(
                0.02,
                ai_box_top - 0.040,
                wrapped_ai,
                fontsize=8,
                color=self.COLOR_TEXT_MAIN,
                va="top",
                linespacing=1.35,
            )
            ax.text(
                0.02,
                ai_box_top - ai_box_h + 0.012,
                f"Confidence Basis: {ai_conf}",
                fontsize=7,
                fontstyle="italic",
                color=self.COLOR_AI_PURPLE,
                va="bottom",
            )
            curr_y = ai_box_top - ai_box_h - 0.03

        # 5. Key Takeaways Section
        ax.text(0.0, curr_y, "KEY TAKEAWAYS", fontsize=10.5, fontweight="bold", color=self.COLOR_PRIMARY, va="top")
        ax.plot([0.0, 1.0], [curr_y - 0.012, curr_y - 0.012], color=self.COLOR_BORDER, linewidth=1.0)
        curr_y -= 0.028

        takeaways = self._extract_key_takeaways(report, ai_report)
        for t in takeaways[:3]:
            wrapped_t = textwrap.fill(t, width=90)
            ax.text(0.02, curr_y, f"•  {wrapped_t}", fontsize=8, color=self.COLOR_TEXT_MAIN, va="top", linespacing=1.3)
            curr_y -= len(wrapped_t.split("\n")) * 0.020 + 0.008

        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)

    # ==========================================================
    # Page 2: Dataset Profile & Governance Table
    # ==========================================================

    def _render_page_dataset_governance(
        self,
        fig: plt.Figure,
        report: StructuredReport,
        cols_profile: dict[str, Any],
        lineage: dict[str, Any] | None,
    ) -> None:
        ax = fig.add_axes((0.08, 0.06, 0.84, 0.88))
        ax.axis("off")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)

        # Section Header
        ax.text(
            0.0,
            0.98,
            "DATASET PROFILE & DATA GOVERNANCE",
            fontsize=13,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        ax.text(
            0.0,
            0.95,
            "Comprehensive schema breakdown, semantic classification, and null-governance policy audit.",
            fontsize=8,
            color=self.COLOR_TEXT_MUTED,
            va="top",
        )
        ax.plot([0.0, 1.0], [0.935, 0.935], color=self.COLOR_ACCENT, linewidth=1.5)

        # Profile Summary Pills
        analytics = report.analytics or {}
        desc = analytics.get("descriptive_statistics", {})
        total_rows = desc.get("total_rows", "N/A")
        total_cols = len(cols_profile) or desc.get("total_columns", "N/A")

        pills = [
            f"Schema Width: {total_cols} Columns",
            f"Observed Volume: {total_rows} Records",
            "Audit Standard: Enterprise Strict",
        ]
        pill_str = "   •   ".join(pills)
        ax.text(0.0, 0.895, pill_str, fontsize=8, fontweight="bold", color=self.COLOR_SECONDARY, va="top")

        # Render Governance Table (Columns 0 to 14)
        table_cols = list(cols_profile.items())[:14]
        if table_cols:
            headers = ["Field Name", "Semantic Type", "Analytical Role", "Missing", "Unique", "Governance Policy"]
            cell_data: list[list[str]] = []

            for cname, cdata in table_cols:
                disp_name = cname if len(cname) <= 20 else cname[:18] + "…"
                sem_type = str(cdata.get("semantic_type", "Text")).replace("_", " ").title()
                role = str(cdata.get("analytical_role", "Attribute")).replace("_", " ").title()
                missing_str = f"{cdata.get('missing_count', 0)} ({cdata.get('missing_percentage', 0.0):.1f}%)"
                unique_str = f"{cdata.get('unique_count', 0)} ({cdata.get('uniqueness_percentage', 0.0):.1f}%)"
                policy = str(cdata.get("governance_recommendation", "Standard Validation")).replace("_", " ").title()

                cell_data.append([disp_name, sem_type, role, missing_str, unique_str, policy])

            col_widths = [0.22, 0.16, 0.18, 0.14, 0.14, 0.16]
            table_ax = fig.add_axes((0.08, 0.08, 0.84, 0.76))
            table_ax.axis("off")

            tbl = table_ax.table(
                cellText=cell_data,
                colLabels=headers,
                colWidths=col_widths,
                loc="center",
                cellLoc="left",
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7.2)
            tbl.scale(1.0, 1.25)

            for (r, c), cell in tbl.get_celld().items():
                cell.set_edgecolor(self.COLOR_BORDER)
                cell.set_linewidth(0.5)
                if r == 0:
                    cell.set_facecolor(self.COLOR_SECONDARY)
                    cell.get_text().set_color("#FFFFFF")
                    cell.get_text().set_fontweight("bold")
                    cell.set_height(0.040)
                else:
                    bg = "#FFFFFF" if r % 2 != 0 else self.COLOR_BG_CARD
                    cell.set_facecolor(bg)
                    cell.get_text().set_color(self.COLOR_TEXT_MAIN)
        else:
            ax.text(
                0.0,
                0.85,
                "All dataset fields adhere to standard enterprise schema validation.",
                fontsize=9,
                color=self.COLOR_TEXT_MUTED,
                va="top",
            )

    def _render_page_governance_continuation(
        self,
        fig: plt.Figure,
        report: StructuredReport,
        cols_profile: dict[str, Any],
        start_idx: int = 14,
    ) -> None:
        ax = fig.add_axes((0.08, 0.06, 0.84, 0.88))
        ax.axis("off")

        ax.text(
            0.0,
            0.94,
            "DATASET PROFILE & DATA GOVERNANCE (CONTINUED)",
            fontsize=13,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        ax.plot([0.0, 1.0], [0.91, 0.91], color=self.COLOR_ACCENT, linewidth=1.5)

        table_cols = list(cols_profile.items())[start_idx : start_idx + 18]
        if table_cols:
            headers = ["Field Name", "Semantic Type", "Analytical Role", "Missing", "Unique", "Governance Policy"]
            cell_data = []

            for cname, cdata in table_cols:
                disp_name = cname if len(cname) <= 20 else cname[:18] + "…"
                sem_type = str(cdata.get("semantic_type", "Text")).replace("_", " ").title()
                role = str(cdata.get("analytical_role", "Attribute")).replace("_", " ").title()
                missing_str = f"{cdata.get('missing_count', 0)} ({cdata.get('missing_percentage', 0.0):.1f}%)"
                unique_str = f"{cdata.get('unique_count', 0)} ({cdata.get('uniqueness_percentage', 0.0):.1f}%)"
                policy = str(cdata.get("governance_recommendation", "Standard Validation")).replace("_", " ").title()
                cell_data.append([disp_name, sem_type, role, missing_str, unique_str, policy])

            col_widths = [0.22, 0.16, 0.18, 0.14, 0.14, 0.16]
            table_ax = fig.add_axes((0.08, 0.08, 0.84, 0.80))
            table_ax.axis("off")

            tbl = table_ax.table(
                cellText=cell_data,
                colLabels=headers,
                colWidths=col_widths,
                loc="center",
                cellLoc="left",
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7.2)
            tbl.scale(1.0, 1.25)

            for (r, c), cell in tbl.get_celld().items():
                cell.set_edgecolor(self.COLOR_BORDER)
                cell.set_linewidth(0.5)
                if r == 0:
                    cell.set_facecolor(self.COLOR_SECONDARY)
                    cell.get_text().set_color("#FFFFFF")
                    cell.get_text().set_fontweight("bold")
                    cell.set_height(0.040)
                else:
                    bg = "#FFFFFF" if r % 2 != 0 else self.COLOR_BG_CARD
                    cell.set_facecolor(bg)
                    cell.get_text().set_color(self.COLOR_TEXT_MAIN)

    # ==========================================================
    # Page 3: Visual Analytics & Analytical Findings
    # ==========================================================

    def _render_page_visual_analytics(
        self,
        fig: plt.Figure,
        report: StructuredReport,
        cat_data: dict[str, Any],
        num_data: dict[str, Any],
        corr_data: dict[str, Any],
        dist_data: dict[str, Any],
        dataset_profile: dict[str, Any],
    ) -> None:
        header_ax = fig.add_axes((0.08, 0.88, 0.84, 0.07))
        header_ax.axis("off")
        header_ax.set_xlim(0.0, 1.0)
        header_ax.set_ylim(0.0, 1.0)

        header_ax.text(
            0.0,
            0.95,
            "VISUAL ANALYTICS & EMPIRICAL PATTERNS",
            fontsize=13,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        header_ax.text(
            0.0,
            0.55,
            "Evidence-based distributions, category concentrations, and statistical summaries.",
            fontsize=8,
            color=self.COLOR_TEXT_MUTED,
            va="top",
        )
        header_ax.plot([0.0, 1.0], [0.25, 0.25], color=self.COLOR_ACCENT, linewidth=1.5)

        total_rows = report.analytics.get("descriptive_statistics", {}).get("total_rows") if report.analytics else None

        # Chart 1 (Left): Deterministically Selected Categorical Distribution
        ax_chart1 = fig.add_axes((0.20, 0.54, 0.29, 0.29))
        self._plot_categorical_bar(ax_chart1, cat_data, dataset_profile, total_rows)

        # Chart 2 (Right): Empirical Measure Statistical Summary Card (Never synthetic Gaussian curve)
        ax_chart2 = fig.add_axes((0.57, 0.54, 0.35, 0.29))
        if num_data:
            self._plot_numerical_distribution(ax_chart2, num_data, dist_data)
        else:
            self._plot_dimension_composition(ax_chart2, cat_data, dataset_profile)

        # Bottom Analytical Findings Box
        narrative_ax = fig.add_axes((0.08, 0.08, 0.84, 0.38))
        narrative_ax.axis("off")
        narrative_ax.set_xlim(0.0, 1.0)
        narrative_ax.set_ylim(0.0, 1.0)

        narrative_ax.text(
            0.0, 0.98, "KEY STATISTICAL FINDINGS", fontsize=10.5, fontweight="bold", color=self.COLOR_PRIMARY, va="top"
        )
        narrative_ax.plot([0.0, 1.0], [0.94, 0.94], color=self.COLOR_BORDER, linewidth=1.0)

        findings_lines = self._generate_analytical_narrative(cat_data, num_data, corr_data, total_rows)
        curr_y = 0.86
        for f in findings_lines:
            wrapped = textwrap.fill(f, width=95)
            narrative_ax.text(
                0.01, curr_y, wrapped, fontsize=7.8, color=self.COLOR_TEXT_MAIN, va="top", linespacing=1.35
            )
            curr_y -= len(wrapped.split("\n")) * 0.055 + 0.025

    def _select_best_categorical_dimension(
        self,
        cat_data: dict[str, Any],
        dataset_profile: dict[str, Any],
        total_rows: int | None = None,
    ) -> tuple[str, dict[str, Any]] | None:
        """
        Deterministically selects the most analytically meaningful categorical dimension.
        Excludes PII, identifiers, constants, and near-unique keys.
        """
        if not cat_data:
            return None

        cols_profile = dataset_profile.get("columns", {}) if isinstance(dataset_profile, dict) else {}
        candidates: list[tuple[float, str, dict[str, Any]]] = []

        for col_name, stats in cat_data.items():
            if not isinstance(stats, dict):
                continue
            if is_contact_pii_column(col_name):
                continue

            c_profile = cols_profile.get(col_name, {})
            sem_type = str(c_profile.get("semantic_type", "")).lower()
            role = str(c_profile.get("analytical_role", "")).lower()

            if role in {"identifier", "contact_identifier", "constant_attribute", "descriptive_attribute"}:
                continue
            if sem_type in {
                "phone",
                "email",
                "identifier",
                "constant",
                "person_name",
                "address",
                "free_text",
                "postal_code",
            }:
                continue

            distinct = (
                stats.get("unique_values")
                or stats.get("distinct_count")
                or len(stats.get("value_distribution") or stats.get("top_values") or {})
            )
            if distinct <= 1:
                continue

            if total_rows and total_rows > 20 and distinct >= 0.95 * total_rows:
                continue

            score = 0.0
            if role in {"categorical_dimension", "dimension", "geographic_dimension"}:
                score += 10.0
            if 2 <= distinct <= 10:
                score += 15.0
            elif 11 <= distinct <= 25:
                score += 8.0
            elif distinct > 25:
                score += 2.0

            top_dict = stats.get("value_distribution") or stats.get("top_values") or {}
            if top_dict:
                score += 5.0
                sum_vals = sum(top_dict.values())
                if sum_vals > 0:
                    top_freq = next(iter(top_dict.values()))
                    share = top_freq / sum_vals
                    if 0.15 <= share <= 0.85:
                        score += 5.0

            candidates.append((score, col_name, stats))

        if not candidates:
            return None

        # Sort descending by score, tie-break ascending by column name for determinism
        candidates.sort(key=lambda x: (-x[0], x[1]))
        return (candidates[0][1], candidates[0][2])

    def _plot_categorical_bar(
        self,
        ax: plt.Axes,
        cat_data: dict[str, Any],
        dataset_profile: dict[str, Any],
        total_rows: int | None = None,
    ) -> None:
        ax.set_facecolor(self.COLOR_BG_CARD)
        for spine in ax.spines.values():
            spine.set_color(self.COLOR_BORDER)
            spine.set_linewidth(0.75)

        selection = self._select_best_categorical_dimension(cat_data, dataset_profile, total_rows)
        if not selection:
            ax.text(
                0.5,
                0.5,
                "Categorical Distribution:\nNo eligible dimension with\nmeaningful category cardinality.",
                ha="center",
                va="center",
                fontsize=7.5,
                color=self.COLOR_TEXT_MUTED,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            return

        target_col, target_stats = selection
        top_vals = target_stats.get("value_distribution") or target_stats.get("top_values") or {}

        if isinstance(top_vals, dict) and top_vals:
            items = list(top_vals.items())[:5]
            sum_counts = total_rows or sum(top_vals.values()) or 1

            labels: list[str] = []
            counts: list[int] = []

            for k, v in items[::-1]:
                pct = (v / sum_counts) * 100.0 if sum_counts > 0 else 0.0
                labels.append(f"{str(k)[:10]} ({v:,} | {pct:.1f}%)")
                counts.append(v)

            y_pos = np.arange(len(labels))
            ax.barh(y_pos, counts, height=0.55, color=self.COLOR_ACCENT, alpha=0.85)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=7.2, color=self.COLOR_TEXT_MAIN)
            ax.tick_params(axis="x", labelsize=7, colors=self.COLOR_TEXT_MUTED)
            ax.set_title(
                f"Distribution: {target_col}", fontsize=8.5, fontweight="bold", color=self.COLOR_PRIMARY, pad=6
            )
            ax.grid(axis="x", linestyle="--", alpha=0.4, color=self.COLOR_BORDER)
        else:
            ax.text(
                0.5,
                0.5,
                f"Category count: {len(cat_data)} dimensions",
                ha="center",
                va="center",
                fontsize=8,
                color=self.COLOR_TEXT_MUTED,
            )
            ax.set_xticks([])
            ax.set_yticks([])

    def _plot_numerical_distribution(
        self,
        ax: plt.Axes,
        num_data: dict[str, Any],
        dist_data: dict[str, Any],
    ) -> None:
        """
        Renders an empirical statistical measure card with exact summary statistics.
        NEVER renders a synthetic Gaussian curve.
        """
        ax.set_facecolor(self.COLOR_BG_CARD)
        for spine in ax.spines.values():
            spine.set_color(self.COLOR_BORDER)
            spine.set_linewidth(0.75)

        col_name, stats = next(iter(num_data.items()))
        if not isinstance(stats, dict):
            ax.text(
                0.5,
                0.5,
                "Measure statistics unavailable",
                ha="center",
                va="center",
                fontsize=8,
                color=self.COLOR_TEXT_MUTED,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            return

        # Extract deterministic statistics
        mean_v = stats.get("mean", 0.0)
        med_v = stats.get("median", 0.0)
        std_v = stats.get("standard_deviation", 0.0)
        min_v = stats.get("minimum", 0.0)
        max_v = stats.get("maximum", 0.0)
        q1_v = stats.get("first_quartile")
        q3_v = stats.get("third_quartile")

        dist_info = dist_data.get(col_name, {}) if isinstance(dist_data, dict) else {}
        skew_v = dist_info.get("skewness")
        shape_v = dist_info.get("distribution_shape")

        # Render structured summary card directly onto axis
        ax.axis("off")
        ax.text(
            0.05,
            0.92,
            f"EMPIRICAL MEASURE SUMMARY: {col_name.upper()}",
            fontsize=8.5,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        ax.plot([0.05, 0.95], [0.84, 0.84], color=self.COLOR_BORDER, linewidth=0.75)

        rows = [
            ("Sample Mean", f"{mean_v:,.2f}" if isinstance(mean_v, (int, float)) else str(mean_v)),
            ("Median", f"{med_v:,.2f}" if isinstance(med_v, (int, float)) else str(med_v)),
            ("Std Deviation", f"{std_v:,.2f}" if isinstance(std_v, (int, float)) else str(std_v)),
            (
                "Min / Max Range",
                (
                    f"{min_v:,.2f}  to  {max_v:,.2f}"
                    if isinstance(min_v, (int, float)) and isinstance(max_v, (int, float))
                    else "N/A"
                ),
            ),
        ]
        if q1_v is not None and q3_v is not None:
            rows.append(("Quartiles (Q1 / Q3)", f"{q1_v:,.2f}  /  {q3_v:,.2f}"))
        if skew_v is not None:
            shape_str = f" ({shape_v})" if shape_v else ""
            rows.append(("Skewness", f"{skew_v:.2f}{shape_str}"))

        y_cursor = 0.76
        for label, val in rows:
            ax.text(0.05, y_cursor, label, fontsize=7.2, color=self.COLOR_TEXT_MUTED, va="top")
            ax.text(
                0.95, y_cursor, val, fontsize=7.5, fontweight="bold", color=self.COLOR_PRIMARY, ha="right", va="top"
            )
            y_cursor -= 0.12

    def _plot_dimension_composition(
        self,
        ax: plt.Axes,
        cat_data: dict[str, Any],
        dataset_profile: dict[str, Any],
    ) -> None:
        """
        Renders categorical cardinality profile when no continuous measures exist.
        """
        ax.set_facecolor(self.COLOR_BG_CARD)
        for spine in ax.spines.values():
            spine.set_color(self.COLOR_BORDER)
            spine.set_linewidth(0.75)

        valid_dims = []
        for k in list(cat_data.keys()):
            if not is_contact_pii_column(k):
                valid_dims.append(k)

        display_dims = valid_dims[:5] if valid_dims else list(cat_data.keys())[:5]
        dim_names = [k[:10] for k in display_dims]
        cardinalities = []

        for k in display_dims:
            c_info = cat_data[k]
            if isinstance(c_info, dict):
                cardinalities.append(
                    c_info.get("unique_values")
                    or c_info.get("distinct_count")
                    or len(c_info.get("value_distribution", {}))
                )
            else:
                cardinalities.append(0)

        if cardinalities:
            x_pos = np.arange(len(dim_names))
            ax.bar(x_pos, cardinalities, width=0.5, color="#475569", alpha=0.85)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(dim_names, fontsize=7, rotation=15, ha="right")
            ax.tick_params(axis="y", labelsize=7, colors=self.COLOR_TEXT_MUTED)
            ax.set_title(
                "Categorical Cardinality Profile", fontsize=8.5, fontweight="bold", color=self.COLOR_PRIMARY, pad=6
            )
            ax.grid(axis="y", linestyle="--", alpha=0.4, color=self.COLOR_BORDER)
        else:
            ax.text(
                0.5,
                0.5,
                "Dimension cardinality unavailable",
                ha="center",
                va="center",
                fontsize=8,
                color=self.COLOR_TEXT_MUTED,
            )
            ax.set_xticks([])
            ax.set_yticks([])

    def _generate_analytical_narrative(
        self,
        cat_data: dict[str, Any],
        num_data: dict[str, Any],
        corr_data: dict[str, Any],
        total_rows: int | None = None,
    ) -> list[str]:
        narrative: list[str] = []

        # 1. Categorical Narrative
        if cat_data:
            dim_cnt = len(cat_data)
            dominant_examples = []
            for col, stats in list(cat_data.items())[:2]:
                if isinstance(stats, dict):
                    top = stats.get("value_distribution") or stats.get("top_values") or {}
                    if top:
                        top_k, top_v = next(iter(top.items()))
                        pct_str = f" ({(top_v / total_rows) * 100.0:.1f}%)" if total_rows and total_rows > 0 else ""
                        dominant_examples.append(
                            f"'{col}' most frequent category is '{top_k}' with {top_v} records{pct_str}"
                        )
            example_str = f" Specifically, {'; '.join(dominant_examples)}." if dominant_examples else ""
            narrative.append(
                f"• Categorical Dimensions: The dataset contains {dim_cnt} analyzed categorical dimensions.{example_str}"
            )

        # 2. Numerical Narrative
        if num_data:
            m_summaries = []
            for col, stats in list(num_data.items())[:2]:
                if isinstance(stats, dict):
                    mean_val = stats.get("mean", 0.0)
                    med_val = stats.get("median", 0.0)
                    std_val = stats.get("standard_deviation", 0.0)
                    m_summaries.append(
                        f"'{col}' has mean {mean_val:.2f}, median {med_val:.2f}, and standard deviation {std_val:.2f}"
                    )
            narrative.append(
                f"• Quantitative Measures: Sample statistics for governed measures show {'; '.join(m_summaries)}."
            )
        else:
            narrative.append(
                "• Quantitative Measures: Quantitative relationship analysis was not applicable because the dataset schema contained zero governed numerical measure columns."
            )

        # 3. Correlation Narrative
        corr_mat = corr_data.get("correlation_matrix") if isinstance(corr_data, dict) else {}
        if corr_mat and len(corr_mat) >= 2:
            pos = corr_data.get("strongest_positive", {})
            if pos and pos.get("correlation") is not None:
                narrative.append(
                    f"• Bivariate Association: Strongest observed correlation is between '{pos.get('column_1')}' and '{pos.get('column_2')}' (r = {pos.get('correlation')}). Note: correlation indicates statistical association and does not imply causation."
                )
        else:
            narrative.append(
                "• Bivariate Association: Relationship analysis was not applicable because fewer than two governed numerical measures were available."
            )

        return narrative

    # ==========================================================
    # Page 4: Dedicated AI Insights Section
    # ==========================================================

    def _render_page_ai_insights(
        self,
        fig: plt.Figure,
        report: StructuredReport,
        ai_report: Any,
    ) -> None:
        ax = fig.add_axes((0.08, 0.06, 0.84, 0.88))
        ax.axis("off")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)

        model_name = getattr(ai_report, "model", None) or (
            ai_report.get("model") if isinstance(ai_report, dict) else "Gemma 3"
        )
        provider = getattr(ai_report, "provider", None) or (
            ai_report.get("provider") if isinstance(ai_report, dict) else "Ollama"
        )

        # Header
        ax.text(
            0.0,
            0.94,
            "AI INSIGHTS & STRATEGIC SYNTHESIS",
            fontsize=13,
            fontweight="bold",
            color=self.COLOR_AI_PURPLE,
            va="top",
        )
        ax.text(
            0.0,
            0.91,
            f"Synthesized via {provider} ({model_name}) — Authoritative grounding in deterministic analytics.",
            fontsize=8,
            color=self.COLOR_TEXT_MUTED,
            va="top",
        )
        ax.plot([0.0, 1.0], [0.895, 0.895], color=self.COLOR_AI_PURPLE, linewidth=1.5)

        curr_y = 0.86

        # 1. Key Findings
        findings = (
            getattr(ai_report, "key_findings", None)
            or (ai_report.get("key_findings") if isinstance(ai_report, dict) else None)
            or getattr(ai_report, "explanations", None)
            or (ai_report.get("explanations") if isinstance(ai_report, dict) else [])
        )
        if findings:
            ax.text(
                0.0,
                curr_y,
                "Key Analytical Findings",
                fontsize=10,
                fontweight="bold",
                color=self.COLOR_PRIMARY,
                va="top",
            )
            curr_y -= 0.022
            for f in findings[:2]:
                wrapped_f = textwrap.fill(str(f), width=92)
                ax.text(
                    0.02, curr_y, f"•  {wrapped_f}", fontsize=7.8, color=self.COLOR_TEXT_MAIN, va="top", linespacing=1.3
                )
                curr_y -= len(wrapped_f.split("\n")) * 0.019 + 0.008
            curr_y -= 0.012

        # 2. Business Implications & Opportunities
        implications = getattr(ai_report, "business_implications", None) or (
            ai_report.get("business_implications") if isinstance(ai_report, dict) else []
        )
        if implications:
            ax.text(
                0.0,
                curr_y,
                "Business Implications & Opportunities",
                fontsize=10,
                fontweight="bold",
                color=self.COLOR_PRIMARY,
                va="top",
            )
            curr_y -= 0.022
            for imp in implications[:2]:
                wrapped_imp = textwrap.fill(str(imp), width=92)
                ax.text(
                    0.02,
                    curr_y,
                    f"•  {wrapped_imp}",
                    fontsize=7.8,
                    color=self.COLOR_TEXT_MAIN,
                    va="top",
                    linespacing=1.3,
                )
                curr_y -= len(wrapped_imp.split("\n")) * 0.019 + 0.008
            curr_y -= 0.012

        # 3. Prioritized Actions
        recs = getattr(ai_report, "recommendations", None) or (
            ai_report.get("recommendations") if isinstance(ai_report, dict) else []
        )
        if recs:
            ax.text(
                0.0,
                curr_y,
                "Prioritized Strategic Actions",
                fontsize=10,
                fontweight="bold",
                color=self.COLOR_PRIMARY,
                va="top",
            )
            curr_y -= 0.022
            for idx, r in enumerate(recs[:2], start=1):
                wrapped_r = textwrap.fill(str(r), width=92)
                ax.text(
                    0.02,
                    curr_y,
                    f"{idx}.  {wrapped_r}",
                    fontsize=7.8,
                    color=self.COLOR_TEXT_MAIN,
                    va="top",
                    linespacing=1.3,
                )
                curr_y -= len(wrapped_r.split("\n")) * 0.019 + 0.008
            curr_y -= 0.012

        # 4. Evidence Basis & Confidence
        conf = getattr(ai_report, "confidence", None) or (
            ai_report.get("confidence") if isinstance(ai_report, dict) else "Grounded in deterministic analytics"
        )
        ax.text(
            0.0,
            curr_y,
            "Analytical Confidence & Evidence Basis",
            fontsize=10,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        curr_y -= 0.022
        conf_box = textwrap.fill(
            f"Confidence Level: {conf}. All AI interpretations are programmatically constrained by deterministic calculations and schema profiles.",
            width=92,
        )
        ax.text(0.02, curr_y, conf_box, fontsize=7.5, fontstyle="italic", color=self.COLOR_TEXT_MUTED, va="top")

        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)

    # ==========================================================
    # Page 5: Recommendations, Governance Limitations & Provenance
    # ==========================================================

    def _render_page_recommendations_and_lineage(
        self,
        fig: plt.Figure,
        report: StructuredReport,
        ai_report: Any | None,
        lineage: dict[str, Any] | None,
    ) -> None:
        ax = fig.add_axes((0.08, 0.06, 0.84, 0.88))
        ax.axis("off")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)

        # 1. Recommendations Section
        ax.text(
            0.0,
            0.94,
            "EVIDENCE-LINKED RECOMMENDATIONS",
            fontsize=13,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        ax.text(
            0.0,
            0.91,
            "Conditional operational recommendations strictly grounded in observed dataset evidence.",
            fontsize=8,
            color=self.COLOR_TEXT_MUTED,
            va="top",
        )
        ax.plot([0.0, 1.0], [0.895, 0.895], color=self.COLOR_ACCENT, linewidth=1.5)

        recs = self._build_evidence_recommendations(report)
        curr_y = 0.86
        for obs, imp, act in recs[:2]:
            w_obs = textwrap.fill(f"OBSERVATION: {obs}", width=88)
            w_imp = textwrap.fill(f"INTERPRETATION: {imp}", width=88)
            w_act = textwrap.fill(f"ACTION: {act}", width=88)

            obs_lines = len(w_obs.split("\n"))
            imp_lines = len(w_imp.split("\n"))
            act_lines = len(w_act.split("\n"))

            card_h = (obs_lines + imp_lines + act_lines) * 0.018 + 0.040

            card_patch = patches.FancyBboxPatch(
                (0.0, curr_y - card_h),
                1.0,
                card_h,
                boxstyle="round,pad=0.01,rounding_size=0.012",
                facecolor=self.COLOR_BG_CARD,
                edgecolor=self.COLOR_BORDER,
                linewidth=0.75,
            )
            ax.add_patch(card_patch)

            text_y = curr_y - 0.014
            ax.text(
                0.02,
                text_y,
                w_obs,
                fontsize=7.5,
                fontweight="bold",
                color=self.COLOR_PRIMARY,
                va="top",
                linespacing=1.25,
            )
            text_y -= obs_lines * 0.018 + 0.006

            ax.text(0.02, text_y, w_imp, fontsize=7.2, color=self.COLOR_TEXT_MUTED, va="top", linespacing=1.25)
            text_y -= imp_lines * 0.018 + 0.006

            ax.text(
                0.02,
                text_y,
                w_act,
                fontsize=7.5,
                fontweight="bold",
                color=self.COLOR_ACCENT,
                va="top",
                linespacing=1.25,
            )

            curr_y -= card_h + 0.016

        # 2. Data Limitations & Caveats
        curr_y -= 0.01
        ax.text(
            0.0,
            curr_y,
            "GOVERNANCE BOUNDARIES & LIMITATIONS",
            fontsize=10.5,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        ax.plot([0.0, 1.0], [curr_y - 0.012, curr_y - 0.012], color=self.COLOR_BORDER, linewidth=1.0)
        curr_y -= 0.028

        limitations = [
            "• Scope Constraint: Analysis is strictly bounded by ingested dataset fields and observed records.",
            "• Non-Causality   : Observational records describe correlation and distribution; causal conclusions require experimental validation.",
            "• Domain Context  : Business actions should validate these empirical findings with domain operational experts.",
        ]
        for lim in limitations:
            ax.text(0.01, curr_y, lim, fontsize=7.5, color=self.COLOR_TEXT_MAIN, va="top")
            curr_y -= 0.022

        # 3. Lineage & Provenance Metadata Box
        curr_y -= 0.015
        ax.text(
            0.0,
            curr_y,
            "DATA LINEAGE & PROVENANCE",
            fontsize=10.5,
            fontweight="bold",
            color=self.COLOR_PRIMARY,
            va="top",
        )
        ax.plot([0.0, 1.0], [curr_y - 0.012, curr_y - 0.012], color=self.COLOR_BORDER, linewidth=1.0)
        curr_y -= 0.028

        lineage_h = 0.12
        lineage_patch = patches.FancyBboxPatch(
            (0.0, curr_y - lineage_h),
            1.0,
            lineage_h,
            boxstyle="round,pad=0.01,rounding_size=0.012",
            facecolor="#F1F5F9",
            edgecolor=self.COLOR_BORDER,
            linewidth=0.75,
        )
        ax.add_patch(lineage_patch)

        run_id = lineage.get("pipeline_run_id") if lineage else "N/A"
        src_ver = str(lineage.get("source_version_id") if lineage else "src_canonical")
        clean_ver = str(lineage.get("cleaned_version_id") if lineage else "clean_validated")
        if len(src_ver) > 24:
            src_ver = src_ver[:22] + "…"
        if len(clean_ver) > 24:
            clean_ver = clean_ver[:22] + "…"

        ai_info = (
            f"{getattr(ai_report, 'provider', 'None')} / {getattr(ai_report, 'model', 'N/A')}"
            if ai_report
            else "Deterministic Only"
        )

        col1_text = f"• Pipeline Run ID: {run_id}\n• Source Version: {src_ver}\n• Cleaned Version: {clean_ver}"
        col2_text = f"• Analytics Engine: AnalystGPT Enterprise 2.0\n• AI Synthesis: {ai_info}\n• Report Architecture: Enterprise Brief"

        ax.text(0.03, curr_y - 0.020, col1_text, fontsize=7.5, color=self.COLOR_TEXT_MAIN, va="top", linespacing=1.4)
        ax.text(0.52, curr_y - 0.020, col2_text, fontsize=7.5, color=self.COLOR_TEXT_MAIN, va="top", linespacing=1.4)

    # ==========================================================
    # Helper Utilities
    # ==========================================================

    def _extract_key_takeaways(
        self,
        report: StructuredReport,
        ai_report: Any | None,
    ) -> list[str]:
        takeaways: list[str] = []
        analytics = report.analytics or {}
        cat_data = analytics.get("categorical_analysis", {})
        num_data = analytics.get("numerical_analysis", {})

        if cat_data:
            dim_cnt = len(cat_data)
            takeaways.append(
                f"Categorical Segmentation: {dim_cnt} categorical dimensions identified for empirical grouping."
            )
        if num_data:
            num_cnt = len(num_data)
            takeaways.append(
                f"Governed Measures: {num_cnt} continuous numerical measures analyzed with verified summary statistics."
            )
        else:
            takeaways.append(
                "Measure Availability: Zero governed continuous measures detected; analysis is focused on categorical distributions."
            )

        if ai_report is not None:
            findings = getattr(ai_report, "key_findings", None) or (
                ai_report.get("key_findings") if isinstance(ai_report, dict) else None
            )
            if findings and len(findings) > 0:
                takeaways.append(f"AI Interpretation: {findings[0]}")

        if not takeaways:
            takeaways.append(
                "Data Ingestion: All dataset rows and columns verified against baseline enterprise quality rules."
            )

        return takeaways

    def _build_evidence_recommendations(
        self,
        report: StructuredReport,
    ) -> list[tuple[str, str, str]]:
        """
        Builds evidence-linked recommendations adhering strictly to:
        OBSERVATION -> INTERPRETATION -> CONDITIONAL ACTION.
        Never infers operational workflows, staffing, or unobserved revenue impact.
        """
        recs: list[tuple[str, str, str]] = []
        analytics = report.analytics or {}
        cat_data = analytics.get("categorical_analysis", {})
        num_data = analytics.get("numerical_analysis", {})
        total_rows = analytics.get("descriptive_statistics", {}).get("total_rows") or report.kpis.get("Rows") or 0

        if cat_data:
            for col_name, stats in cat_data.items():
                if is_contact_pii_column(col_name):
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
