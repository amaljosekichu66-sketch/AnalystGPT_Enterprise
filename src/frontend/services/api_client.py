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


def _forwarding_headers() -> dict[str, str]:
    """
    Tell the API which browser this request is for (M11).

    Every Streamlit user reaches the API from the frontend's own address, so
    without this all of them shared one rate-limit bucket. The API believes
    the header only from peers in its TRUSTED_PROXY_IPS. An upstream proxy's
    X-Forwarded-For chain is kept, with the address Streamlit saw appended.
    """
    try:
        import streamlit as st

        if not st.runtime.exists():
            return {}
        browser = st.context.ip_address
        upstream = st.context.headers.get("X-Forwarded-For")
    except Exception:
        return {}
    # Only real strings: test harnesses (and odd proxies) can hand back other objects.
    chain = [hop for hop in (upstream, browser) if isinstance(hop, str) and hop]
    return {"X-Forwarded-For": ", ".join(chain)} if chain else {}


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

    DATASETS = "/api/datasets"

    REPORTS = "/api/reports"

    DASHBOARD = "/api/powerbi/dashboard"

    AUTH_LOGIN = "/api/auth/login"

    AUTH_REGISTER = "/api/auth/register"

    AUTH_ME = "/api/auth/me"

    AUTH_LOGOUT = "/api/auth/logout"

    AUTH_PASSWORD = "/api/auth/password"

    AUTH_LOGOUT_ALL = "/api/auth/logout-all"

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
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute an HTTP request with automatic Bearer token injection.
        """
        request_headers = dict(headers) if headers else {}
        request_headers.update(_forwarding_headers())
        auth_token = token or get_auth_token()
        if auth_token and "Authorization" not in request_headers:
            request_headers["Authorization"] = f"Bearer {auth_token}"

        try:

            request_kwargs: dict[str, Any] = {}
            if files is not None:
                request_kwargs["files"] = files

            response = self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
                headers=request_headers if request_headers else None,
                **request_kwargs,
            )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Backend request timed out. " "The analytics pipeline or AI engine may still be processing."
            ) from exc

        except httpx.HTTPStatusError as exc:
            try:
                error_body = exc.response.json()
                detail = error_body.get("error") or error_body.get("message") or exc.response.text
            except Exception:
                detail = exc.response.text
            raise RuntimeError(f"Backend returned HTTP {exc.response.status_code}: {detail}") from exc

        except httpx.RequestError as exc:
            raise RuntimeError(f"Unable to connect to backend: {exc}") from exc

        except Exception as exc:
            raise RuntimeError(f"Unexpected API client error: {exc}") from exc

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
        dataset_version_id: str,
    ) -> dict[str, Any]:
        """
        Return dashboard information for an uploaded dataset.
        """

        return self._get(
            self.DASHBOARD,
            params={
                "dataset_version_id": dataset_version_id,
            },
        )

    def powerbi_dashboard(
        self,
        dataset_version_id: str,
    ) -> dict[str, Any]:
        """
        Backwards-compatible alias.
        """

        return self.dashboard(
            dataset_version_id,
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

    def download_report(
        self,
        endpoint: str,
        token: str | None = None,
    ) -> bytes:
        """
        Download raw file bytes from a report export endpoint.
        """
        request_headers: dict[str, str] = _forwarding_headers()
        auth_token = token or get_auth_token()
        if auth_token:
            request_headers["Authorization"] = f"Bearer {auth_token}"

        response = self._client.get(
            endpoint,
            headers=request_headers if request_headers else None,
        )
        response.raise_for_status()
        return response.content

    def export_text_report(
        self,
        report_id: int | None = None,
        token: str | None = None,
    ) -> bytes:
        """
        Export text report via REST API.
        """
        endpoint = (
            f"/api/reports/{report_id}/export/text" if report_id is not None else "/api/reports/latest/export/text"
        )
        return self.download_report(endpoint, token=token)

    def export_pdf_report(
        self,
        report_id: int | None = None,
        token: str | None = None,
    ) -> bytes:
        """
        Export PDF report via REST API.
        """
        endpoint = f"/api/reports/{report_id}/export/pdf" if report_id is not None else "/api/reports/latest/export/pdf"
        return self.download_report(endpoint, token=token)

    # ==========================================================
    # Power BI
    # ==========================================================

    # ==========================================================
    # Datasets
    # ==========================================================

    def upload_dataset(
        self,
        filename: str,
        content: bytes,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Upload dataset bytes (multipart). Returns the server-issued `dataset_version_id`.
        """

        return self._request(
            "POST",
            self.DATASETS,
            files={"file": (filename, content)},
            token=token,
        )

    # ==========================================================
    # Pipeline
    # ==========================================================

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

    def change_password(self, current_password: str, new_password: str) -> dict[str, Any]:
        """
        Change the signed-in user's password. Every session is signed out.
        """
        return self._post(
            self.AUTH_PASSWORD,
            payload={"current_password": current_password, "new_password": new_password},
        )

    def logout_all(self) -> dict[str, Any]:
        """
        Invalidate every access token of the signed-in user.
        """
        return self._post(self.AUTH_LOGOUT_ALL, payload={})

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

    def cancel_ai_job(self, job_id: str, token: str | None = None) -> dict[str, Any]:
        """POST /api/ai/jobs/{job_id}/cancel (P2-02)."""
        return self._post(f"{self.AI_JOBS}/{job_id}/cancel", token=token)

    # ==========================================================
    # Datasets, governance and policies (P2-04, P2-05)
    # ==========================================================

    def dataset_analysis(self, dataset_version_id: str) -> dict[str, Any]:
        """GET /api/datasets/{id}/analysis: profile, chart plan, policy recommendation."""
        return self._get(f"{self.DATASETS}/{dataset_version_id}/analysis")

    def delete_dataset(self, dataset_version_id: str) -> dict[str, Any]:
        return self._delete(f"{self.DATASETS}/{dataset_version_id}")

    def governance_preview(self, dataset_version_id: str, missing_value_policy: str) -> dict[str, Any]:
        return self._post(
            "/api/governance/preview",
            payload={
                "dataset_version_id": dataset_version_id,
                "cleaning_config": {"missing_value_policy": missing_value_policy},
            },
        )

    def list_policies(self, dataset_version_id: str | None = None) -> list[dict[str, Any]]:
        params = {"dataset_version_id": dataset_version_id} if dataset_version_id else None
        return self._get("/api/governance/policies", params=params)  # type: ignore[return-value]

    def propose_policy(self, dataset_version_id: str, missing_value_policy: str) -> dict[str, Any]:
        return self._post(
            "/api/governance/policies",
            payload={"dataset_version_id": dataset_version_id, "missing_value_policy": missing_value_policy},
        )

    def review_policy(self, proposal_id: str, approve: bool, note: str | None = None) -> dict[str, Any]:
        action = "approve" if approve else "reject"
        return self._post(f"/api/governance/policies/{proposal_id}/{action}", payload={"note": note})

    def run_pipeline_for(self, dataset_version_id: str, proposal_id: str | None = None) -> dict[str, Any]:
        """POST /api/pipeline, optionally with an APPROVED cleaning policy proposal."""
        payload: dict[str, Any] = {"dataset_version_id": dataset_version_id}
        if proposal_id:
            payload["cleaning_policy_proposal_id"] = proposal_id
        return self._post(self.PIPELINE, payload)

    # ==========================================================
    # Administration extras (P2-25)
    # ==========================================================

    def admin_audit_events(self, limit: int = 100, event_type: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        return self._get("/api/admin/audit-events", params=params)  # type: ignore[return-value]

    def admin_unlock_user(self, user_id: int) -> dict[str, Any]:
        return self._post(f"{self.ADMIN_USERS}/{user_id}/unlock")

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
        _exc_type,
        _exc,
        _traceback,
    ) -> None:
        """
        Exit the client context.
        """

        self.close()
