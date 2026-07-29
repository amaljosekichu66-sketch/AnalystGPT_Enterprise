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
    ) -> dict[str, Any]:
        """
        Execute an HTTP request.
        """

        try:

            response = self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
            )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Backend request timed out. "
                "The analytics pipeline or AI engine may still be processing."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Backend returned HTTP {exc.response.status_code}: "
                f"{exc.response.text}"
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
    ) -> dict[str, Any]:
        """
        Execute a GET request.
        """

        return self._request(
            "GET",
            endpoint,
            params=params,
        )

    def _post(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a POST request.
        """

        return self._request(
            "POST",
            endpoint,
            json=payload,
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