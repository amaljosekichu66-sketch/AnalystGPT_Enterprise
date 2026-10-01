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
from src.frontend.services.errors import friendly_error, http_status
from src.frontend.services.session_manager import (
    clear_authenticated_session,
    get_auth_token,
    set_auth_user,
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
        }

        try:
            self._client.register(payload=payload)
            return True, None
        except RuntimeError as exc:
            error_msg = str(exc)
            if "already exists" in error_msg.lower() or "409" in error_msg:
                return False, "A user with this username or email already exists."
            if http_status(exc) == 422:
                return False, (
                    "Check your details: the username needs 3–50 letters, digits, '_' or '-', "
                    "and the password 8–128 characters."
                )
            return False, friendly_error(exc, "registration")
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
            if http_status(exc) == 422:
                return False, "Enter a username or email (up to 254 characters) and a password."
            return False, friendly_error(exc, "sign-in")

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

    def change_password(self, current_password: str, new_password: str) -> tuple[bool, str | None]:
        """
        Change the password; on success the session is cleared (every token is revoked).
        """
        try:
            self._client.change_password(current_password, new_password)
        except RuntimeError as exc:
            message = str(exc)
            if "incorrect" in message.lower():
                return False, "Current password is incorrect."
            if "400" in message or "422" in message:
                return False, "The new password does not meet the password policy."
            return False, "Could not change the password. Please try again."
        clear_authenticated_session()
        return True, None

    def logout_everywhere(self) -> tuple[bool, str | None]:
        """
        Sign out of every session on every device, then clear this one.
        """
        try:
            self._client.logout_all()
        except Exception as exc:
            logger.warning("Sign out everywhere failed: %s", exc)
            return False, "Could not sign out of other sessions. Please try again."
        clear_authenticated_session()
        return True, None

    def revalidate_session(self, max_age_seconds: int = 300) -> None:
        """
        Re-check the session against GET /api/auth/me at most every `max_age_seconds` (I2).

        Refreshes the cached role (a demoted user stopped seeing stale pages
        only after signing out) and clears the session when the backend no
        longer accepts the token: revoked, invalidated, expired or disabled.
        """
        import time

        import streamlit as st

        now = time.monotonic()
        if now - st.session_state.get("_session_checked_at", 0.0) < max_age_seconds:
            return
        st.session_state["_session_checked_at"] = now

        ok, user_data, error = self.fetch_current_user()
        if ok and user_data:
            set_auth_user(user_data)
        elif error and ("401" in error or "403" in error or "expired" in error.lower()):
            clear_authenticated_session()

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
