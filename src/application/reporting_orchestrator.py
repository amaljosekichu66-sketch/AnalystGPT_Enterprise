"""
Reporting orchestrator for AnalystGPT Enterprise.

Coordinates reporting operations for the frontend and REST API.

Responsibilities
----------------
- Provide report metadata.
- Expose the latest generated reports.
- Coordinate future reporting operations.
- Expose a stable application-layer interface.

This module intentionally contains orchestration logic only.
Business logic belongs in ReportingManager.
"""

from __future__ import annotations

from typing import Any

from src.application.app import Application
from src.core.logger import logger


class ReportingOrchestrator:
    """
    Coordinates reporting operations.
    """

    def __init__(
        self,
        application: Application,
    ) -> None:
        """
        Initialise the orchestrator.
        """

        self._application = application

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _build_report_list(
        self,
        has_ai: bool,
    ) -> list[dict[str, str]]:
        """
        Return available reports.
        """

        reports = [
            {
                "name": "Executive Summary",
                "status": "Available",
            },
            {
                "name": "Quality Report",
                "status": "Available",
            },
            {
                "name": "Analytics Report",
                "status": "Available",
            },
            {
                "name": "Structured Report",
                "status": "Available",
            },
        ]

        if has_ai:

            reports.extend(
                [
                    {
                        "name": "AI Executive Summary",
                        "status": "Available",
                    },
                    {
                        "name": "AI Recommendations",
                        "status": "Available",
                    },
                    {
                        "name": "AI Explanations",
                        "status": "Available",
                    },
                    {
                        "name": "AI Narrative",
                        "status": "Available",
                    },
                ]
            )

        return reports

    def _build_ai_report(
        self,
        ai_report,
    ) -> dict[str, Any] | None:
        """
        Convert AIReport into a serialisable dictionary.
        """

        if ai_report is None:
            return None

        return {
            "executive_summary":
                ai_report.executive_summary,
            "recommendations":
                ai_report.recommendations,
            "explanations":
                ai_report.explanations,
            "narrative":
                ai_report.narrative,
            "model":
                ai_report.model,
            "provider":
                ai_report.provider,
            "execution_time":
                ai_report.execution_time,
            "generated_at":
                ai_report.generated_at,
        }

    # ==========================================================
    # Report Metadata
    # ==========================================================

    def get_reports(
        self,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Return reporting metadata for the latest pipeline execution.
        """

        logger.info("=" * 80)

        logger.info("GET REPORTS REQUESTED")

        logger.info("=" * 80)

        logger.info(
            "Application Instance : %s",
            id(self._application),
        )

        try:
            result = self._application.get_result_for_user(user_id=user_id)
        except AttributeError:
            result = getattr(self._application, "get_last_result", lambda: getattr(self._application, "last_result", None))()

        logger.info(
            "Returned Result : %s",
            result,
        )

        logger.info("=" * 80)

        if (
            result is None
            or not result.success
            or result.pipeline_report is None
        ):

            return {
                "reports": [],
                "report": None,
                "ai_report": None,
                "execution_time": None,
                "output_path": None,
            }

        reporting_report = (
            result.pipeline_report.reporting_report
        )

        ai_report = (
            result.pipeline_report.ai_report
        )

        return {
            "reports": self._build_report_list(
                ai_report is not None,
            ),
            "report": reporting_report.to_dict(),
            "ai_report": self._build_ai_report(
                ai_report,
            ),
            "execution_time":
                result.execution_time,
            "output_path":
                result.output_path,
        }

    # ==========================================================
    # Export Operations
    # ==========================================================

    def export_text_report(
        self,
        dataframe,
        filename: str,
    ) -> dict[str, Any]:
        """
        Prepare a text report export.

        ReportingManager integration will be added
        in a future sprint.
        """

        return {
            "success": False,
            "message": (
                "Text report export is not yet "
                "implemented."
            ),
            "filename": filename,
        }

    def export_pdf_report(
        self,
        dataframe,
        filename: str,
    ) -> dict[str, Any]:
        """
        Prepare a PDF report export.

        ReportingManager integration will be added
        in a future sprint.
        """

        return {
            "success": False,
            "message": (
                "PDF report export is not yet "
                "implemented."
            ),
            "filename": filename,
        }