"""
Authentication service for AnalystGPT Enterprise Streamlit frontend.

Responsibilities
----------------
- Coordinate authentication workflows between Streamlit UI and APIClient.
- Manage secure login, session initialization, current user resolution, and logout.
- Provide clean error translation and safe state cleanup.
"""

from __future__ import annotations

from typing import Any

from src.core.logger import logger
from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import (
    clear_authenticated_session,
    get_auth_token,
    set_authenticated_session,
)


class AuthService:
    """
    Frontend service coordinating authentication and administrative workflows.
    """

    def __init__(self, api_client: APIClient | None = None) -> None:
        self._client = api_client or APIClient()

    def register(
        self,
        username: str,
        email: str,
        password: str,
    ) -> tuple[bool, str | None]:
        """
        Register a new user account. Returns (Success, Error Message).
        """
        if not username.strip() or not email.strip() or not password:
            return False, "Please provide username, email, and password."

        payload = {
            "username": username.strip(),
            "email": email.strip(),
            "password": password,
            "role": "ANALYST"  # Default role for self-registration
        }

        try:
            self._client.register(payload=payload)
            return True, None
        except RuntimeError as exc:
            error_msg = str(exc)
            if "already exists" in error_msg.lower() or "409" in error_msg:
                return False, "A user with this username or email already exists."
            return False, error_msg
        except Exception as exc:
            logger.error("Unexpected error during registration: %s", exc)
            return False, "An unexpected error occurred during registration."

    def login(
        self,
        username_or_email: str,
        password: str,
    ) -> tuple[bool, str | None]:
        """
        Execute login request and establish authenticated frontend session.

        Returns
        -------
        tuple[bool, str | None]
            (Success flag, Error message if failed)
        """
        if not username_or_email.strip() or not password:
            return False, "Please provide both username/email and password."

        try:
            response = self._client.login(
                username_or_email=username_or_email.strip(),
                password=password,
            )

            token = response.get("access_token")
            user_data = response.get("user")

            if not token or not user_data:
                return False, "Authentication succeeded but token response was invalid."

            # Establish clean authenticated session
            set_authenticated_session(token=token, user_data=user_data)
            logger.info("User '%s' authenticated successfully in frontend.", user_data.get("username"))
            return True, None

        except RuntimeError as exc:
            error_msg = str(exc)
            logger.warning("Frontend authentication failure: %s", error_msg)
            # User friendly message translation
            if "401" in error_msg or "Invalid username or password" in error_msg:
                return False, "Invalid username or password."
            if "403" in error_msg or "disabled" in error_msg.lower() or "suspended" in error_msg.lower():
                return False, "Your account has been deactivated or suspended. Please contact an administrator."
            if "Unable to connect" in error_msg:
                return False, "Unable to connect to AnalystGPT backend server."
            return False, error_msg

        except Exception as exc:
            logger.error("Unexpected error during login: %s", exc)
            return False, "An unexpected error occurred during login."

    def logout(self) -> tuple[bool, str | None]:
        """
        Invalidate session on backend and thoroughly purge frontend tenant state.

        Returns
        -------
        tuple[bool, str | None]
            (Success flag, Error message if failed)
        """
        token = get_auth_token()
        try:
            if token:
                self._client.logout(token=token)
        except Exception as exc:
            logger.warning("Backend token revocation notice: %s", exc)
        finally:
            clear_authenticated_session()
            logger.info("Frontend authenticated session cleared.")

        return True, None

    def fetch_current_user(self) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Authoritatively retrieve profile of current user from GET /api/auth/me.
        """
        token = get_auth_token()
        if not token:
            return False, None, "No active session token."

        try:
            user_data = self._client.me(token=token)
            return True, user_data, None
        except RuntimeError as exc:
            error_msg = str(exc)
            if "401" in error_msg:
                clear_authenticated_session()
                return False, None, "Session expired. Please log in again."
            return False, None, error_msg
        except Exception as exc:
            return False, None, str(exc)

    def admin_list_users(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Retrieve paginated list of users for administration.
        """
        token = get_auth_token()
        try:
            data = self._client.admin_list_users(limit=limit, offset=offset, token=token)
            return True, data, None
        except RuntimeError as exc:
            return False, None, str(exc)
        except Exception as exc:
            return False, None, str(exc)

    def admin_update_user(
        self,
        user_id: int,
        role: str | None = None,
        status: str | None = None,
        email: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Update user account status, role, or email as administrator.
        """
        token = get_auth_token()
        payload: dict[str, Any] = {}
        if role is not None:
            payload["role"] = role
        if status is not None:
            payload["status"] = status
        if email is not None:
            payload["email"] = email

        try:
            data = self._client.admin_update_user(user_id=user_id, payload=payload, token=token)
            return True, data, None
        except RuntimeError as exc:
            return False, None, str(exc)
        except Exception as exc:
            return False, None, str(exc)

    def admin_delete_user(
        self,
        user_id: int,
    ) -> tuple[bool, str | None]:
        """
        Delete a user account as administrator.
        """
        token = get_auth_token()
        try:
            self._client.admin_delete_user(user_id=user_id, token=token)
            return True, None
        except RuntimeError as exc:
            return False, str(exc)
        except Exception as exc:
            return False, str(exc)
