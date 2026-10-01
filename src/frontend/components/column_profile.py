"""
Column Profile Component for AnalystGPT Enterprise.

Renders column semantic profiles, analytical roles, cardinality,
missingness, and governance recommendations from the profile the API
returns (GET /api/datasets/{id}/analysis). The profiler used to run inside
the Streamlit process (P2-05).

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_column_profile(profile: dict[str, Any] | None) -> None:
    """
    Render the semantic column profile table.
    """
    if not profile or not profile.get("columns"):
        st.info("No data available for profiling.")
        return

    roles = profile.get("role_counts") or {}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Columns", profile.get("column_count", len(profile["columns"])))
    with col2:
        st.metric("Measures", roles.get("measure", 0) + roles.get("demographic_measure", 0))
    with col3:
        st.metric("Dimensions", roles.get("categorical_dimension", 0) + roles.get("geographic_dimension", 0))
    with col4:
        st.metric(
            "Identifiers / Constants",
            roles.get("identifier", 0) + roles.get("contact_identifier", 0) + roles.get("constant_attribute", 0),
        )

    rows = []
    for col_name, cp in profile["columns"].items():
        rows.append(
            {
                "Column": col_name,
                "Physical Type": cp.get("physical_dtype"),
                "Semantic Type": cp.get("semantic_type"),
                "Analytical Role": cp.get("analytical_role"),
                "Missing": f"{cp.get('missing_count', 0):,} ({cp.get('missing_percentage', 0.0):.1f}%)",
                "Unique": f"{cp.get('unique_count', 0):,} ({cp.get('uniqueness_percentage', 0.0):.1f}%)",
                "Visualization": "Included" if cp.get("is_visualizable") else "Excluded",
                "Recommendation": str(cp.get("governance_recommendation", "")).replace("_", " ").title(),
            }
        )

    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
