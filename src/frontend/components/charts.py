"""
Chart Component for AnalystGPT Enterprise.

Renders high-value visual analytics cards arranged in a responsive
2x2 / 3x3 dashboard grid, powered by the authoritative VisualizationPlanner.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from src.analytics.visualization_planner import (
    PlannedChart,
    VisualizationPlan,
    VisualizationPlanner,
)
from src.core.config import MAX_CHART_ROWS
from src.profiling.data_profiler import DataProfiler
from src.profiling.models import DatasetProfile


def _style_axes(ax: plt.Axes, title: str, subtitle: str = "") -> None:
    """Apply clean enterprise styling to matplotlib axes."""
    ax.set_facecolor("#1E222A")
    ax.grid(True, linestyle="--", alpha=0.2, color="#718096")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#4A5568")
    ax.spines["bottom"].set_color("#4A5568")
    ax.tick_params(colors="#CBD5E0", labelsize=8)
    if title:
        ax.set_title(title, fontsize=10, fontweight="bold", color="#F7FAFC", pad=10)


def _render_single_chart(chart: PlannedChart, dataframe: pd.DataFrame) -> None:
    """Render a single planned chart card."""
    with st.container(border=True):
        st.markdown(f"**{chart.title}**")
        if chart.subtitle:
            st.caption(chart.subtitle)

        fig, ax = plt.subplots(figsize=(5.5, 3.2), facecolor="#14171F")
        _style_axes(ax, "")

        payload = chart.chart_payload

        if chart.chart_type == "histogram":
            data = payload.get("series_data", [])
            if data:
                n, bins, patches = ax.hist(
                    data,
                    bins=payload.get("bins", 20),
                    color="#3182CE",
                    edgecolor="#2B6CB0",
                    alpha=0.85,
                )
                median_val = payload.get("median")
                if median_val is not None:
                    ax.axvline(
                        median_val,
                        color="#ECC94B",
                        linestyle="--",
                        linewidth=1.5,
                        label=f"Median: {median_val:,.1f}",
                    )
                    ax.legend(fontsize=7, facecolor="#1E222A", edgecolor="#4A5568", labelcolor="#F7FAFC")
                ax.set_ylabel("Frequency", color="#A0AEC0", fontsize=8)

        elif chart.chart_type == "horizontal_bar":
            categories = payload.get("categories", [])
            counts = payload.get("counts", [])
            if categories and counts:
                y_pos = np.arange(len(categories))
                ax.barh(y_pos, counts, color="#38B2AC", edgecolor="#2C7A7B", alpha=0.85, height=0.6)
                ax.set_yticks(y_pos)
                ax.set_yticklabels([str(c)[:18] for c in categories], fontsize=8, color="#CBD5E0")
                ax.invert_yaxis()
                ax.set_xlabel("Count / Value", color="#A0AEC0", fontsize=8)

        elif chart.chart_type == "missingness_bar":
            missing_dict = payload.get("missing_counts", {})
            if missing_dict:
                cols = list(missing_dict.keys())
                vals = list(missing_dict.values())
                y_pos = np.arange(len(cols))
                ax.barh(y_pos, vals, color="#E53E3E", edgecolor="#C53030", alpha=0.85, height=0.6)
                ax.set_yticks(y_pos)
                ax.set_yticklabels([str(c)[:18] for c in cols], fontsize=8, color="#CBD5E0")
                ax.invert_yaxis()
                ax.set_xlabel("Missing Cells", color="#A0AEC0", fontsize=8)

        elif chart.chart_type == "scatter":
            x_data = payload.get("x_data", [])
            y_data = payload.get("y_data", [])
            if x_data and y_data:
                ax.scatter(x_data, y_data, color="#805AD5", alpha=0.6, edgecolors="none", s=25)
                ax.set_xlabel(str(chart.primary_column).replace("_", " ").title(), color="#A0AEC0", fontsize=8)
                ax.set_ylabel(str(chart.secondary_column).replace("_", " ").title(), color="#A0AEC0", fontsize=8)

        elif chart.chart_type == "line":
            dates = payload.get("dates", [])
            values = payload.get("values", [])
            if dates and values:
                ax.plot(range(len(dates)), values, color="#48BB78", linewidth=1.8, marker="o", markersize=3)
                step = max(1, len(dates) // 5)
                ax.set_xticks(range(0, len(dates), step))
                ax.set_xticklabels(
                    [dates[i] for i in range(0, len(dates), step)], rotation=25, fontsize=7, color="#CBD5E0"
                )
                ax.set_ylabel("Value", color="#A0AEC0", fontsize=8)

        elif chart.chart_type == "correlation_heatmap":
            cols = payload.get("columns", [])
            matrix = np.array(payload.get("matrix", []))
            if len(cols) >= 2 and matrix.size > 0:
                cax = ax.matshow(matrix, cmap="coolwarm", vmin=-1, vmax=1)
                fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
                ax.set_xticks(range(len(cols)))
                ax.set_yticks(range(len(cols)))
                ax.set_xticklabels([str(c)[:8] for c in cols], rotation=45, ha="left", fontsize=7, color="#CBD5E0")
                ax.set_yticklabels([str(c)[:8] for c in cols], fontsize=7, color="#CBD5E0")
                for i in range(len(cols)):
                    for j in range(len(cols)):
                        ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="#F7FAFC", fontsize=6)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


def render_charts(
    dataframe: pd.DataFrame,
    profile: DatasetProfile | None = None,
    plan: VisualizationPlan | None = None,
) -> None:
    """
    Render visual analytics cards arranged in a responsive 2x2 or 3x3 grid.
    """
    if dataframe.empty:
        st.info("No data available for visualization.")
        return

    # 1. Resolve Profile and Plan
    if profile is None:
        profiler = DataProfiler()
        profile = profiler.profile_dataset(dataframe)

    if plan is None:
        planner = VisualizationPlanner()
        plan = planner.plan_visualizations(dataframe, profile)

    if not plan.charts:
        st.info("No meaningful visual analytics available for this dataset structure.")
        if plan.excluded_columns:
            with st.expander("ℹ️ Why were some columns excluded from charts?"):
                for exc in plan.excluded_columns:
                    st.write(f"- {exc}")
        return

    # 2. Render Grid Layout (2x2 or 3x3)
    charts = plan.charts
    num_cols = 2  # Default clean 2-column grid
    rows = [charts[i : i + num_cols] for i in range(0, len(charts), num_cols)]

    for row in rows:
        cols = st.columns(num_cols)
        for idx, chart in enumerate(row):
            with cols[idx]:
                _render_single_chart(chart, dataframe)

    # 3. Excluded Columns Summary Expander
    if plan.excluded_columns:
        with st.expander(f"ℹ️ Excluded Columns ({len(plan.excluded_columns)} low-information / identifier fields)"):
            st.caption(
                "To maintain dashboard focus, constant columns, unique keys, and contact fields are omitted from default charts."
            )
            for exc in plan.excluded_columns:
                st.markdown(f"- `{exc}`")
