"""
Frontend AI Insights Hydration, Lifecycle & Auth Expiry Regression Tests.

Sprint 14 Remediation — AI Insights Runtime Failure Remediation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from src.frontend.services.ai_service import get_ai_job_status
from src.frontend.services.dashboard_service import (
    _cache_dashboard,
    _get_cached_dashboard,
    get_dashboard_data,
)
from src.frontend.services.session_manager import (
    AI_JOB_ID_KEY,
    AI_REPORT_KEY,
    get_ai_job_id,
    get_ai_report,
    set_ai_job_id,
    set_ai_report,
)
from src.frontend.views import ai_insights_page


@pytest.fixture(autouse=True)
def clean_session_state():
    """Ensure clean Streamlit session state between tests."""
    st.session_state.clear()
    yield
    st.session_state.clear()


# ==============================================================================
# 1 & 2. PENDING and GENERATING Jobs
# ==============================================================================

def test_pending_and_generating_job_lifecycle():
    for status_name in ["PENDING", "GENERATING"]:
        st.session_state.clear()
        mock_data = {
            "job_id": f"ai_job_{status_name.lower()}_111",
            "status": status_name,
            "provider": "ollama",
            "model": "gemma3:4b",
            "ai_report": None,
        }

        with patch("src.frontend.services.ai_service.APIClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_ai_job.return_value = mock_data
            mock_client_cls.return_value = mock_client

            res = get_ai_job_status(f"ai_job_{status_name.lower()}_111")
            assert res["status"] == status_name
            assert res["ai_report"] is None
            assert res["is_auth_error"] is False

        # Page view test
        dashboard_data = {
            "dataset_loaded": True,
            "filename": "test.csv",
            "ai_report": None,
        }
        with patch("src.frontend.views.ai_insights_page.get_dashboard_data", return_value=dashboard_data):
            with patch("src.frontend.views.ai_insights_page.get_ai_job_id", return_value=f"ai_job_{status_name.lower()}_111"):
                with patch("src.frontend.views.ai_insights_page.get_ai_job_status", return_value=res):
                    with patch("time.sleep"):
                        with patch("streamlit.rerun") as mock_rerun:
                            ai_insights_page.render()
                            assert mock_rerun.called
                            assert st.session_state.get("_ai_poll_count") == 1


# ==============================================================================
# 3 & 4. READY Job with AIReport & Session State Hydration
# ==============================================================================

def test_ready_job_with_report_hydrates_session_state():
    mock_data = {
        "job_id": "ai_job_ready_999",
        "status": "READY",
        "provider": "ollama",
        "model": "gemma3:4b",
        "ai_report": {
            "executive_summary": "Executive summary test.",
            "key_findings": ["Finding 1"],
            "business_implications": ["Implication 1"],
            "risks": ["Risk 1"],
            "opportunities": ["Opportunity 1"],
            "actions": ["Action 1"],
            "confidence": "High — Grounded in analytics",
        },
    }

    with patch("src.frontend.services.ai_service.APIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.get_ai_job.return_value = mock_data
        mock_client_cls.return_value = mock_client

        res = get_ai_job_status("ai_job_ready_999")

        assert res["success"] is True
        assert res["status"] == "READY"
        assert res["job_id"] == "ai_job_ready_999"
        assert res["ai_report"] is not None
        assert res["ai_report"]["executive_summary"] == "Executive summary test."
        # Verify hydrated into session state
        assert get_ai_report() is not None
        assert get_ai_report()["executive_summary"] == "Executive summary test."
        assert get_ai_job_id() == "ai_job_ready_999"


# ==============================================================================
# 5. READY Hydration when Dashboard Data has ai_report=None
# ==============================================================================

def test_ready_hydration_when_dashboard_data_has_no_report():
    dashboard_data = {
        "dataset_loaded": True,
        "filename": "test.csv",
        "ai_report": None,
    }

    job_data = {
        "job_id": "ai_job_ready_777",
        "status": "READY",
        "ai_report": {
            "executive_summary": "Hydrated summary.",
            "key_findings": ["Finding 1"],
            "actions": ["Action 1"],
            "confidence": "High — Grounded in governed measures.",
        },
    }

    with patch("src.frontend.views.ai_insights_page.get_dashboard_data", return_value=dashboard_data):
        with patch("src.frontend.views.ai_insights_page.get_ai_job_id", return_value="ai_job_ready_777"):
            with patch("src.frontend.views.ai_insights_page.get_ai_job_status", return_value=job_data):
                with patch("src.frontend.views.ai_insights_page.render_ai_insights") as mock_render_insights:
                    ai_insights_page.render()
                    assert mock_render_insights.called
                    assert dashboard_data["ai_report"] is not None
                    assert get_ai_report() is not None
                    assert get_ai_report()["executive_summary"] == "Hydrated summary."
                    assert st.session_state.get("_ai_poll_count") == 0


# ==============================================================================
# 6. FAILED Job Handling
# ==============================================================================

def test_failed_job_stops_polling_and_renders_diagnostics():
    dashboard_data = {
        "dataset_loaded": True,
        "filename": "test.csv",
        "ai_report": None,
    }

    job_data = {
        "job_id": "ai_job_failed_555",
        "status": "FAILED",
        "provider": "ollama",
        "model": "gemma3:4b",
        "failure_category": "TIMEOUT",
        "error": "Ollama service read timeout after 180s.",
        "ai_report": None,
    }

    with patch("src.frontend.views.ai_insights_page.get_dashboard_data", return_value=dashboard_data):
        with patch("src.frontend.views.ai_insights_page.get_ai_job_id", return_value="ai_job_failed_555"):
            with patch("src.frontend.views.ai_insights_page.get_ai_job_status", return_value=job_data):
                with patch("streamlit.error") as mock_st_error:
                    with patch("streamlit.rerun") as mock_rerun:
                        ai_insights_page.render()
                        assert mock_st_error.called
                        assert not mock_rerun.called
                        assert st.session_state.get("_ai_poll_count") == 0


# ==============================================================================
# 7. HTTP 401 Authentication-Expired Response
# ==============================================================================

def test_http_401_auth_expired_shows_session_expired():
    with patch("src.frontend.services.ai_service.APIClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.get_ai_job.side_effect = RuntimeError("Backend returned HTTP 401: Authentication token has expired.")
        mock_client_cls.return_value = mock_client

        res = get_ai_job_status("ai_job_expired_001")
        assert res["status"] == "UNAUTHORIZED"
        assert res["is_auth_error"] is True

    dashboard_data = {
        "dataset_loaded": True,
        "filename": "test.csv",
        "ai_report": None,
    }

    with patch("src.frontend.views.ai_insights_page.get_dashboard_data", return_value=dashboard_data):
        with patch("src.frontend.views.ai_insights_page.get_ai_job_id", return_value="ai_job_expired_001"):
            with patch("src.frontend.views.ai_insights_page.get_ai_job_status", return_value=res):
                with patch("streamlit.warning") as mock_warning:
                    with patch("src.frontend.views.ai_insights_page.render_empty_state") as mock_empty:
                        ai_insights_page.render()
                        assert mock_warning.called
                        # Verify it did NOT call generic empty state
                        assert not mock_empty.called


# ==============================================================================
# 8. Stale Dashboard Cache Must NOT Overwrite READY AI Report
# ==============================================================================

def test_stale_dashboard_cache_does_not_overwrite_ready_report():
    dataset_path = "/tmp/test_dataset.csv"
    ready_report = {
        "executive_summary": "Authoritative READY Report.",
        "key_findings": ["F1"],
    }
    set_ai_report(ready_report)

    stale_dashboard = {
        "dataset_loaded": True,
        "filename": "test_dataset.csv",
        "ai_report": None,
    }
    _cache_dashboard(dataset_path, stale_dashboard)

    with patch("src.frontend.services.dashboard_service.get_dataset_path", return_value=dataset_path):
        data = get_dashboard_data()
        assert data["ai_report"] is not None
        assert data["ai_report"]["executive_summary"] == "Authoritative READY Report."


# ==============================================================================
# 9 & 10. Navigation Away/Back & Streamlit Rerun Preserves READY Report
# ==============================================================================

def test_navigation_and_rerun_preserves_ready_report():
    ready_report = {
        "executive_summary": "Persistent Summary Across Nav & Reruns.",
        "key_findings": ["Finding"],
    }
    set_ai_report(ready_report)

    # 1. First render on AI Insights page
    dashboard_data = {
        "dataset_loaded": True,
        "filename": "data.csv",
        "ai_report": None,  # Simulated unhydrated dashboard
    }
    with patch("src.frontend.views.ai_insights_page.get_dashboard_data", return_value=dashboard_data):
        with patch("src.frontend.views.ai_insights_page.render_ai_insights") as mock_render:
            ai_insights_page.render()
            assert mock_render.called
            assert mock_render.call_args[0][0]["executive_summary"] == "Persistent Summary Across Nav & Reruns."

    # 2. Simulate navigating away to Dashboard
    st.session_state.current_page = "Dashboard"
    assert get_ai_report() == ready_report

    # 3. Simulate navigating back to AI Insights and rerunning
    st.session_state.current_page = "AI Insights"
    with patch("src.frontend.views.ai_insights_page.get_dashboard_data", return_value=dashboard_data):
        with patch("src.frontend.views.ai_insights_page.render_ai_insights") as mock_render:
            ai_insights_page.render()
            assert mock_render.called
            assert mock_render.call_args[0][0]["executive_summary"] == "Persistent Summary Across Nav & Reruns."
