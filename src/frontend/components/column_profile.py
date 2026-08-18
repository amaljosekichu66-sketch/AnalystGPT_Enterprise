"""
Column Profile Component for AnalystGPT Enterprise.

Renders authoritative column semantic profiles, analytical roles,
cardinality, missingness, and governance recommendations.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.core.config import MAX_PROFILE_ROWS
from src.profiling.data_profiler import DataProfiler
from src.profiling.models import DatasetProfile


def render_column_profile(
    dataframe: pd.DataFrame,
    profile: DatasetProfile | None = None,
) -> None:
    """
    Render comprehensive semantic column profile table.
    """
    if dataframe.empty:
        st.info("No data available for profiling.")
        return

    # 1. Resolve Profile
    if profile is None:
        profiler = DataProfiler()
        profile = profiler.profile_dataset(dataframe)

    # 2. Semantic Distribution Summary Badges
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Columns", profile.column_count)
    with col2:
        measures_cnt = profile.role_counts.get("measure", 0) + profile.role_counts.get("demographic_measure", 0)
        st.metric("Measures", measures_cnt)
    with col3:
        dims_cnt = profile.role_counts.get("categorical_dimension", 0) + profile.role_counts.get("geographic_dimension", 0)
        st.metric("Dimensions", dims_cnt)
    with col4:
        id_cnt = profile.role_counts.get("identifier", 0) + profile.role_counts.get("contact_identifier", 0) + profile.role_counts.get("constant_attribute", 0)
        st.metric("Identifiers / Constants", id_cnt)

    # 3. Comprehensive Column Table
    profile_rows = []
    for col_name, cp in profile.column_profiles.items():
        profile_rows.append(
            {
                "Column": col_name,
                "Physical Type": cp.physical_dtype,
                "Semantic Type": cp.semantic_type.value,
                "Analytical Role": cp.analytical_role.value,
                "Missing": f"{cp.missing_count:,} ({cp.missing_percentage:.1f}%)",
                "Unique": f"{cp.unique_count:,} ({cp.uniqueness_percentage:.1f}%)",
                "Visualization": "Included" if cp.is_visualizable else "Excluded",
                "Recommendation": cp.governance_recommendation.replace("_", " ").title(),
            }
        )

    profile_table = pd.DataFrame(profile_rows)

    st.dataframe(
        profile_table,
        hide_index=True,
        width="stretch",
    )
