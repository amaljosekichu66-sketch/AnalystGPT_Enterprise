"""
AI Insights Page for AnalystGPT Enterprise.

Dedicated presentation view for AI-generated business insights,
executive summaries, recommendations, explanations, and narratives.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
Sprint 14 Remediation — AI Insights + Enterprise Reporting Reliability Remediation.
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.ai_insights import render_ai_insights
from src.frontend.components.empty_state import render_empty_state
from src.frontend.components.loading_state import loading
from src.frontend.components.scroll_to_top import scroll_to_top
from src.frontend.services.ai_service import get_ai_job_status, retry_ai_job
from src.frontend.services.dashboard_service import get_dashboard_data
from src.frontend.services.session_manager import (
    clear_authenticated_session,
    get_ai_job_id,
    get_ai_report,
    set_ai_report,
)


def render() -> None:
    """
    Render the dedicated AI Insights page with complete lifecycle state awareness:
    IDLE -> QUEUED -> GENERATING -> READY / FAILED / STALE
    """
    scroll_to_top()

    st.title("🧠 AI Business Insights")

    st.caption(
        "Executive summaries, strategic findings, and actionable recommendations "
        "synthesized from deterministic analytics by the AI Insight Engine."
    )

    with loading("Loading AI business insights..."):
        dashboard_data = get_dashboard_data()

    # ==========================================================
    # State 1: IDLE / No Dataset Available
    # ==========================================================
    if not dashboard_data.get("dataset_loaded"):
        render_empty_state(
            title="No Dataset Available",
            message=(
                "Upload a CSV, Excel or JSON dataset from the Upload page "
                "to execute the analytics pipeline and generate AI insights."
            ),
            icon="🧠",
            button_label="Go to Upload",
            target_page="Upload",
        )
        return

    # Dataset Banner
    st.success(f"Current Dataset: **{dashboard_data.get('filename') or 'Active Dataset'}**")

    # ==========================================================
    # State Resolution: Resolve AI Report & Job Lifecycle State
    # ==========================================================
    ai_report = get_ai_report() or dashboard_data.get("ai_report")

    if not ai_report:
        active_job_id = get_ai_job_id()
        job_data = get_ai_job_status(active_job_id)
        job_status = job_data.get("status", "NOT_FOUND")

        # State 2: UNAUTHORIZED / Auth Token Expired
        if job_status == "UNAUTHORIZED" or job_data.get("is_auth_error"):
            st.session_state._ai_poll_count = 0
            st.warning(
                "🔒 **Authentication Session Expired**\n\n"
                "Your authentication session token has expired. "
                "Please sign in again to retrieve your AI insights and pipeline reports."
            )
            col_auth, _ = st.columns([1, 2])
            with col_auth:
                if st.button("🔐 Sign In Again", width="stretch"):
                    clear_authenticated_session()
                    st.session_state.current_page = "Sign In"
                    st.rerun()
            return

        # State 3 & 4: PENDING / GENERATING
        if job_status in {"PENDING", "GENERATING"}:
            poll_count = st.session_state.get("_ai_poll_count", 0) + 1
            st.session_state._ai_poll_count = poll_count

            status_label = "Queued in Background" if job_status == "PENDING" else "Synthesizing Insights"
            st.info(
                f"⏳ **AI Insight Generation in Progress — {status_label} ({job_status})**\n\n"
                f"• **Provider / Model:** `{job_data.get('provider', 'ollama')}` / `{job_data.get('model', 'gemma3:4b')}`\n\n"
                f"• **Job ID:** `{job_data.get('job_id', active_job_id or 'Pending')}`\n\n"
                f"Deterministic analytics, quality checks, and KPIs are complete. "
                f"Local LLM synthesis executes asynchronously (typically 30–90s). The page will refresh automatically."
            )

            col_a, col_b = st.columns([1, 2])
            with col_a:
                if st.button("🔄 Refresh Status Now", width="stretch"):
                    st.session_state._ai_poll_count = 0
                    st.rerun()
            with col_b:
                if st.button("🏠 Explore Dashboard while AI synthesizes", width="stretch"):
                    st.session_state.current_page = "Dashboard"
                    st.rerun()

            # Auto-poll up to 40 times (~120s max automated polling)
            if poll_count < 40:
                import time

                time.sleep(3)
                st.rerun()
            else:
                st.warning(
                    "Automatic polling paused to preserve resources. Click 'Refresh Status Now' to check completion."
                )
            return

        # Reset poll counter on exit from in-progress
        st.session_state._ai_poll_count = 0

        # State 5: FAILED
        if job_status == "FAILED":
            st.error(
                f"⚠️ **AI Insight Generation Unsuccessful**\n\n"
                f"The AI Insight Engine was unable to complete generation.\n\n"
                f"• **Job ID:** `{job_data.get('job_id', 'N/A')}`\n\n"
                f"• **Provider / Model:** `{job_data.get('provider')}` / `{job_data.get('model')}`\n\n"
                f"• **Failure Category:** `{job_data.get('failure_category') or 'UNKNOWN'}`\n\n"
                f"• **Reason:** `{job_data.get('error') or 'Inference timed out or service unavailable'}`\n\n"
                f"Your core dataset analytics, visual charts, and reports remain fully intact."
            )
            col_retry, _ = st.columns([1, 2])
            with col_retry:
                job_id = job_data.get("job_id")
                if job_id and st.button("🔄 Retry Generation", width="stretch"):
                    retry_result = retry_ai_job(job_id)
                    if retry_result.get("success"):
                        st.success("Retry scheduled successfully.")
                        st.session_state._ai_poll_count = 0
                        st.rerun()
                    else:
                        st.error(retry_result.get("message", "Failed to schedule retry."))
            return

        # State 6: READY
        elif job_status == "READY" and job_data.get("ai_report"):
            ai_report = job_data["ai_report"]
            if isinstance(ai_report, dict) and job_data.get("job_id"):
                ai_report["job_id"] = job_data["job_id"]
            set_ai_report(ai_report)
            dashboard_data["ai_report"] = ai_report
            st.session_state._ai_poll_count = 0

        # State 7: READY but missing report payload
        elif job_status == "READY" and not job_data.get("ai_report"):
            st.warning(
                f"⚠️ AI Job `{job_data.get('job_id')}` completed with status READY, "
                "but the structured report payload could not be loaded. Please refresh or retry."
            )
            if st.button("🔄 Reload Report"):
                st.rerun()
            return

        # State 8: STALE / UNKNOWN / NOT_FOUND
        else:
            render_empty_state(
                title="AI Insights Not Generated Yet",
                message=(
                    "AI insights have not been generated for the active dataset. "
                    "Ensure the backend analytics pipeline has completed with AI enrichment."
                ),
                icon="🤖",
                button_label="Go to Dashboard",
                target_page="Dashboard",
            )
            return

    # Ensure session state and poll count are cleanly synchronized
    st.session_state._ai_poll_count = 0
    if ai_report and not get_ai_report():
        set_ai_report(ai_report)

    st.divider()

    # ==========================================================
    # Render AI Insights Component (READY State)
    # ==========================================================
    render_ai_insights(ai_report)

    st.divider()

    # ==========================================================
    # Contextual Navigation
    # ==========================================================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🏠 Return to Dashboard", width="stretch"):
            st.session_state.current_page = "Dashboard"
            st.rerun()

    with col2:
        if st.button("📄 View Full Reports", width="stretch"):
            st.session_state.current_page = "Reports"
            st.rerun()
