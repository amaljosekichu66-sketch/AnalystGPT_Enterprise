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

import uuid
from pathlib import Path
from typing import Any

from src.application.app import Application
from src.core import config
from src.core.config import (
    DEFAULT_PDF_REPORT_FILENAME,
    DEFAULT_REPORT_FILENAME,
)
from src.core.logger import logger
from src.core.redaction import public_artifact_name, public_report_dict
from src.reporting.structured_report import StructuredReport


def _contained_report_file(raw: str | None) -> Path | None:
    """The stored report path, if it is an existing file inside REPORT_OUTPUT_DIRECTORY."""
    if not raw:
        return None
    path = Path(raw).resolve()
    root = Path(config.REPORT_OUTPUT_DIRECTORY).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        logger.warning("Refusing to serve a stored report path outside the report directory.")
        return None
    return path


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
                # Never another report (P2-03): a by-id cache miss (after a
                # restart, say) used to fall back to the user's LATEST result.
                return self._rebuild_from_persistence(report_id, user_id)

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

        # 2. Extract lineage from the resolved result itself. It used to be
        #    read from the Application's shared persistence state, i.e. from
        #    whichever run - by any user - happened to finish last.
        if result is not None:
            lineage = {
                "pipeline_run_id": getattr(result, "pipeline_run_id", None),
                "source_version_id": getattr(result, "dataset_version_id", None),
                "cleaned_version_id": getattr(result, "cleaned_version_id", None),
                "cleaning_execution_id": getattr(result, "cleaning_execution_id", None),
                "context_schema_version": "1.0",
            }

        return structured_report, ai_report, lineage

    # ==========================================================
    # Report Metadata
    # ==========================================================

    def _rebuild_from_persistence(
        self,
        report_id: int,
        user_id: int | None,
    ) -> tuple[StructuredReport | None, Any | None, dict[str, Any] | None]:
        """
        Rebuild report `report_id` from its persisted rows (P2-03).

        The AI job of a run stores the run's ReportingReport (P2-01), and the
        AI report and its lineage are in `ai_reports`. Returns no report when
        nothing was persisted for this id; the caller answers 404.
        """
        from src.database.repositories.ai_job_repository import AIJobRepository
        from src.reporting.reporting_report import ReportingReport

        service = self._application.ai_job_service
        with service._session() as conn:
            repo = AIJobRepository(conn)
            job = repo.get_by_report_id(report_id, user_id=user_id)
            payload = repo.get_report_payload(job.job_id) if job is not None else None
        if job is None or not payload:
            return None, None, None

        structured_report = ReportingReport.from_payload(payload).report
        job_data = service.get_job_with_report(job.job_id, user_id=user_id) or {}
        ai_report = job_data.get("ai_report")
        ai_dict = ai_report if isinstance(ai_report, dict) else {}
        lineage = {
            "pipeline_run_id": job.pipeline_run_id,
            "source_version_id": ai_dict.get("source_version_id"),
            "cleaned_version_id": ai_dict.get("cleaned_version_id"),
            "cleaning_execution_id": ai_dict.get("cleaning_execution_id"),
            "context_schema_version": "1.0",
        }
        return structured_report, ai_report, lineage

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
                "report_id": None,
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
            # The id the export-by-id routes take (P2-03).
            "report_id": getattr(result, "report_id", None),
            "report": public_report_dict(reporting_report.to_dict()),
            "ai_report": ai_report_dict,
            "execution_time": result.execution_time,
            "output_path": public_artifact_name(result.output_path),
        }

    # ==========================================================
    # Export Operations
    # ==========================================================

    @staticmethod
    def _ephemeral_export_path(suffix: str) -> Path:
        """
        A fresh file for one export request (SEC-12).

        Exports without an explicit target used to share the exporter's
        default file, so a concurrent export by another user could overwrite
        it before this response was streamed. The route deletes the file once
        the response has been sent.
        """
        directory = Path(config.REPORT_OUTPUT_DIRECTORY) / "exports"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"export_{uuid.uuid4().hex}{suffix}"

    def _owned_report_record(
        self,
        report_id: int,
        user_id: int | None,
    ) -> dict[str, Any] | None:
        """
        Return the report row only if it exists AND belongs to `user_id`.

        Fails closed. This used to read `application.persistence._report_repository`
        through `getattr(..., None)` and skip the check when that was missing -
        which it became once persistence moved to per-request sessions, so any
        user could export any report by id.
        """
        if user_id is None:
            return None
        with self._application.persistence_session() as persistence:
            return persistence._report_repository.get_by_id(report_id, user_id=user_id)

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
            record = self._owned_report_record(report_id, user_id)
            if record is None:
                return {
                    "success": False,
                    "message": "Report not found or access denied.",
                }

        structured_report, ai_report, lineage = self._resolve_context_and_report(
            user_id=user_id,
            report_id=report_id,
        )

        if structured_report is None and report_id is not None:
            # A report from before job inputs were persisted: its own run file,
            # if it is inside the report directory (I6). Never another report.
            disk_path = _contained_report_file(record.get("report_path"))
            if disk_path is not None:
                return {
                    "success": True,
                    "message": "Text report exported successfully.",
                    "export_path": str(disk_path.resolve()),
                    "path": str(disk_path.resolve()),
                    "filename": disk_path.name,
                    "mime_type": "text/plain",
                }

        if structured_report is None:
            return {
                "success": False,
                "message": "No generated report was found.",
            }

        target_path = output_path
        if target_path is None and filename is not None:
            target_path = config.REPORT_OUTPUT_DIRECTORY / filename
        ephemeral = target_path is None
        if ephemeral:
            target_path = self._ephemeral_export_path(".txt")

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
            "filename": DEFAULT_REPORT_FILENAME if ephemeral else p.name,
            "mime_type": "text/plain",
            "ephemeral": ephemeral,
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
        if report_id is not None and self._owned_report_record(report_id, user_id) is None:
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
        ephemeral = target_path is None
        if ephemeral:
            target_path = self._ephemeral_export_path(".pdf")

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
            "filename": DEFAULT_PDF_REPORT_FILENAME if ephemeral else p.name,
            "mime_type": "application/pdf",
            "ephemeral": ephemeral,
        }
