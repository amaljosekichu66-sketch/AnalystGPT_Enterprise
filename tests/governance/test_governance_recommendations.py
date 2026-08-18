"""
Unit and Property Tests for Semantically Aware Null Governance Recommendations.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.governance.governance_service import CleaningGovernanceService
from src.governance.models import CleaningConfig, MissingValuePolicy
from src.governance.preview_service import CleaningPreviewService
from src.profiling.data_profiler import DataProfiler


def test_recommend_policy_for_numeric_missingness():
    df = pd.DataFrame(
        {
            "Revenue": [100.0, None, 300.0, 400.0, None],
            "Cost": [50.0, 60.0, None, 80.0, 90.0],
            "Department": ["Sales", "Engineering", "Marketing", "Sales", "Engineering"],
        }
    )
    profiler = DataProfiler()
    profile = profiler.profile_dataset(df)

    gov_service = CleaningGovernanceService()
    policy, reason = gov_service.recommend_dataset_policy(profile)

    assert policy == MissingValuePolicy.FILL_NUMERIC_MEDIAN
    assert "numeric measures" in reason


def test_recommend_policy_for_categorical_missingness():
    df = pd.DataFrame(
        {
            "Revenue": [100.0, 200.0, 300.0, 400.0, 500.0],
            "Department": ["Sales", None, "Marketing", "Sales", None],
            "City": ["NYC", "Chicago", None, "NYC", "Chicago"],
        }
    )
    profiler = DataProfiler()
    profile = profiler.profile_dataset(df)

    gov_service = CleaningGovernanceService()
    policy, reason = gov_service.recommend_dataset_policy(profile)

    assert policy == MissingValuePolicy.FILL_CATEGORICAL_MODE
    assert "categorical" in reason


def test_preview_service_non_destructive_isolation():
    raw_df = pd.DataFrame(
        {
            "Revenue": [100.0, None, 300.0],
            "Department": ["Sales", "Support", None],
        }
    )
    original_copy = raw_df.copy(deep=True)

    preview_service = CleaningPreviewService()
    cfg = CleaningConfig(
        config_id="test-prev",
        missing_value_policy=MissingValuePolicy.DROP_ROWS,
    )
    result = preview_service.preview(raw_df, cfg)

    # Raw DF must remain 100% identical and unmutated
    pd.testing.assert_frame_equal(raw_df, original_copy)

    # Preview results reflect policy
    assert result.quality_comparison.rows_removed == 2
    assert result.quality_comparison.cleaned.row_count == 1
