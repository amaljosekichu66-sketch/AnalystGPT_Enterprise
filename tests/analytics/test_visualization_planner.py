"""
Unit and Property Tests for VisualizationPlanner.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.analytics.visualization_planner import VisualizationPlanner
from src.profiling.data_profiler import DataProfiler


@pytest.fixture
def complex_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "First Name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"] * 10,
            "Last Name": ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis"] * 10,
            "City": ["New York", "Chicago", "Houston", "Phoenix", "New York", "Chicago"] * 10,
            "Lead_Status": ["Open", "Contacted", "Qualified", "Closed", "Open", "Contacted"] * 10,
            "Campaign": ["Summer_2026"] * 60,
            "Phone": [f"+1647410750{i}" for i in range(60)],
            "State": ["NY", "IL", "TX", "AZ", "NY", "IL"] * 10,
            "Street": [f"{i} Main St" for i in range(60)],
            "Unique_Data": [f"UQ-{i:03d}" for i in range(60)],
            "Zip Code": ["06857", "02396", "73973", "59185", "06857", "02396"] * 10,
            "Revenue": [12500.50, 4500.00, 8900.25, 15200.00, 3100.00, 11450.75] * 10,
            "Age": [29, 45, 33, 52, 24, 41] * 10,
        }
    )


def test_visualization_planner_budget_and_exclusions(complex_dataframe: pd.DataFrame):
    profiler = DataProfiler()
    profile = profiler.profile_dataset(complex_dataframe)

    planner = VisualizationPlanner()
    plan = planner.plan_visualizations(complex_dataframe, profile, max_charts=6)

    # 1. Budget enforcement (<= 6 charts)
    assert plan.total_charts <= 6
    assert plan.total_charts >= 2

    # 2. Excluded columns check (Phone, Street, Campaign, Unique_Data, First Name, Last Name must not be charted)
    chart_cols = [c.primary_column for c in plan.charts] + [c.secondary_column for c in plan.charts if c.secondary_column]
    assert "Phone" not in chart_cols
    assert "Campaign" not in chart_cols
    assert "Unique_Data" not in chart_cols
    assert "First Name" not in chart_cols
    assert "Street" not in chart_cols

    # 3. Meaningful charts are present
    chart_types = [c.chart_type for c in plan.charts]
    assert "histogram" in chart_types
    assert "horizontal_bar" in chart_types

    # 4. Excluded columns list is populated
    assert len(plan.excluded_columns) > 0


def test_visualization_planner_empty_dataframe():
    empty_df = pd.DataFrame()
    profiler = DataProfiler()
    profile = profiler.profile_dataset(empty_df)

    planner = VisualizationPlanner()
    plan = planner.plan_visualizations(empty_df, profile)
    assert plan.total_charts == 0
    assert plan.charts == []
