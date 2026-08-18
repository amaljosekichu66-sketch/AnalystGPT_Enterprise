"""
Visualization Planner for AnalystGPT Enterprise.

Determines an optimal, high-value set of visualizations based on column
semantic profiles, analytical roles, cardinality, correlation, and dataset structure.
Enforces a chart budget and eliminates meaningless identifier/constant plots.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.core.logger import logger
from src.profiling.models import (
    AnalyticalRole,
    ColumnProfile,
    DatasetProfile,
    SemanticType,
)


@dataclass(frozen=True)
class PlannedChart:
    """
    Specification for a single analytical visualization card.
    """

    chart_id: str
    chart_type: str  # "histogram", "horizontal_bar", "scatter", "line", "correlation_heatmap", "missingness_bar"
    title: str
    subtitle: str
    primary_column: str
    secondary_column: str | None = None
    grid_span: int = 1  # 1 = standard card, 2 = wide card
    chart_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualizationPlan:
    """
    Authoritative visualization plan for dashboard and export rendering.
    """

    charts: list[PlannedChart]
    total_charts: int
    layout_grid: str  # "2x2", "3x3", "single"
    excluded_columns: list[str] = field(default_factory=list)
    plan_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_charts": self.total_charts,
            "layout_grid": self.layout_grid,
            "excluded_columns": self.excluded_columns,
            "plan_summary": self.plan_summary,
            "charts": [c.to_dict() for c in self.charts],
        }


class VisualizationPlanner:
    """
    Intelligent analytical chart planner enforcing a 4-8 chart budget and selective visual storytelling.
    """

    MIN_BUDGET = 2
    DEFAULT_MAX_BUDGET = 6
    MAX_BUDGET = 8

    def plan_visualizations(
        self,
        dataframe: pd.DataFrame,
        profile: DatasetProfile,
        max_charts: int = DEFAULT_MAX_BUDGET,
    ) -> VisualizationPlan:
        """
        Produce a cohesive VisualizationPlan from a DataFrame and its semantic profile.
        """
        logger.info("Planning visual analytics (budget=%d)...", max_charts)

        planned_charts: list[PlannedChart] = []
        excluded_columns: list[str] = []

        # Collect columns by analytical roles
        measures = profile.get_columns_by_role(AnalyticalRole.MEASURE) + profile.get_columns_by_role(AnalyticalRole.DEMOGRAPHIC_MEASURE)
        dimensions = profile.get_columns_by_role(AnalyticalRole.CATEGORICAL_DIMENSION) + profile.get_columns_by_role(AnalyticalRole.GEOGRAPHIC_DIMENSION)
        temporals = profile.get_columns_by_role(AnalyticalRole.TEMPORAL_DIMENSION)
        constants = profile.get_columns_by_role(AnalyticalRole.CONSTANT_ATTRIBUTE)
        identifiers = profile.get_columns_by_role(AnalyticalRole.IDENTIFIER) + profile.get_columns_by_role(AnalyticalRole.CONTACT_IDENTIFIER)
        descriptives = profile.get_columns_by_role(AnalyticalRole.DESCRIPTIVE_ATTRIBUTE)

        # Record exclusions
        for col in constants:
            excluded_columns.append(f"{col.column_name} (constant / single-value field)")
        for col in identifiers:
            excluded_columns.append(f"{col.column_name} ({col.semantic_type.value} identifier)")
        for col in descriptives:
            excluded_columns.append(f"{col.column_name} ({col.semantic_type.value} descriptive text)")

        # 1. Missingness Overview (if dataset has missing values)
        cols_with_missing = profile.get_columns_with_missing()
        if cols_with_missing and len(planned_charts) < max_charts:
            missing_dict = {cp.column_name: cp.missing_count for cp in cols_with_missing}
            # Top missing columns
            sorted_missing = dict(sorted(missing_dict.items(), key=lambda x: x[1], reverse=True)[:8])
            planned_charts.append(
                PlannedChart(
                    chart_id="missingness_overview",
                    chart_type="missingness_bar",
                    title="Missing Values Overview",
                    subtitle=f"{len(cols_with_missing)} columns contain nulls ({profile.total_missing_cells:,} cells total)",
                    primary_column="all_missing",
                    grid_span=1,
                    chart_payload={"missing_counts": sorted_missing},
                )
            )

        # 2. Key Numeric Distributions (Histograms / KDE)
        # Select top 2 measures
        for cp in measures[:2]:
            if len(planned_charts) >= max_charts:
                break
            series = pd.to_numeric(
                dataframe[cp.column_name].astype(str).str.replace(r"[\$,€,£,¥,₹]", "", regex=True).str.replace(",", ""),
                errors="coerce",
            ).dropna()

            if not series.empty and series.nunique() > 1:
                mean_val = float(series.mean())
                median_val = float(series.median())
                std_val = float(series.std()) if len(series) > 1 else 0.0
                planned_charts.append(
                    PlannedChart(
                        chart_id=f"dist_{cp.column_name}",
                        chart_type="histogram",
                        title=f"{cp.column_name.replace('_', ' ').title()} Distribution",
                        subtitle=f"Median: {median_val:,.2f} | Mean: {mean_val:,.2f} | Std: {std_val:,.2f}",
                        primary_column=cp.column_name,
                        grid_span=1,
                        chart_payload={
                            "series_data": series.sample(min(len(series), 5000), random_state=42).tolist(),
                            "bins": 25,
                            "mean": mean_val,
                            "median": median_val,
                        },
                    )
                )

        # 3. Meaningful Categorical Distributions (Top-N Horizontal Bar)
        # Pick top 2 dimensions with low/medium cardinality
        valid_dims = [d for d in dimensions if 2 <= d.unique_count <= 50]
        for cp in valid_dims[:2]:
            if len(planned_charts) >= max_charts:
                break
            vc = dataframe[cp.column_name].fillna("Missing").value_counts()
            top_10 = vc.head(10)
            if len(vc) > 10:
                other_sum = vc.iloc[10:].sum()
                top_10["Other"] = other_sum

            planned_charts.append(
                PlannedChart(
                    chart_id=f"cat_{cp.column_name}",
                    chart_type="horizontal_bar",
                    title=f"{cp.column_name.replace('_', ' ').title()} Breakdown",
                    subtitle=f"{cp.unique_count} distinct categories | Top: {vc.index[0]} ({vc.iloc[0]:,})",
                    primary_column=cp.column_name,
                    grid_span=1,
                    chart_payload={
                        "categories": list(top_10.index.astype(str)),
                        "counts": [int(v) for v in top_10.values],
                    },
                )
            )

        # 4. Correlation / Scatter Plot (If >= 2 numeric measures exist)
        if len(measures) >= 2 and len(planned_charts) < max_charts:
            m1_name, m2_name = measures[0].column_name, measures[1].column_name
            s1 = pd.to_numeric(dataframe[m1_name].astype(str).str.replace(r"[\$,€,£,¥,₹]", "", regex=True).str.replace(",", ""), errors="coerce")
            s2 = pd.to_numeric(dataframe[m2_name].astype(str).str.replace(r"[\$,€,£,¥,₹]", "", regex=True).str.replace(",", ""), errors="coerce")
            paired = pd.DataFrame({m1_name: s1, m2_name: s2}).dropna()

            if len(paired) > 5:
                corr_val = float(paired[m1_name].corr(paired[m2_name]))
                sample_paired = paired.sample(min(len(paired), 1000), random_state=42)
                planned_charts.append(
                    PlannedChart(
                        chart_id=f"scatter_{m1_name}_{m2_name}",
                        chart_type="scatter",
                        title=f"{m1_name.replace('_', ' ').title()} vs {m2_name.replace('_', ' ').title()}",
                        subtitle=f"Pearson Correlation: r = {corr_val:.4f}",
                        primary_column=m1_name,
                        secondary_column=m2_name,
                        grid_span=1,
                        chart_payload={
                            "x_data": sample_paired[m1_name].tolist(),
                            "y_data": sample_paired[m2_name].tolist(),
                            "correlation": corr_val,
                        },
                    )
                )

        # 5. Correlation Heatmap (If >= 3 numeric measures exist)
        if len(measures) >= 3 and len(planned_charts) < max_charts:
            num_cols = [m.column_name for m in measures[:6]]
            num_sub_df = pd.DataFrame()
            for col in num_cols:
                num_sub_df[col] = pd.to_numeric(
                    dataframe[col].astype(str).str.replace(r"[\$,€,£,¥,₹]", "", regex=True).str.replace(",", ""),
                    errors="coerce",
                )
            corr_mat = num_sub_df.corr().round(3)
            planned_charts.append(
                PlannedChart(
                    chart_id="correlation_heatmap",
                    chart_type="correlation_heatmap",
                    title="Correlation Matrix",
                    subtitle="Pairwise relationships across numerical measures",
                    primary_column="all_measures",
                    grid_span=1,
                    chart_payload={
                        "columns": num_cols,
                        "matrix": corr_mat.fillna(0.0).values.tolist(),
                    },
                )
            )

        # 6. Temporal Trend Line (If temporal column + measure exist)
        if temporals and measures and len(planned_charts) < max_charts:
            t_col = temporals[0].column_name
            m_col = measures[0].column_name
            try:
                t_series = pd.to_datetime(dataframe[t_col], errors="coerce")
                m_series = pd.to_numeric(
                    dataframe[m_col].astype(str).str.replace(r"[\$,€,£,¥,₹]", "", regex=True).str.replace(",", ""),
                    errors="coerce",
                )
                temp_df = pd.DataFrame({"time": t_series, "measure": m_series}).dropna().sort_values("time")
                if len(temp_df) > 2:
                    # Aggregate by day or month if dense
                    grouped = temp_df.set_index("time").resample("M").mean().dropna()
                    if len(grouped) < 3:
                        grouped = temp_df.set_index("time").resample("D").mean().dropna()

                    planned_charts.append(
                        PlannedChart(
                            chart_id=f"trend_{t_col}_{m_col}",
                            chart_type="line",
                            title=f"{m_col.replace('_', ' ').title()} Over Time",
                            subtitle=f"Temporal trend indexed by {t_col.replace('_', ' ')}",
                            primary_column=t_col,
                            secondary_column=m_col,
                            grid_span=1,
                            chart_payload={
                                "dates": [str(d.date()) for d in grouped.index],
                                "values": [round(float(v), 2) for v in grouped["measure"].values],
                            },
                        )
                    )
            except Exception as e:
                logger.warning("Could not plan temporal trend: %s", e)

        # 7. Category vs Measure Breakdown (If dimension + measure exist)
        if valid_dims and measures and len(planned_charts) < max_charts:
            d_col = valid_dims[0].column_name
            m_col = measures[0].column_name
            m_num = pd.to_numeric(
                dataframe[m_col].astype(str).str.replace(r"[\$,€,£,¥,₹]", "", regex=True).str.replace(",", ""),
                errors="coerce",
            )
            agg_df = pd.DataFrame({d_col: dataframe[d_col], m_col: m_num}).dropna()
            if not agg_df.empty:
                grouped = agg_df.groupby(d_col)[m_col].mean().sort_values(ascending=False).head(8)
                planned_charts.append(
                    PlannedChart(
                        chart_id=f"group_{d_col}_{m_col}",
                        chart_type="horizontal_bar",
                        title=f"Mean {m_col.replace('_', ' ').title()} by {d_col.replace('_', ' ').title()}",
                        subtitle=f"Average {m_col.replace('_', ' ')} across top {d_col.replace('_', ' ')} categories",
                        primary_column=d_col,
                        secondary_column=m_col,
                        grid_span=1,
                        chart_payload={
                            "categories": list(grouped.index.astype(str)),
                            "counts": [round(float(v), 2) for v in grouped.values],
                        },
                    )
                )

        layout_grid = "2x2" if len(planned_charts) <= 4 else "3x3"
        total_charts = len(planned_charts)
        plan_summary = f"Selected {total_charts} high-value visualizations across {len(measures)} measures and {len(dimensions)} dimensions."

        logger.info("Visual analytics plan complete: %d charts planned (layout=%s).", total_charts, layout_grid)

        return VisualizationPlan(
            charts=planned_charts,
            total_charts=total_charts,
            layout_grid=layout_grid,
            excluded_columns=excluded_columns,
            plan_summary=plan_summary,
        )
