"""
REST API client for AnalystGPT Enterprise.

Responsibilities
----------------
- Communicate with the AnalystGPT REST API.
- Encapsulate HTTP communication.
- Provide a simple interface for frontend services.

This module intentionally contains no business logic.
"""

from __future__ import annotations

from typing import Any

import httpx

from src.frontend.config.settings import API_BASE_URL
from src.frontend.services.session_manager import get_auth_token


class APIClient:
    """
    REST client used by the Streamlit frontend.
    """

    # ==========================================================
    # API Endpoints
    # ==========================================================

    ROOT = "/"

    HEALTH = "/api/health"

    VERSION = "/api/version"

    PIPELINE = "/api/pipeline"

    REPORTS = "/reports"

    DASHBOARD = "/powerbi/dashboard"

    POWERBI_SUMMARY = "/powerbi/summary"

    POWERBI_PIPELINE = "/powerbi/pipeline"

    AUTH_LOGIN = "/api/auth/login"

    AUTH_REGISTER = "/api/auth/register"

    AUTH_ME = "/api/auth/me"

    AUTH_LOGOUT = "/api/auth/logout"

    ADMIN_USERS = "/api/admin/users"

    AI_JOBS = "/api/ai/jobs"

    # ==========================================================
    # Construction
    # ==========================================================

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: float = 180.0,
    ) -> None:
        """
        Initialise the REST client.
        """

        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(
                connect=10.0,
                read=timeout,
                write=timeout,
                pool=timeout,
            ),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
            ),
            follow_redirects=True,
        )

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute an HTTP request with automatic Bearer token injection.
        """
        request_headers = dict(headers) if headers else {}
        auth_token = token or get_auth_token()
        if auth_token and "Authorization" not in request_headers:
            request_headers["Authorization"] = f"Bearer {auth_token}"

        try:

            response = self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
                headers=request_headers if request_headers else None,
            )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Backend request timed out. "
                "The analytics pipeline or AI engine may still be processing."
            ) from exc

        except httpx.HTTPStatusError as exc:
            try:
                error_body = exc.response.json()
                detail = error_body.get("error") or error_body.get("message") or exc.response.text
            except Exception:
                detail = exc.response.text
            raise RuntimeError(
                f"Backend returned HTTP {exc.response.status_code}: {detail}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to connect to backend: {exc}"
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                f"Unexpected API client error: {exc}"
            ) from exc

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a GET request.
        """

        return self._request(
            "GET",
            endpoint,
            params=params,
            token=token,
        )

    def _post(
        self,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a POST request.
        """

        return self._request(
            "POST",
            endpoint,
            json=payload,
            token=token,
        )

    def _patch(
        self,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a PATCH request.
        """

        return self._request(
            "PATCH",
            endpoint,
            json=payload,
            token=token,
        )

    def _delete(
        self,
        endpoint: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a DELETE request.
        """

        return self._request(
            "DELETE",
            endpoint,
            token=token,
        )

    # ==========================================================
    # System
    # ==========================================================

    def root(
        self,
    ) -> dict[str, Any]:
        """
        GET /
        """

        return self._get(
            self.ROOT,
        )

    def health(
        self,
    ) -> dict[str, Any]:
        """
        GET /api/health
        """

        return self._get(
            self.HEALTH,
        )

    def version(
        self,
    ) -> dict[str, Any]:
        """
        GET /api/version
        """

        return self._get(
            self.VERSION,
        )

    # ==========================================================
    # Dashboard
    # ==========================================================

    def dashboard(
        self,
        dataset: str,
    ) -> dict[str, Any]:
        """
        Execute the analytics pipeline and
        return dashboard information.
        """

        return self._get(
            self.DASHBOARD,
            params={
                "dataset": dataset,
            },
        )

    def powerbi_dashboard(
        self,
        dataset: str,
    ) -> dict[str, Any]:
        """
        Backwards-compatible alias.
        """

        return self.dashboard(
            dataset,
        )

    # ==========================================================
    # Reports
    # ==========================================================

    def reports(
        self,
    ) -> dict[str, Any]:
        """
        Retrieve the latest generated reports.
        """

        return self._get(
            self.REPORTS,
        )

    def get_reports(
        self,
    ) -> dict[str, Any]:
        """
        Backwards-compatible alias.
        """

        return self.reports()

    def report(
        self,
    ) -> dict[str, Any]:
        """
        Legacy alias.
        """

        return self.reports()

    # ==========================================================
    # Power BI
    # ==========================================================

    def powerbi_summary(
        self,
        dataset: str,
    ) -> dict[str, Any]:
        """
        Retrieve Power BI summary data.
        """

        return self._get(
            self.POWERBI_SUMMARY,
            params={
                "dataset": dataset,
            },
        )

    def powerbi_pipeline(
        self,
        dataset: str,
    ) -> dict[str, Any]:
        """
        Retrieve pipeline summary.
        """

        return self._get(
            self.POWERBI_PIPELINE,
            params={
                "dataset": dataset,
            },
        )

    # ==========================================================
    # Pipeline
    # ==========================================================

    def run_pipeline(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute the complete analytics pipeline.
        """

        return self._post(
            self.PIPELINE,
            payload,
        )

    # ==========================================================
    # Authentication & Profile
    # ==========================================================

    def login(
        self,
        username_or_email: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Authenticate credentials and retrieve JWT access token.
        """
        return self._post(
            self.AUTH_LOGIN,
            payload={
                "username": username_or_email,
                "password": password,
            },
        )

    def register(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Register a new user account.
        """
        return self._post(
            self.AUTH_REGISTER,
            payload=payload,
        )

    def me(
        self,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve profile of currently authenticated user.
        """
        return self._get(
            self.AUTH_ME,
            token=token,
        )

    def logout(
        self,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Invalidate access token on backend.
        """
        return self._post(
            self.AUTH_LOGOUT,
            token=token,
        )

    # ==========================================================
    # Administration
    # ==========================================================

    def admin_list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        List all users with pagination (Admin only).
        """
        return self._get(
            self.ADMIN_USERS,
            params={"limit": limit, "offset": offset},
            token=token,
        )

    def admin_get_user(
        self,
        user_id: int,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Get user details by ID (Admin only).
        """
        return self._get(
            f"{self.ADMIN_USERS}/{user_id}",
            token=token,
        )

    def admin_update_user(
        self,
        user_id: int,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Update user role or status (Admin only).
        """
        return self._patch(
            f"{self.ADMIN_USERS}/{user_id}",
            payload=payload,
            token=token,
        )

    def admin_delete_user(
        self,
        user_id: int,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Delete user account (Admin only).
        """
        return self._delete(
            f"{self.ADMIN_USERS}/{user_id}",
            token=token,
        )

    # ==========================================================
    # AI Insight Jobs (Sprint 14 Phase 2)
    # ==========================================================

    def get_ai_job(
        self,
        job_id: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        GET /api/ai/jobs/{job_id}
        """
        return self._get(
            f"{self.AI_JOBS}/{job_id}",
            token=token,
        )

    def get_latest_ai_job(
        self,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        GET /api/ai/jobs/latest/status
        """
        return self._get(
            f"{self.AI_JOBS}/latest/status",
            token=token,
        )

    def retry_ai_job(
        self,
        job_id: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        POST /api/ai/jobs/{job_id}/retry
        """
        return self._post(
            f"{self.AI_JOBS}/{job_id}/retry",
            token=token,
        )

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def close(
        self,
    ) -> None:
        """
        Close the HTTP client.
        """

        self._client.close()

    # ==========================================================
    # Context Manager
    # ==========================================================

    def __enter__(
        self,
    ) -> "APIClient":
        """
        Enter the client context.
        """

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        """
        Exit the client context.
        """

        self.close()