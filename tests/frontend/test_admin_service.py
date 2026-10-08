"""
Unit tests for Frontend Admin Service.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

from unittest.mock import MagicMock, patch

from src.frontend.services.admin_service import AdminService


def test_admin_list_users():
    mock_client = MagicMock()
    mock_client._request.return_value = {"items": [{"id": 1, "username": "admin"}], "total": 1}

    service = AdminService(api_client=mock_client)
    success, data, err = service.list_users(limit=50, offset=0)

    assert success is True
    assert data["total"] == 1
    assert err is None


def test_admin_update_user():
    mock_client = MagicMock()
    mock_client._request.return_value = {"id": 2, "role": "ADMIN"}

    service = AdminService(api_client=mock_client)
    success, data, err = service.update_user(user_id=2, role="ADMIN")

    assert success is True
    assert data["role"] == "ADMIN"
    assert err is None


def test_admin_delete_user():
    mock_client = MagicMock()
    mock_client._request.return_value = {"success": True}

    service = AdminService(api_client=mock_client)
    success, data, err = service.delete_user(user_id=2)

    assert success is True
    assert err is None


def test_audit_events_and_unlock_delegate_to_the_api():
    """P2-25: the admin UI covers the audit log and lockout clearing."""
    mock_client = MagicMock()
    mock_client.admin_audit_events.return_value = [{"event_type": "LOGIN_FAILURE"}]
    mock_client.admin_unlock_user.return_value = {"id": 3}
    service = AdminService(api_client=mock_client)

    ok, events, _ = service.audit_events(limit=5, event_type="LOGIN_FAILURE")
    assert ok and events == [{"event_type": "LOGIN_FAILURE"}]
    mock_client.admin_audit_events.assert_called_once_with(limit=5, event_type="LOGIN_FAILURE")

    ok, data, _ = service.unlock_user(3)
    assert ok and data == {"id": 3}


def test_admin_errors_are_readable():
    mock_client = MagicMock()
    mock_client._request.side_effect = RuntimeError('Backend returned HTTP 422: {"detail": []}')
    ok, _, err = AdminService(api_client=mock_client).update_user(1, email="bad")
    assert not ok and "{" not in err


def test_admin_page_success_message_survives_the_rerun():
    import streamlit as st

    from src.frontend.views import admin_page

    st.session_state.clear()
    st.session_state["_admin_flash"] = "User 'x' updated."
    with (
        patch.object(admin_page, "is_authenticated", return_value=True),
        patch.object(admin_page, "is_admin", return_value=True),
        patch.object(admin_page, "AdminService"),
        patch.object(admin_page, "_render_directory"),
        patch.object(admin_page, "_render_audit_log"),
        patch.object(admin_page.st, "success") as success,
        patch.object(admin_page.st, "tabs", return_value=[MagicMock(), MagicMock()]),
    ):
        admin_page.render()
    success.assert_called_once()
    assert "_admin_flash" not in st.session_state
