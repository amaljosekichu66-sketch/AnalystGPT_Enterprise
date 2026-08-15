"""
Unit and integration test suite for Frontend Authentication, Session Management, and Security Integration.

Tests:
- SessionManager authentication helpers and comprehensive session state cleanup.
- APIClient Bearer token injection and auth/admin endpoint methods.
- AuthService login, logout, current user resolution, and error translation.
- 401 Unauthorized vs 403 Forbidden handling in the frontend.
- Cross-tenant session and data isolation across User A -> logout -> User B lifecycle.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.frontend.services.api_client import APIClient
from src.frontend.services.auth_service import AuthService
from src.frontend.services.session_manager import (
    AUTH_STATUS_KEY,
    AUTH_TOKEN_KEY,
    AUTH_USER_KEY,
    DATAFRAME_KEY,
    PIPELINE_RESULT_KEY,
    clear_authenticated_session,
    get_auth_token,
    get_current_user,
    get_user_role,
    is_admin,
    is_authenticated,
    set_authenticated_session,
)


class TestFrontendSessionManagerAuth:
    """
    Test session_manager authentication state and cleanup.
    """

    @patch("streamlit.session_state", new_callable=dict)
    def test_unauthenticated_state(self, mock_state) -> None:
        """Verify unauthenticated state initially."""
        assert is_authenticated() is False
        assert get_auth_token() is None
        assert get_current_user() is None
        assert get_user_role() is None
        assert is_admin() is False

    @patch("streamlit.session_state", new_callable=dict)
    def test_authenticated_state_analyst(self, mock_state) -> None:
        """Verify authenticated state for Analyst."""
        user_data = {
            "id": 1,
            "username": "analyst_alice",
            "email": "alice@enterprise.com",
            "role": "ANALYST",
            "status": "ACTIVE",
        }
        set_authenticated_session(token="jwt.token.abc", user_data=user_data)

        assert is_authenticated() is True
        assert get_auth_token() == "jwt.token.abc"
        assert get_current_user() == user_data
        assert get_user_role() == "ANALYST"
        assert is_admin() is False

    @patch("streamlit.session_state", new_callable=dict)
    def test_authenticated_state_admin(self, mock_state) -> None:
        """Verify authenticated state and is_admin check for Admin."""
        user_data = {
            "id": 2,
            "username": "admin_bob",
            "email": "bob@enterprise.com",
            "role": "ADMIN",
            "status": "ACTIVE",
        }
        set_authenticated_session(token="jwt.token.xyz", user_data=user_data)

        assert is_authenticated() is True
        assert get_user_role() == "ADMIN"
        assert is_admin() is True

    @patch("streamlit.session_state", new_callable=dict)
    def test_clear_authenticated_session_purges_all_state(self, mock_state) -> None:
        """Verify clear_authenticated_session thoroughly wipes auth, datasets, and caches."""
        # Setup residual state
        mock_state[AUTH_TOKEN_KEY] = "token_to_clear"
        mock_state[AUTH_USER_KEY] = {"username": "alice"}
        mock_state[AUTH_STATUS_KEY] = "AUTHENTICATED"
        mock_state[DATAFRAME_KEY] = MagicMock()
        mock_state[PIPELINE_RESULT_KEY] = MagicMock()
        mock_state["dashboard_cache"] = {"cached": "data"}
        mock_state["current_page"] = "Reports"

        clear_authenticated_session()

        assert AUTH_TOKEN_KEY not in mock_state
        assert AUTH_USER_KEY not in mock_state
        assert AUTH_STATUS_KEY not in mock_state
        assert DATAFRAME_KEY not in mock_state
        assert PIPELINE_RESULT_KEY not in mock_state
        assert "dashboard_cache" not in mock_state
        assert is_authenticated() is False
        assert mock_state["current_page"] == "Dashboard"


class TestAPIClientAuth:
    """
    Test APIClient Bearer token injection and endpoint calls.
    """

    @pytest.fixture
    def client(self) -> APIClient:
        return APIClient(base_url="http://localhost:8000")

    @patch("src.frontend.services.api_client.get_auth_token", return_value="mock.session.token")
    @patch("src.frontend.services.api_client.httpx.Client.request")
    def test_bearer_token_injected_from_session(self, mock_request, mock_get_token, client) -> None:
        """When session token exists, Authorization: Bearer <token> is injected."""
        response = MagicMock()
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        mock_request.return_value = response

        client.reports()

        mock_request.assert_called_once_with(
            method="GET",
            url="/reports",
            params=None,
            json=None,
            headers={"Authorization": "Bearer mock.session.token"},
        )

    @patch("src.frontend.services.api_client.get_auth_token", return_value=None)
    @patch("src.frontend.services.api_client.httpx.Client.request")
    def test_unauthenticated_request_has_no_auth_header(self, mock_request, mock_get_token, client) -> None:
        """When no session token exists, headers is None."""
        response = MagicMock()
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        mock_request.return_value = response

        client.health()

        mock_request.assert_called_once_with(
            method="GET",
            url="/api/health",
            params=None,
            json=None,
            headers=None,
        )

    @patch.object(APIClient, "_post")
    def test_login_method(self, mock_post, client) -> None:
        """Verify login helper posts credentials to /api/auth/login."""
        mock_post.return_value = {"access_token": "token123", "user": {}}
        res = client.login("alice", "Password123!")
        mock_post.assert_called_once_with(
            "/api/auth/login",
            payload={"username": "alice", "password": "Password123!"},
        )
        assert res["access_token"] == "token123"

    @patch.object(APIClient, "_get")
    def test_me_method(self, mock_get, client) -> None:
        """Verify me helper calls /api/auth/me."""
        mock_get.return_value = {"username": "alice"}
        res = client.me(token="token123")
        mock_get.assert_called_once_with("/api/auth/me", token="token123")
        assert res["username"] == "alice"

    @patch.object(APIClient, "_get")
    def test_admin_list_users(self, mock_get, client) -> None:
        """Verify admin_list_users calls /api/admin/users."""
        mock_get.return_value = {"items": [], "total": 0}
        client.admin_list_users(limit=50, offset=10, token="admin_tok")
        mock_get.assert_called_once_with(
            "/api/admin/users",
            params={"limit": 50, "offset": 10},
            token="admin_tok",
        )


class TestAuthService:
    """
    Test AuthService login, logout, profile resolution, and error translation.
    """

    @patch("streamlit.session_state", new_callable=dict)
    def test_login_success(self, mock_state) -> None:
        """Successful login initializes session state and returns (True, None)."""
        mock_client = MagicMock()
        mock_client.login.return_value = {
            "access_token": "valid.token.here",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": 1,
                "username": "charlie",
                "email": "charlie@enterprise.com",
                "role": "ANALYST",
                "status": "ACTIVE",
            },
        }

        auth_service = AuthService(api_client=mock_client)
        success, err = auth_service.login("charlie", "SecretPass123!")

        assert success is True
        assert err is None
        assert mock_state[AUTH_TOKEN_KEY] == "valid.token.here"
        assert mock_state[AUTH_STATUS_KEY] == "AUTHENTICATED"

    @patch("streamlit.session_state", new_callable=dict)
    def test_login_invalid_credentials_returns_friendly_message(self, mock_state) -> None:
        """Invalid credentials translates 401 error cleanly."""
        mock_client = MagicMock()
        mock_client.login.side_effect = RuntimeError("Backend returned HTTP 401: Invalid username or password.")

        auth_service = AuthService(api_client=mock_client)
        success, err = auth_service.login("charlie", "WrongPass")

        assert success is False
        assert err == "Invalid username or password."
        assert AUTH_TOKEN_KEY not in mock_state

    @patch("streamlit.session_state", new_callable=dict)
    def test_login_disabled_account_returns_friendly_message(self, mock_state) -> None:
        """Disabled account translates 403 error cleanly."""
        mock_client = MagicMock()
        mock_client.login.side_effect = RuntimeError("Backend returned HTTP 403: User account is suspended.")

        auth_service = AuthService(api_client=mock_client)
        success, err = auth_service.login("suspended_user", "Pass123!")

        assert success is False
        assert "deactivated or suspended" in err  # type: ignore

    @patch("streamlit.session_state", new_callable=dict)
    def test_logout_clears_session_state(self, mock_state) -> None:
        """Logout revokes token and clears session state."""
        mock_client = MagicMock()
        mock_state[AUTH_TOKEN_KEY] = "active_token"
        mock_state[AUTH_STATUS_KEY] = "AUTHENTICATED"

        auth_service = AuthService(api_client=mock_client)
        success, err = auth_service.logout()

        assert success is True
        assert err is None
        mock_client.logout.assert_called_once_with(token="active_token")
        assert AUTH_TOKEN_KEY not in mock_state
        assert is_authenticated() is False


class TestCrossUserSessionIsolation:
    """
    Test User A login -> logout -> User B login cross-tenant session isolation.
    """

    @patch("streamlit.session_state", new_callable=dict)
    def test_user_a_to_user_b_isolation(self, mock_state) -> None:
        """User B must never inherit cached datasets or state from User A."""
        mock_client = MagicMock()
        auth_service = AuthService(api_client=mock_client)

        # 1. User A logs in
        mock_client.login.return_value = {
            "access_token": "token_a",
            "user": {"id": 10, "username": "user_a", "role": "ANALYST"},
        }
        auth_service.login("user_a", "PassA!")
        mock_state[DATAFRAME_KEY] = "User A Private Dataframe"
        mock_state["dashboard_cache"] = {"user_a": "sensitive_metrics"}

        assert get_auth_token() == "token_a"
        assert get_current_user()["username"] == "user_a"
        assert mock_state[DATAFRAME_KEY] == "User A Private Dataframe"

        # 2. User A logs out
        auth_service.logout()

        assert is_authenticated() is False
        assert DATAFRAME_KEY not in mock_state
        assert "dashboard_cache" not in mock_state

        # 3. User B logs in
        mock_client.login.return_value = {
            "access_token": "token_b",
            "user": {"id": 20, "username": "user_b", "role": "VIEWER"},
        }
        auth_service.login("user_b", "PassB!")

        assert is_authenticated() is True
        assert get_auth_token() == "token_b"
        assert get_current_user()["username"] == "user_b"
        assert get_user_role() == "VIEWER"

        # Verify absolutely no residual data from User A exists
        assert DATAFRAME_KEY not in mock_state
        assert "dashboard_cache" not in mock_state
