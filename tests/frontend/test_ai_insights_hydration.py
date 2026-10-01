"""
Frontend AI Insights lifecycle tests.

Sprint 14 Remediation, updated for the Sprint 15 readiness gate:
- P2-06: the job shown is the one of the run on screen; there is no fallback
  to the user's latest job (which may belong to another dataset).
- P2-08: no blocking time.sleep polling; a fragment refreshes the status.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from src.frontend.services.ai_service import get_ai_job_status
from src.frontend.services.session_manager import AI_REPORT_KEY, get_ai_report
from src.frontend.views import ai_insights_page

ANALYSED = {"dataset_loaded": True, "analysed": True, "filename": "d.csv", "ai_job_id": "job_1"}


@pytest.fixture(autouse=True)
def clean_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def _render(job: dict, dashboard: dict | None = None):
    with (
        patch.object(ai_insights_page, "get_dashboard_data", return_value=dashboard or ANALYSED),
        patch.object(ai_insights_page, "get_ai_job_status", return_value=job),
        patch.object(ai_insights_page, "_poll_status") as poll,
        patch.object(ai_insights_page, "render_ai_insights") as insights,
        patch.object(ai_insights_page, "render_empty_state") as empty,
        patch("time.sleep", side_effect=AssertionError("blocking sleep")),
    ):
        ai_insights_page.render()
    return poll, insights, empty


def test_status_without_a_job_id_does_not_fall_back_to_the_latest_job() -> None:
    with patch("src.frontend.services.ai_service.APIClient") as client_cls:
        result = get_ai_job_status(None)
    assert result["status"] == "NOT_FOUND"
    client_cls.assert_not_called()


@pytest.mark.parametrize("status", ["PENDING", "GENERATING"])
def test_unfinished_job_is_polled_without_blocking(status: str) -> None:
    poll, insights, _ = _render({"job_id": "job_1", "status": status})
    poll.assert_called_once_with("job_1")
    insights.assert_not_called()


def test_ready_job_renders_and_hydrates_the_session() -> None:
    report = {"executive_summary": "ok"}
    _, insights, _ = _render({"job_id": "job_1", "status": "READY", "ai_report": report})
    insights.assert_called_once_with(report)
    assert get_ai_report() == report


def test_failed_job_shows_diagnostics_and_offers_retry() -> None:
    with patch.object(ai_insights_page.st, "error") as error, patch.object(ai_insights_page, "_job_actions") as actions:
        _render({"job_id": "job_1", "status": "FAILED", "error": "The AI provider is unavailable."})
    assert "The AI provider is unavailable." in error.call_args[0][0]
    actions.assert_called_once()


def test_auth_expiry_asks_to_sign_in_again() -> None:
    with patch.object(ai_insights_page.st, "warning") as warning:
        _render({"job_id": "job_1", "status": "UNAUTHORIZED", "is_auth_error": True})
    assert "expired" in warning.call_args[0][0]


def test_not_analysed_dataset_points_to_the_upload_page() -> None:
    _, _, empty = _render({"status": "NOT_FOUND"}, dashboard={**ANALYSED, "analysed": False, "ai_job_id": None})
    assert empty.call_args.kwargs["target_page"] == "Upload"


def test_ready_report_payload_is_stored_once_fetched() -> None:
    with patch("src.frontend.services.ai_service.APIClient") as client_cls:
        client = MagicMock()
        client.get_ai_job.return_value = {"job_id": "job_9", "status": "READY", "ai_report": {"executive_summary": "x"}}
        client_cls.return_value = client
        result = get_ai_job_status("job_9")
    assert result["status"] == "READY"
    assert st.session_state[AI_REPORT_KEY] == {"executive_summary": "x"}
