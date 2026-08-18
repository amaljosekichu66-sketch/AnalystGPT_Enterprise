"""
Admin Service for AnalystGPT Enterprise Frontend.

Provides a technology-neutral service interface for administrative
user management, account updates, and deletions.

Sprint 14 Phase 6 — OpenAPI / React Migration Readiness.
"""

from __future__ import annotations

from typing import Any

from src.frontend.services.api_client import APIClient


class AdminService:
    """
    Technology-neutral frontend service for user administration workflows.
    """

    def __init__(self, api_client: APIClient | None = None) -> None:
        self._api_client = api_client or APIClient()

    def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        token: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        List all registered users with pagination.
        """
        try:
            res = self._api_client._request(
                "GET",
                f"/api/admin/users?limit={limit}&offset={offset}",
                token=token,
            )
            return True, res, None
        except Exception as exc:
            return False, None, str(exc)

    def get_user(
        self,
        user_id: int,
        token: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Retrieve profile details for a specific user.
        """
        try:
            res = self._api_client._request(
                "GET",
                f"/api/admin/users/{user_id}",
                token=token,
            )
            return True, res, None
        except Exception as exc:
            return False, None, str(exc)

    def update_user(
        self,
        user_id: int,
        role: str | None = None,
        status_val: str | None = None,
        email: str | None = None,
        token: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Update user role, account status, or email.
        """
        payload: dict[str, Any] = {}
        if role is not None:
            payload["role"] = role
        if status_val is not None:
            payload["status"] = status_val
        if email is not None:
            payload["email"] = email

        try:
            res = self._api_client._request(
                "PATCH",
                f"/api/admin/users/{user_id}",
                json=payload,
                token=token,
            )
            return True, res, None
        except Exception as exc:
            return False, None, str(exc)

    def delete_user(
        self,
        user_id: int,
        token: str | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        Delete a user account.
        """
        try:
            res = self._api_client._request(
                "DELETE",
                f"/api/admin/users/{user_id}",
                token=token,
            )
            return True, res, None
        except Exception as exc:
            return False, None, str(exc)
