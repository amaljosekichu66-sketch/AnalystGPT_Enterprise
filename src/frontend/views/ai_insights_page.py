"""
AI Insights Page for AnalystGPT Enterprise.

Dedicated presentation view for AI-generated business insights,
executive summaries, recommendations, explanations, and narratives.

The job shown is the one of the run on screen (P2-06). While it is queued or
generating, a fragment refreshes only the status block every few seconds:
the page used to block the whole script with time.sleep(3) up to 40 times
(P2-08), and promised 30-90 s where CPU-only runs take 3-6 minutes.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
Sprint 14 Remediation — AI Insights + Enterprise Reporting Reliability Remediation.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.frontend.components.ai_insights import render_ai_insights
from src.frontend.components.empty_state import render_empty_state
from src.frontend.components.loading_state import loading
from src.frontend.components.safe_text import markdown_text
from src.frontend.components.scroll_to_top import scroll_to_top
from src.frontend.services.ai_service import cancel_ai_job, get_ai_job_status, retry_ai_job
from src.frontend.services.dashboard_service import get_dashboard_data
from src.frontend.services.session_manager import (
    clear_authenticated_session,
    get_ai_job_id,
    set_ai_report,
)

#: Seconds between status refreshes while a job is unfinished.
POLL_SECONDS = 10

IN_PROGRESS = {"PENDING", "GENERATING"}


def _job_actions(job: dict[str, Any]) -> None:
    job_id = job.get("job_id")
    if not job_id:
        return
    status = job.get("status")
    left, right, _ = st.columns([1, 1, 2])
    if status in IN_PROGRESS:
        with left:
            if st.button("⏹️ Cancel generation", key=f"cancel_{job_id}", width="stretch"):
                result = cancel_ai_job(job_id)
                (st.success if result["success"] else st.error)(result["message"])
    elif status in {"FAILED", "CANCELLED"}:
        with left:
            if st.button("🔄 Retry generation", key=f"retry_{job_id}", width="stretch"):
                result = retry_ai_job(job_id)
                if result["success"]:
                    st.success("Retry scheduled.")
                    st.rerun()
                else:
                    st.error(result["message"])
    with right:
        if st.button("🏠 Dashboard", key=f"dash_{job_id}", width="stretch"):
            st.session_state.current_page = "Dashboard"
            st.rerun()


@st.fragment(run_every=POLL_SECONDS)
def _poll_status(job_id: str) -> None:
    """Refresh only this block while the job runs; rerun the page once it finishes."""
    job = get_ai_job_status(job_id)
    status = job.get("status")
    if status not in IN_PROGRESS:
        st.rerun()
        return
    label = "Queued" if status == "PENDING" else "Generating insights"
    st.info(
        f"⏳ **{label}** — job `{markdown_text(job_id)}`, model "
        f"`{markdown_text(job.get('model', 'gemma3:4b'))}`, attempt {job.get('attempt_count', 0)} of "
        f"{job.get('max_attempts', 3)}.\n\n"
        "Analytics, quality checks and KPIs are complete. On CPU-only hardware the local model usually "
        f"needs 3–6 minutes. This status refreshes every {POLL_SECONDS} seconds; you can leave the page."
    )
    _job_actions(job)


def render() -> None:
    """
    Render the AI Insights page.
    """
    scroll_to_top()
    st.title("🧠 AI Business Insights")
    st.caption(
        "Executive summaries, strategic findings, and actionable recommendations "
        "synthesized from deterministic analytics by the AI Insight Engine."
    )

    with loading("Loading AI business insights..."):
        dashboard_data = get_dashboard_data()

    if not dashboard_data.get("dataset_loaded"):
        render_empty_state(
            title="No Dataset Available",
            message="Upload a dataset and run the analysis from the Upload page to generate AI insights.",
            icon="🧠",
            button_label="Go to Upload",
            target_page="Upload",
        )
        return

    if dashboard_data.get("api_error"):
        st.error(dashboard_data["api_error"])
        return

    st.success(f"Current dataset: **{markdown_text(dashboard_data.get('filename') or 'Active dataset')}**")

    job_id = dashboard_data.get("ai_job_id") or get_ai_job_id()
    if not dashboard_data.get("analysed") or not job_id:
        render_empty_state(
            title="AI Insights Not Generated Yet",
            message="Run the analysis from the Upload page; AI insights are generated for that run.",
            icon="🤖",
            button_label="Go to Upload",
            target_page="Upload",
        )
        return

    job = get_ai_job_status(job_id)
    status = job.get("status")

    if job.get("is_auth_error"):
        st.warning("🔒 Your session has expired. Please sign in again to see your AI insights.")
        if st.button("🔐 Sign in again"):
            clear_authenticated_session()
            st.session_state.current_page = "Sign In"
            st.rerun()
        return

    if status in IN_PROGRESS:
        _poll_status(job_id)
        return

    if status == "READY" and job.get("ai_report"):
        ai_report = job["ai_report"]
        set_ai_report(ai_report)
        st.divider()
        render_ai_insights(ai_report)
        st.divider()
        if st.button("📄 View full reports", width="stretch"):
            st.session_state.current_page = "Reports"
            st.rerun()
        return

    if status in {"FAILED", "CANCELLED"}:
        headline = "AI insight generation was cancelled." if status == "CANCELLED" else "AI insight generation failed."
        st.error(
            f"⚠️ **{headline}**\n\n{markdown_text(job.get('error') or '')}\n\n"
            "Your dataset analytics, charts and reports are unaffected."
        )
        _job_actions(job)
        return

    if job.get("error"):
        st.error(job["error"])
    else:
        st.warning("The AI job for this run could not be found. Run the analysis again from the Upload page.")
