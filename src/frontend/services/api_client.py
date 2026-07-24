"""
REST API client for AnalystGPT Enterprise.

Responsibilities
----------------
- Communicate with the AnalystGPT REST API.
- Encapsulate HTTP communication.
- Provide a simple interface for frontend services.

This class contains no business logic.
"""

from __future__ import annotations

from typing import Any

import httpx

from src.frontend.config.settings import (
    API_BASE_URL,
)


class APIClient:
    """
    REST client used by the Streamlit frontend.
    """

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: float = 30.0,
    ) -> None:

        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _get(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """
        Execute a GET request.
        """

        response = self._client.get(endpoint)

        response.raise_for_status()

        return response.json()

    def _post(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a POST request.
        """

        response = self._client.post(
            endpoint,
            json=payload,
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # System
    # ==========================================================

    def root(self) -> dict[str, Any]:
        """
        GET /
        """

        return self._get("/")

    def health(self) -> dict[str, Any]:
        """
        GET /api/health
        """

        return self._get("/api/health")

    def version(self) -> dict[str, Any]:
        """
        GET /api/version
        """

        return self._get("/api/version")

    # ==========================================================
    # Dashboard
    # ==========================================================

    def dashboard(self) -> dict[str, Any]:
        """
        GET /dashboard
        """

        return self._get("/dashboard")

    # ==========================================================
    # Reports
    # ==========================================================

    def reports(self) -> dict[str, Any]:
        """
        GET /reports
        """

        return self._get("/reports")

    # ==========================================================
    # Pipeline
    # ==========================================================

    def run_pipeline(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        POST /api/pipeline
        """

        return self._post(
            "/api/pipeline",
            payload,
        )

    # ==========================================================
    # Context Manager
    # ==========================================================

    def close(self) -> None:
        """
        Close the HTTP client.
        """

        self._client.close()

    def __enter__(self) -> "APIClient":

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:

        self.close()