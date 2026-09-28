"""
Dashboard orchestrator for AnalystGPT Enterprise.

Coordinates dashboard information for API consumers.

Responsibilities
----------------
- Execute the analytics pipeline.
- Aggregate reporting and AI information.
- Return structured dashboard data.

This module contains orchestration logic only.
"""

from __future__ import annotations

from typing import Any

from src.application.app import Application
from src.application.pipeline_result import PipelineResult
from src.core.constants import (
    APP_NAME,
    APP_VERSION,
)


class DashboardOrchestrator:
    """
    Coordinates dashboard information.

    This orchestrator is stateless and delegates execution to a shared
    Application instance. The Application lifecycle is managed externally.
    """

    def __init__(
        self,
        application: Application,
    ) -> None:
        """
        Initialise the orchestrator with a shared Application instance.

        Parameters
        ----------
        application : Application
            The shared Application instance. Must not be None.
        """
        self._application = application

    # ==========================================================
    # Dashboard
    # ==========================================================

    def get_dashboard(
        self,
        dataset: str,
        user_context: Any | None = None,
    ) -> dict[str, Any]:
        """
        Execute the analytics pipeline and return dashboard information.

        Uses the shared Application's cached pipeline result if available,
        otherwise runs the pipeline.

        Parameters
        ----------
        dataset : str
            Path to the dataset.
        user_context : UserContext | None
            Optional authenticated security context.

        Returns
        -------
        dict[str, Any]
            The dashboard data.

        Raises
        ------
        ValueError
            If dataset is empty.
        """
        if not dataset:
            raise ValueError("Dataset path must not be empty.")

        # Use cached or run new pipeline
        try:
            result = self._application.get_or_run(
                input_path=dataset,
                user_context=user_context,
            )
        except TypeError:
            result = self._application.get_or_run(
                input_path=dataset,
            )

        return self._build_dashboard(
            result,
            user_context=user_context,
        )

    # ==========================================================
    # Status
    # ==========================================================

    def get_status(
        self,
    ) -> dict[str, Any]:
        """
        Return lightweight application status.
        """

        return {
            "application": APP_NAME,
            "version": APP_VERSION,
            "status": "Ready",
        }

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _build_ai_report(
        self,
        pipeline_result: PipelineResult,
        user_context: Any | None = None,
    ) -> dict[str, Any] | None:
        """
        Convert the AI report into a serialisable dictionary.
        """

        if pipeline_result.pipeline_report is not None and pipeline_result.pipeline_report.ai_report is not None:
            ai_report = pipeline_result.pipeline_report.ai_report

            return {
                "executive_summary": ai_report.executive_summary,
                "recommendations": ai_report.recommendations,
                "explanations": ai_report.explanations,
                "narrative": ai_report.narrative,
                "model": ai_report.model,
                "provider": ai_report.provider,
                "execution_time": ai_report.execution_time,
            }

        # Check database if job exists and has completed
        job_id = getattr(pipeline_result, "ai_job_id", None)
        if job_id is not None:
            user_id = (
                user_context.user_id if user_context and getattr(user_context, "is_authenticated", False) else None
            )
            try:
                ai_job_data = self._application.ai_job_service.get_job_with_report(
                    job_id=job_id,
                    user_id=user_id,
                )
                if ai_job_data is not None and ai_job_data.get("ai_report") is not None:
                    rep = ai_job_data["ai_report"]
                    return {
                        "executive_summary": rep.get("executive_summary", ""),
                        "recommendations": rep.get("recommendations", []),
                        "explanations": rep.get("explanations", []),
                        "narrative": rep.get("narrative", ""),
                        "model": rep.get("model", ""),
                        "provider": rep.get("provider", ""),
                        "execution_time": rep.get("execution_time", 0.0),
                    }
            except Exception:
                pass

        return None

    def _build_dashboard(
        self,
        result: PipelineResult,
        user_context: Any | None = None,
    ) -> dict[str, Any]:
        """
        Convert a PipelineResult into dashboard data.
        """

        reporting_report = None

        if result.pipeline_report is not None:
            reporting_report = result.pipeline_report.reporting_report

        return {
            "application": {
                "name": APP_NAME,
                "version": APP_VERSION,
                "status": ("Ready" if result.success else "Failed"),
            },
            "pipeline": {
                "success": result.success,
                "execution_time": result.execution_time,
                "output_path": result.output_path,
                "ai_job_id": getattr(result, "ai_job_id", None),
                "ai_job_status": getattr(result, "ai_job_status", None),
            },
            "report": (reporting_report.to_dict() if reporting_report is not None else {}),
            "ai_report": self._build_ai_report(
                result,
                user_context=user_context,
            ),
        }
