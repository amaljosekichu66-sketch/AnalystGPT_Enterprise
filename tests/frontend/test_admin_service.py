"""
Unit tests for Frontend Admin Service.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

from unittest.mock import MagicMock

from src.frontend.services.admin_service import AdminService


def test_admin_list_users():
    mock_client = MagicMock()
    mock_client._request.return_value = {"items": [{"id": 1, "username": "admin"}], "total": 1}

    service = AdminService(api_client=mock_client)
    success, data, err = service.list_users(limit=50, offset=0)

    assert success is True
    assert data["total"] == 1
    assert err is None


def test_admin_get_user():
    mock_client = MagicMock()
    mock_client._request.return_value = {"id": 2, "username": "analyst"}

    service = AdminService(api_client=mock_client)
    success, data, err = service.get_user(user_id=2)

    assert success is True
    assert data["username"] == "analyst"
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
