"""
Upload Page for AnalystGPT Enterprise.

Upload a dataset, review its profile and charts, choose a cleaning policy
(proposal -> approval), preview its impact, and run the analysis.

Everything analytical happens behind the API (P2-05): the profile, chart plan
and policy recommendation come from GET /api/datasets/{id}/analysis, the
preview from POST /api/governance/preview, policies from
/api/governance/policies. This page is the only place that runs the pipeline,
and only when the user asks (P2-06).

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
Sprint 15 — policy approval workflow (P2-04).
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.frontend.components.charts import render_charts
from src.frontend.components.column_profile import render_column_profile
from src.frontend.components.dataset_info import render_dataset_info
from src.frontend.components.dataset_quality import render_dataset_quality
from src.frontend.components.safe_text import markdown_text
from src.frontend.components.scroll_to_top import scroll_to_top
from src.frontend.components.uploader import render_uploader
from src.frontend.services.api_client import APIClient
from src.frontend.services.errors import friendly_error
from src.frontend.services.session_manager import (
    ANALYSIS_KEY,
    get_current_user,
    get_dataset_version_id,
    get_pipeline_result,
    is_admin,
    store_dataset,
    store_pipeline_result,
)

#: The default policy runs without approval; every other one needs an approved proposal.
DEFAULT_POLICY = "DROP_ROWS"

POLICY_LABELS = {
    "DROP_ROWS": "Drop rows containing missing values (default, no approval needed)",
    "PRESERVE_NULLS": "Preserve missing values as NULL / NaN",
    "FILL_NUMERIC_MEDIAN": "Impute numeric nulls with the column median",
    "FILL_NUMERIC_MEAN": "Impute numeric nulls with the column mean",
    "FILL_CATEGORICAL_MODE": "Impute categorical nulls with the column mode",
}

_ACTIVE_DATASET_KEY = "_upload_page_dataset"


# ==========================================================
# Data access
# ==========================================================


def _analysis(dataset_version_id: str) -> dict[str, Any] | None:
    cached = st.session_state.get(ANALYSIS_KEY)
    if isinstance(cached, dict) and cached.get("dataset_version_id") == dataset_version_id:
        return cached
    try:
        with st.spinner("Profiling the dataset..."), APIClient() as client:
            analysis = client.dataset_analysis(dataset_version_id)
    except Exception as exc:
        st.error(friendly_error(exc, "dataset analysis"))
        return None
    st.session_state[ANALYSIS_KEY] = analysis
    return analysis


def _proposals(dataset_version_id: str) -> list[dict[str, Any]]:
    try:
        with APIClient() as client:
            return list(client.list_policies(dataset_version_id))
    except Exception as exc:
        st.warning(friendly_error(exc, "policy list"))
        return []


# ==========================================================
# Sections
# ==========================================================


def _render_governance(dataset_version_id: str, analysis: dict[str, Any]) -> None:
    profile = analysis.get("profile") or {}
    if not profile.get("has_missing_values"):
        st.info("✅ No missing values detected — the default policy is safe to run.")
        return

    with st.container(border=True):
        st.subheader("🛡️ Missing-Value Governance")
        missing_columns = [c for c in (profile.get("columns") or {}).values() if c.get("missing_count")]
        st.warning(
            f"Missing values detected: {profile.get('total_missing_cells', 0):,} cells across "
            f"{len(missing_columns)} column(s). Completeness: {profile.get('overall_completeness_pct', 100.0):.1f}%."
        )
        recommended = analysis.get("recommended_policy", DEFAULT_POLICY)
        st.info(
            f"💡 **Recommended policy**: `{markdown_text(recommended)}` — "
            f"{markdown_text(analysis.get('recommendation_reason', ''))}"
        )

        options = list(POLICY_LABELS)
        selected = st.selectbox(
            "Cleaning policy",
            options=options,
            index=options.index(recommended) if recommended in options else 0,
            format_func=lambda value: POLICY_LABELS[value],
            key=f"policy_select_{dataset_version_id}",
        )

        preview_col, propose_col = st.columns(2)
        with preview_col:
            if st.button("🔍 Preview cleaning impact", width="stretch"):
                _render_preview(dataset_version_id, selected)
        with propose_col:
            if selected != DEFAULT_POLICY and st.button("📨 Submit policy for approval", width="stretch"):
                try:
                    with APIClient() as client:
                        client.propose_policy(dataset_version_id, selected)
                    st.success("Policy submitted. It can run once it is approved.")
                except Exception as exc:
                    st.error(friendly_error(exc, "policy submission"))


def _render_preview(dataset_version_id: str, policy: str) -> None:
    try:
        with st.spinner("Generating a non-destructive preview..."), APIClient() as client:
            preview = client.governance_preview(dataset_version_id, policy)
    except Exception as exc:
        st.error(friendly_error(exc, "cleaning preview"))
        return
    cmp = preview.get("quality_comparison") or {}
    st.success("Preview generated (the source dataset is not modified).")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows removed", f"{cmp.get('rows_removed', 0):,}", f"{cmp.get('pct_rows_removed', 0.0):.1f}%")
    c2.metric("Missing values resolved", f"{cmp.get('missing_values_resolved', 0):,}")
    c3.metric(
        "Completeness",
        f"{cmp.get('source_completeness_pct', 0.0):.1f}% → {cmp.get('cleaned_completeness_pct', 0.0):.1f}%",
        f"+{cmp.get('completeness_gain', 0.0):.1f}%",
    )
    if cmp.get("has_material_loss"):
        st.warning("This policy removes a material share of the rows.")


def _render_proposals(proposals: list[dict[str, Any]]) -> None:
    if not proposals:
        return
    me = (get_current_user() or {}).get("id")
    st.markdown("**Policy proposals for this dataset**")
    for proposal in proposals:
        status = proposal.get("status")
        line = f"`{markdown_text(proposal.get('missing_value_policy'))}` — **{markdown_text(status)}**"
        if proposal.get("review_note"):
            line += f" — {markdown_text(proposal['review_note'])}"
        st.markdown(line)
        can_review = status == "PROPOSED" and (is_admin() or proposal.get("proposed_by") == me)
        if can_review:
            approve_col, reject_col, _ = st.columns([1, 1, 3])
            pid = proposal["proposal_id"]
            for column, approve, label in ((approve_col, True, "Approve"), (reject_col, False, "Reject")):
                with column:
                    if st.button(label, key=f"review_{label}_{pid}"):
                        try:
                            with APIClient() as client:
                                client.review_policy(pid, approve=approve)
                            st.session_state["_upload_flash"] = f"Policy {label.lower()}d."
                            st.rerun()
                        except Exception as exc:
                            st.error(friendly_error(exc, "policy review"))


def _render_run(dataset_version_id: str, proposals: list[dict[str, Any]]) -> None:
    st.subheader("▶️ Run analysis")
    approved = [p for p in proposals if p.get("status") == "APPROVED"]
    choices: dict[str, str | None] = {f"Default policy ({DEFAULT_POLICY})": None}
    for p in approved:
        choices[f"Approved: {p['missing_value_policy']} ({p['proposal_id'][:8]})"] = p["proposal_id"]
    choice = st.radio("Cleaning policy to apply", list(choices), key=f"run_choice_{dataset_version_id}")

    last = get_pipeline_result()
    if last and last.get("dataset_version_id") == dataset_version_id:
        st.caption(
            f"Last run: pipeline run {last.get('pipeline_run_id')}, report {last.get('report_id')}. "
            "Running again creates a new run."
        )

    if st.button("▶️ Run analysis", type="primary", width="stretch"):
        try:
            with st.spinner("Running the analytics pipeline..."), APIClient() as client:
                result = client.run_pipeline_for(dataset_version_id, choices[choice])
        except Exception as exc:
            st.error(friendly_error(exc, "pipeline run"))
            return
        if not result.get("success"):
            st.error(result.get("error") or "The pipeline did not complete. Please try again.")
            return
        store_pipeline_result(result)
        st.success(
            "Analysis complete. AI insights are being generated in the background; " "open AI Insights to follow them."
        )


# ==========================================================
# Page
# ==========================================================


def render() -> None:
    """
    Render the Upload and Governance page.
    """
    scroll_to_top()

    st.title("📁 Upload Dataset")
    st.write("Upload a CSV, Excel, or JSON dataset to profile it, choose a cleaning policy and run the analysis.")

    flash = st.session_state.pop("_upload_flash", None)
    if flash:
        st.success(flash)

    uploaded_file, dataframe = render_uploader()
    if dataframe is None:
        return

    dataset_version_id = get_dataset_version_id()
    if not dataset_version_id:
        return

    # Only a NEW dataset resets the session's dataset state; a rerun must not
    # wipe the analysis or the last run (P2-07).
    if st.session_state.get(_ACTIVE_DATASET_KEY) != dataset_version_id:
        store_dataset(uploaded_file=uploaded_file, dataframe=dataframe, dataset_version_id=dataset_version_id)
        st.session_state[_ACTIVE_DATASET_KEY] = dataset_version_id

    analysis = _analysis(dataset_version_id)

    st.divider()
    if analysis is not None:
        _render_governance(dataset_version_id, analysis)
        proposals = _proposals(dataset_version_id)
        _render_proposals(proposals)
        st.divider()
        _render_run(dataset_version_id, proposals)

    st.divider()
    col_info, col_qual = st.columns(2)
    with col_info:
        with st.expander("📊 Dataset Information", expanded=True):
            render_dataset_info(uploaded_file, dataframe)
    with col_qual:
        with st.expander("✅ Data Quality Overview", expanded=True):
            render_dataset_quality(dataframe)

    if analysis is not None:
        with st.expander("📈 Visual Analytics", expanded=True):
            render_charts(analysis.get("visualization_plan"))
        with st.expander("📋 Semantic Column Profile", expanded=False):
            render_column_profile(analysis.get("profile"))

    st.subheader("🔍 Dataset Preview")
    st.dataframe(dataframe.head(20), width="stretch")
