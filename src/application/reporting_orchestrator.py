"""
Reporting orchestrator for AnalystGPT Enterprise.

Coordinates reporting operations for the frontend and REST API.

Responsibilities
----------------
- Provide report metadata.
- Expose the latest generated reports.
- Coordinate report exports (Text and PDF).
- Expose a stable application-layer interface.

This module intentionally contains orchestration logic only.
Business logic belongs in ReportingManager.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.application.app import Application
from src.core import config
from src.core.config import (
    DEFAULT_PDF_REPORT_FILENAME,
    DEFAULT_REPORT_FILENAME,
)
from src.core.logger import logger
from src.reporting.structured_report import StructuredReport


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
            "executive_summary": ai_report.executive_summary,
            "recommendations": ai_report.recommendations,
            "explanations": ai_report.explanations,
            "narrative": ai_report.narrative,
            "model": ai_report.model,
            "provider": ai_report.provider,
            "execution_time": ai_report.execution_time,
            "generated_at": ai_report.generated_at,
        }

    def _resolve_context_and_report(
        self,
        user_id: int | None = None,
        report_id: int | None = None,
    ) -> tuple[StructuredReport | None, Any | None, dict[str, Any] | None]:
        """
        Resolve StructuredReport, AI report, and lineage metadata.
        """
        structured_report: StructuredReport | None = None
        ai_report: Any | None = None
        lineage: dict[str, Any] | None = None

        # 1. Check in-memory result for report_id or user
        result = None
        if report_id is not None:
            try:
                result = self._application.get_result_by_report_id(report_id)
            except AttributeError:
                result = None

        if result is None:
            try:
                result = self._application.get_result_for_user(user_id=user_id)
            except AttributeError:
                result = getattr(
                    self._application,
                    "get_last_result",
                    lambda: getattr(self._application, "last_result", None),
                )()

        if result and getattr(result, "success", False) and getattr(result, "pipeline_report", None):
            reporting_rep = result.pipeline_report.reporting_report
            if reporting_rep and hasattr(reporting_rep, "report"):
                structured_report = reporting_rep.report

            ai_report = result.pipeline_report.ai_report
            if ai_report is None and getattr(result, "ai_job_id", None):
                try:
                    job_data = self._application.ai_job_service.get_job_with_report(
                        job_id=result.ai_job_id,
                        user_id=user_id,
                    )
                    if job_data:
                        ai_report = job_data.get("ai_report")
                except Exception:
                    pass

        # 2. Extract lineage
        persistence = getattr(self._application, "persistence", None)
        if persistence:
            lineage = {
                "pipeline_run_id": getattr(persistence, "_pipeline_run_id", None),
                "source_version_id": getattr(persistence, "_source_version_id", None),
                "cleaned_version_id": getattr(persistence, "_cleaned_version_id", None),
                "cleaning_execution_id": getattr(persistence, "_cleaning_execution_id", None),
                "context_schema_version": "1.0",
            }

        return structured_report, ai_report, lineage

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
            result = getattr(
                self._application,
                "get_last_result",
                lambda: getattr(self._application, "last_result", None),
            )()

        logger.info(
            "Returned Result : %s",
            result,
        )
        logger.info("=" * 80)

        if result is None or not result.success or result.pipeline_report is None:
            return {
                "reports": [],
                "report": None,
                "ai_report": None,
                "execution_time": None,
                "output_path": None,
            }

        reporting_report = result.pipeline_report.reporting_report

        ai_report = result.pipeline_report.ai_report

        ai_report_dict = None
        if ai_report is not None:
            ai_report_dict = self._build_ai_report(ai_report)
        elif getattr(result, "ai_job_id", None) is not None:
            try:
                ai_job_data = self._application.ai_job_service.get_job_with_report(
                    job_id=result.ai_job_id,
                    user_id=user_id,
                )
                if ai_job_data is not None and ai_job_data.get("ai_report") is not None:
                    ai_report_dict = ai_job_data["ai_report"]
            except Exception:
                pass

        return {
            "reports": self._build_report_list(
                ai_report_dict is not None,
            ),
            "report": reporting_report.to_dict(),
            "ai_report": ai_report_dict,
            "execution_time": result.execution_time,
            "output_path": result.output_path,
        }

    # ==========================================================
    # Export Operations
    # ==========================================================

    def export_text_report(
        self,
        dataframe: Any = None,
        filename: str | None = None,
        user_id: int | None = None,
        report_id: int | None = None,
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate and export a text report.
        """
        logger.info(
            "ReportingOrchestrator: export_text_report requested (user_id=%s, report_id=%s)", user_id, report_id
        )

        # Database-level ownership verification if report_id provided
        if report_id is not None:
            report_repo = getattr(getattr(self._application, "persistence", None), "_report_repository", None)
            if report_repo is not None:
                record = report_repo.get_by_id(report_id, user_id=user_id)
                if record is None:
                    return {
                        "success": False,
                        "message": "Report not found or access denied.",
                    }
                # Check if file exists on disk
                disk_path = Path(record.get("report_path", ""))
                if disk_path.exists():
                    return {
                        "success": True,
                        "message": "Text report exported successfully.",
                        "export_path": str(disk_path.resolve()),
                        "path": str(disk_path.resolve()),
                        "filename": disk_path.name,
                        "mime_type": "text/plain",
                    }

        structured_report, ai_report, lineage = self._resolve_context_and_report(
            user_id=user_id,
            report_id=report_id,
        )

        if structured_report is None:
            return {
                "success": False,
                "message": "No generated report was found.",
            }

        target_path = output_path
        if target_path is None and filename is not None:
            target_path = config.REPORT_OUTPUT_DIRECTORY / filename

        export_path = self._application.reporting_manager.export_text(
            report=structured_report,
            output_path=target_path,
            ai_report=ai_report,
            lineage=lineage,
        )

        p = Path(export_path)
        return {
            "success": True,
            "message": "Text report exported successfully.",
            "export_path": str(p.resolve()),
            "path": str(p.resolve()),
            "filename": p.name,
            "mime_type": "text/plain",
        }

    def export_pdf_report(
        self,
        dataframe: Any = None,
        filename: str | None = None,
        user_id: int | None = None,
        report_id: int | None = None,
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate and export a PDF report.
        """
        logger.info("ReportingOrchestrator: export_pdf_report requested (user_id=%s, report_id=%s)", user_id, report_id)

        # Database-level ownership verification if report_id provided
        if report_id is not None:
            report_repo = getattr(getattr(self._application, "persistence", None), "_report_repository", None)
            if report_repo is not None:
                record = report_repo.get_by_id(report_id, user_id=user_id)
                if record is None:
                    return {
                        "success": False,
                        "message": "Report not found or access denied.",
                    }

        structured_report, ai_report, lineage = self._resolve_context_and_report(
            user_id=user_id,
            report_id=report_id,
        )

        if structured_report is None:
            return {
                "success": False,
                "message": "No generated report was found to export as PDF.",
            }

        target_path = output_path
        if target_path is None and filename is not None:
            target_path = config.REPORT_OUTPUT_DIRECTORY / filename

        export_path = self._application.reporting_manager.export_pdf(
            report=structured_report,
            output_path=target_path,
            ai_report=ai_report,
            lineage=lineage,
        )

        p = Path(export_path)
        return {
            "success": True,
            "message": "PDF report exported successfully.",
            "export_path": str(p.resolve()),
            "path": str(p.resolve()),
            "filename": p.name,
            "mime_type": "application/pdf",
        }
