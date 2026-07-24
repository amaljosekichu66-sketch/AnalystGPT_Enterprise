"""
Dashboard orchestrator for AnalystGPT Enterprise.

Coordinates dashboard information for API consumers.

Responsibilities
----------------
- Aggregate dashboard information.
- Coordinate application services.
- Return structured dashboard data.

This module contains orchestration logic only.
"""

from __future__ import annotations

from typing import Any

from src.core.constants import (
    APP_NAME,
    APP_VERSION,
)


class DashboardOrchestrator:
    """
    Coordinates dashboard information.
    """

    def get_dashboard(self) -> dict[str, Any]:
        """
        Build dashboard response.
        """

        return {
            "application": {
                "name": APP_NAME,
                "version": APP_VERSION,
                "status": "Ready",
            },
            "pipeline": {
                "status": "Idle",
                "last_execution": None,
            },
            "database": {
                "status": "Configured",
            },
            "quality": {
                "status": "Waiting",
            },
            "analytics": {
                "status": "Waiting",
            },
            "reporting": {
                "status": "Waiting",
            },
        }

    def get_status(self) -> dict[str, Any]:
        """
        Return lightweight dashboard status.
        """

        return {
            "application": APP_NAME,
            "version": APP_VERSION,
            "status": "Ready",
        }