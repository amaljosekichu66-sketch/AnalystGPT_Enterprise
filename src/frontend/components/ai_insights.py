"""
AI Insights Component for AnalystGPT Enterprise.

Displays structured, evidence-grounded AI-generated business insights,
executive summaries, strategic implications, risks, and recommendations.

Sprint 14 Remediation — AI Insights + Enterprise Reporting Reliability Remediation.
"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st


def _extract_ai_report(data: Any) -> dict[str, Any] | None:
    """
    Safely extract and normalize AI report dictionary from various payload formats.
    """
    if data is None:
        return None

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return None

    if hasattr(data, "to_dict"):
        data = data.to_dict()

    if not isinstance(data, dict):
        return None

    if data.get("ai_report"):
        inner = data["ai_report"]
        return inner.to_dict() if hasattr(inner, "to_dict") else inner

    if data.get("report") and isinstance(data["report"], dict):
        if data["report"].get("ai_report"):
            return data["report"]["ai_report"]
        if data["report"].get("ai"):
            return data["report"]["ai"]

    return data


def render_ai_insights(data: Any) -> None:
    """
    Render comprehensive structured enterprise AI business insights.
    """
    ai_report = _extract_ai_report(data)

    if not ai_report:
        st.info("AI insights have not been generated yet.")
        return

    # ==========================================================
    # 1. Executive Summary / Interpretation
    # ==========================================================
    summary = ai_report.get("executive_summary")
    if summary:
        st.subheader("📋 Executive Interpretation")
        st.markdown(
            f"""
            <div style="background-color: rgba(28, 131, 225, 0.08); border-left: 4px solid #1c83e1; padding: 14px 18px; border-radius: 4px; margin-bottom: 18px;">
                <p style="margin: 0; font-size: 1.05rem; line-height: 1.6;">{summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================================
    # 2. Key Findings & Business Implications
    # ==========================================================
    col_find, col_impl = st.columns(2)

    with col_find:
        st.subheader("🔍 Key Analytical Findings")
        findings = ai_report.get("key_findings") or ai_report.get("explanations", [])
        if findings:
            for item in findings:
                st.markdown(f"• **Finding:** {item}")
        else:
            st.caption("No specific findings recorded.")

    with col_impl:
        st.subheader("💼 Business Implications")
        implications = ai_report.get("business_implications") or ai_report.get("explanations", [])[:2]
        if implications:
            for item in implications:
                st.markdown(f"• **Impact:** {item}")
        else:
            st.caption("No strategic implications recorded.")

    st.divider()

    # ==========================================================
    # 3. Risks vs Opportunities
    # ==========================================================
    col_risk, col_opp = st.columns(2)

    with col_risk:
        st.subheader("⚠️ Risks & Data Concerns")
        risks = ai_report.get("risks")
        if risks:
            for r in risks:
                st.markdown(
                    f"""
                    <div style="background-color: rgba(255, 75, 75, 0.08); border-left: 3px solid #ff4b4b; padding: 10px 14px; border-radius: 4px; margin-bottom: 8px;">
                        <span style="font-size: 0.95rem;">{r}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No critical risks identified from current analytical findings.")

    with col_opp:
        st.subheader("🚀 Strategic Opportunities")
        opportunities = ai_report.get("opportunities")
        if opportunities:
            for o in opportunities:
                st.markdown(
                    f"""
                    <div style="background-color: rgba(9, 171, 59, 0.08); border-left: 3px solid #09ab3b; padding: 10px 14px; border-radius: 4px; margin-bottom: 8px;">
                        <span style="font-size: 0.95rem;">{o}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Target core segments to capitalize on stable dimension distributions.")

    st.divider()

    # ==========================================================
    # 4. Recommended Actions
    # ==========================================================
    st.subheader("🎯 Prioritized Recommended Actions")
    actions = ai_report.get("actions") or ai_report.get("recommendations", [])
    if actions:
        for idx, act in enumerate(actions, start=1):
            st.markdown(f"**{idx}.** {act}")
    else:
        st.caption("No prioritized recommendations available.")

    # ==========================================================
    # 5. Business Narrative
    # ==========================================================
    narrative = ai_report.get("narrative")
    if narrative:
        st.divider()
        with st.expander("📖 Complete Strategic Narrative", expanded=False):
            st.write(narrative)

    # ==========================================================
    # 6. Confidence, Limitations & Evidence
    # ==========================================================
    st.divider()
    col_conf, col_lim = st.columns([1, 2])

    with col_conf:
        st.caption("ANALYSIS CONFIDENCE")
        confidence = ai_report.get("confidence", "High (Grounded in Deterministic Analytics)")
        st.success(f"🛡️ **{confidence}**")

    with col_lim:
        st.caption("DATA LIMITATIONS & CAVEATS")
        limitations = ai_report.get("limitations") or [
            "AI interpretations reflect observational analytics and must be evaluated in business context.",
            "Causal relationships cannot be established solely from non-experimental records.",
        ]
        for lim in limitations:
            st.markdown(f"• *{lim}*")

    # ==========================================================
    # 7. Engine Metadata
    # ==========================================================
    st.divider()
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)

    with mcol1:
        st.metric("Model", ai_report.get("model", "-"))
    with mcol2:
        st.metric("Provider", ai_report.get("provider", "-"))
    with mcol3:
        exec_time = ai_report.get("execution_time")
        st.metric("Inference Time", f"{float(exec_time):.2f} s" if exec_time is not None else "-")
    with mcol4:
        job_id = ai_report.get("job_id") or "Synchronized"
        st.metric("AI Job", str(job_id)[:14])
