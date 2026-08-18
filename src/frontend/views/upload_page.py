"""
Upload Page for AnalystGPT Enterprise.

Provides dataset upload, semantic profiling, missing-value governance workflow,
cleaning impact preview, visual analytics, and schema exploration.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.frontend.components.charts import render_charts
from src.frontend.components.column_profile import render_column_profile
from src.frontend.components.dataset_info import render_dataset_info
from src.frontend.components.dataset_quality import render_dataset_quality
from src.frontend.components.scroll_to_top import scroll_to_top
from src.frontend.components.uploader import render_uploader
from src.frontend.services.session_manager import (
    clear_dataset,
    get_dataset_path,
    store_dataset,
)
from src.governance.governance_service import CleaningGovernanceService
from src.governance.models import CleaningConfig, MissingValuePolicy
from src.governance.preview_service import CleaningPreviewService
from src.profiling.data_profiler import DataProfiler


def render() -> None:
    """
    Render the Upload and Governance page.
    """
    scroll_to_top()

    st.title("📁 Upload Dataset")
    st.write("Upload a CSV, Excel, or JSON dataset to profile schema, configure governance, and begin analytics.")

    uploaded_file, dataframe = render_uploader()

    if dataframe is None:
        return

    # Preserve dataset in session
    dataset_path = get_dataset_path()
    clear_dataset()
    store_dataset(
        uploaded_file=uploaded_file,
        dataframe=dataframe,
        dataset_path=dataset_path,
    )

    # 1. Authoritative Semantic Profiling
    profiler = DataProfiler()
    profile = profiler.profile_dataset(dataframe)

    # 2. Missing-Value Governance Workflow
    if profile.has_missing_values:
        st.divider()
        with st.container(border=True):
            st.subheader("🛡️ Missing-Value Governance")
            st.warning(
                f"Missing values detected: {profile.total_missing_cells:,} cells across "
                f"{len(profile.get_columns_with_missing())} column(s). Completeness: {profile.overall_completeness_pct:.1f}%."
            )

            gov_service = CleaningGovernanceService()
            rec_policy, rec_reason = gov_service.recommend_dataset_policy(profile)

            st.info(f"💡 **Recommended Policy**: `{rec_policy.value}` — {rec_reason}")

            # Policy Selector
            policy_options = {
                "Drop rows containing missing values (Default)": MissingValuePolicy.DROP_ROWS,
                "Preserve missing values as NULL / NaN": MissingValuePolicy.PRESERVE_NULLS,
                "Impute numeric nulls with column Median": MissingValuePolicy.FILL_NUMERIC_MEDIAN,
                "Impute numeric nulls with column Mean": MissingValuePolicy.FILL_NUMERIC_MEAN,
                "Impute categorical nulls with column Mode": MissingValuePolicy.FILL_CATEGORICAL_MODE,
                "Custom governance policy": MissingValuePolicy.CUSTOM_POLICY,
            }

            default_idx = 0
            if rec_policy == MissingValuePolicy.PRESERVE_NULLS:
                default_idx = 1
            elif rec_policy == MissingValuePolicy.FILL_NUMERIC_MEDIAN:
                default_idx = 2
            elif rec_policy == MissingValuePolicy.FILL_CATEGORICAL_MODE:
                default_idx = 4

            selected_label = st.selectbox(
                "Select Cleaning Policy for Pipeline Execution",
                options=list(policy_options.keys()),
                index=default_idx,
                help="The selected policy will be executed during pipeline processing while keeping the raw dataset immutable.",
            )
            selected_policy = policy_options[selected_label]
            st.session_state.selected_cleaning_policy = selected_policy.value

            # Preview Button
            if st.button("🔍 Preview Cleaning Impact", use_container_width=False):
                with st.spinner("Generating non-destructive preview..."):
                    preview_service = CleaningPreviewService()
                    cfg = CleaningConfig(
                        config_id="preview-config",
                        missing_value_policy=selected_policy,
                    )
                    preview_res = preview_service.preview(dataframe, cfg)

                st.success("Preview generated successfully (source dataset remains unmodified).")
                cmp = preview_res.quality_comparison

                pcol1, pcol2, pcol3 = st.columns(3)
                with pcol1:
                    st.metric("Rows", f"{cmp.source.row_count:,} → {cmp.cleaned.row_count:,}", f"-{cmp.rows_removed:,}")
                with pcol2:
                    st.metric("Missing Cells", f"{cmp.source.total_missing:,} → {cmp.cleaned.total_missing:,}", f"-{cmp.source.total_missing - cmp.cleaned.total_missing:,}")
                with pcol3:
                    delta_comp = cmp.cleaned.completeness_percentage - cmp.source.completeness_percentage
                    st.metric(
                        "Completeness",
                        f"{cmp.source.completeness_percentage:.1f}% → {cmp.cleaned.completeness_percentage:.1f}%",
                        f"+{delta_comp:.1f}%",
                    )
    else:
        st.divider()
        st.info("✅ No missing values detected — no missing-value policy is required.")
        st.session_state.selected_cleaning_policy = MissingValuePolicy.PRESERVE_NULLS.value

    st.divider()

    # 3. Dataset Information & Quality
    col_info, col_qual = st.columns(2)
    with col_info:
        with st.expander("📊 Dataset Information", expanded=True):
            render_dataset_info(uploaded_file, dataframe)
    with col_qual:
        with st.expander("✅ Data Quality Overview", expanded=True):
            render_dataset_quality(dataframe)

    # 4. Visual Analytics (2x2 / 3x3 Responsive Grid)
    with st.expander("📈 Visual Analytics", expanded=True):
        render_charts(dataframe, profile=profile)

    # 5. Semantic Column Profile
    with st.expander("📋 Semantic Column Profile", expanded=True):
        render_column_profile(dataframe, profile=profile)

    # 6. Dataset Preview
    st.subheader("🔍 Dataset Preview")
    st.dataframe(dataframe.head(20), width="stretch")

    # 7. Session Confirmation
    st.divider()
    st.success(f"✅ Dataset `{uploaded_file.name if hasattr(uploaded_file, 'name') else 'dataset'}` loaded ({len(dataframe):,} rows, {len(dataframe.columns)} columns). Ready for enterprise pipeline.")
