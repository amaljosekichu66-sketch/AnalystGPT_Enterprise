"""
Unit and Property Tests for DataProfiler.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.profiling.data_profiler import DataProfiler
from src.profiling.models import AnalyticalRole, SemanticType


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "First Name": ["Alice", "Bob", "Charlie", "David", None],
            "Last Name": ["Smith", "Johnson", "Williams", "Jones", "Brown"],
            "City": ["New York", "Chicago", "Houston", "Phoenix", "New York"],
            "Lead_Status": ["Open", "Contacted", "Qualified", "Closed", "Open"],
            "Campaign": ["Summer_2026", "Summer_2026", "Summer_2026", "Summer_2026", "Summer_2026"],
            "Phone": ["+16474107503", "846-213-0121", "555-123-4567", "415-888-9999", None],
            "State": ["NY", "IL", "TX", "AZ", "NY"],
            "Street": ["123 Main St", "456 Elm Ave", "789 Oak Rd", "101 Pine Blvd", "202 Maple Dr"],
            "Unique_Data": ["UQ-001", "UQ-002", "UQ-003", "UQ-004", "UQ-005"],
            "Zip Code": ["06857", "02396", "73973", "59185", "06857"],
            "Revenue": ["$12,500.50", "$4,500.00", "$8,900.25", "$15,200.00", "$3,100.00"],
            "Age": ["29", "45", "33", "52", "24"],
        }
    )


def test_data_profiler_comprehensive_metrics(sample_dataframe: pd.DataFrame):
    profiler = DataProfiler()
    profile = profiler.profile_dataset(sample_dataframe)

    assert profile.row_count == 5
    assert profile.column_count == 12
    assert profile.has_missing_values is True
    assert profile.total_missing_cells == 2
    assert profile.overall_completeness_pct < 100.0

    # Verify column roles and semantics
    phone_cp = profile.get_column("Phone")
    assert phone_cp is not None
    assert phone_cp.semantic_type == SemanticType.PHONE
    assert phone_cp.is_visualizable is False

    campaign_cp = profile.get_column("Campaign")
    assert campaign_cp is not None
    assert campaign_cp.semantic_type == SemanticType.CONSTANT
    assert campaign_cp.is_visualizable is False

    rev_cp = profile.get_column("Revenue")
    assert rev_cp is not None
    assert rev_cp.semantic_type == SemanticType.NUMERIC_MEASURE
    assert rev_cp.is_visualizable is True

    zip_cp = profile.get_column("Zip Code")
    assert zip_cp is not None
    assert zip_cp.semantic_type == SemanticType.POSTAL_CODE


def test_create_analytical_view_preserves_postal_code_and_casts_measures(sample_dataframe: pd.DataFrame):
    profiler = DataProfiler()
    profile = profiler.profile_dataset(sample_dataframe)
    view_df = profiler.create_analytical_view(sample_dataframe, profile)

    # Revenue should now be numeric float
    assert pd.api.types.is_numeric_dtype(view_df["Revenue"])
    assert view_df["Revenue"].iloc[0] == 12500.50

    # Zip code should preserve leading zeros
    assert view_df["Zip Code"].iloc[0] == "06857"
    assert view_df["Zip Code"].iloc[1] == "02396"

    # Original DataFrame must remain unmutated
    assert sample_dataframe["Revenue"].iloc[0] == "$12,500.50"
