"""
AI Insight Engine manager.

Coordinates execution of the AI subsystem.
"""

from __future__ import annotations

import time
from dataclasses import fields
from datetime import UTC, datetime

from src.ai.ai_report import AIReport
from src.ai.ai_result import AIResult
from src.ai.unified_report_engine import AISections, UnifiedReportEngine
from src.core import config
from src.core.logger import logger
from src.llm.llm_factory import LLMFactory
from src.reporting.reporting_report import ReportingReport


# ==========================================================
# Constants
# ==========================================================

_LOG_SEPARATOR = "=" * 60
_PROMPT_COUNT = 1


class AIManager:
    """
    Coordinates execution of the AI subsystem.

    This manager encapsulates the complete AI insight generation
    pipeline, including LLM initialization, report generation,
    validation, logging, and result packaging.
    """

    def __init__(
        self,
    ) -> None:
        """Initialise the AI subsystem."""
        logger.info("Initialising AI Manager...")

        self._llm = LLMFactory.create()

        logger.info(
            "LLM Initialised | Provider=%s | Model=%s",
            config.LLM_PROVIDER,
            self._llm.model,
        )

        self._engine = UnifiedReportEngine(
            self._llm,
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def generate_ai_report(
        self,
        reporting_report: ReportingReport | None,
    ) -> AIResult:
        """
        Generate the complete AI report from a reporting result.

        Exceptions during generation are captured and returned in
        a failed AIResult so pipeline execution can continue.
        """
        if reporting_report is None:
            return self._failure_result(
                ValueError("reporting_report cannot be None."),
                0.0,
            )

        self._log_start()

        start_time = time.perf_counter()

        try:
            sections = self._generate_sections(
                reporting_report,
            )

            engine_time = (
                time.perf_counter() - start_time
            )

            build_start = time.perf_counter()

            report = self._build_report(
                sections,
                engine_time,
            )

            build_time = (
                time.perf_counter() - build_start
            )

            total_time = (
                time.perf_counter() - start_time
            )

            self._log_success(
                total_time,
                engine_time,
                build_time,
                report,
            )

            return self._success_result(
                report,
                total_time,
            )

        except Exception as exc:
            total_time = (
                time.perf_counter() - start_time
            )

            self._log_failure(
                exc,
                total_time,
            )

            return self._failure_result(
                exc,
                total_time,
            )

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _generate_sections(
        self,
        reporting_report: ReportingReport,
    ) -> AISections:
        """
        Generate and validate all AI report sections.

        Raises
        ------
        TypeError
            If the engine does not return AISections.
        ValueError
            If a required section is None.
        """
        logger.info(
            "Generating AI report using model: %s",
            self._llm.model,
        )

        sections = self._engine.generate(
            reporting_report,
        )

        if not isinstance(sections, AISections):
            raise TypeError(
                "UnifiedReportEngine must return AISections. "
                f"Got {type(sections).__name__} instead."
            )

        for section_field in fields(sections):
            value = getattr(
                sections,
                section_field.name,
            )

            if value is None:
                raise ValueError(
                    f"Section '{section_field.name}' is None."
                )

        logger.info("Generated AI sections successfully.")
        logger.info(
            "Executive Summary : %d chars",
            len(sections.executive_summary),
        )
        logger.info(
            "Recommendations   : %d items",
            len(sections.recommendations),
        )
        logger.info(
            "Explanations      : %d items",
            len(sections.explanations),
        )
        logger.info(
            "Narrative         : %d chars",
            len(sections.narrative),
        )

        return sections

    def _build_report(
        self,
        sections: AISections,
        execution_time: float,
    ) -> AIReport:
        """Build an immutable AIReport from generated sections."""
        logger.info("Building AIReport object...")

        report = AIReport(
            executive_summary=sections.executive_summary,
            recommendations=sections.recommendations,
            explanations=sections.explanations,
            narrative=sections.narrative,
            model=self._llm.model,
            provider=config.LLM_PROVIDER,
            execution_time=execution_time,
            prompt_count=_PROMPT_COUNT,
            # Keep this as datetime, not .isoformat().
            # AIReport.to_dict() performs serialization.
            generated_at=datetime.now(UTC),
        )

        if not report.executive_summary.strip():
            logger.warning("Executive summary is empty.")

        if not report.narrative.strip():
            logger.warning("Narrative is empty.")

        if not report.recommendations:
            logger.warning("No recommendations generated.")

        if not report.explanations:
            logger.warning("No explanations generated.")

        return report

    def _success_result(
        self,
        report: AIReport,
        execution_time: float,
    ) -> AIResult:
        """Build a successful AIResult."""
        return AIResult(
            success=True,
            ai_report=report,
            execution_time=execution_time,
            error=None,
        )

    def _failure_result(
        self,
        error: Exception,
        execution_time: float,
    ) -> AIResult:
        """Build a failed AIResult."""
        return AIResult(
            success=False,
            ai_report=None,
            execution_time=execution_time,
            error=error,
        )

    # ==========================================================
    # Logging
    # ==========================================================

    def _log_start(
        self,
    ) -> None:
        """Log AI engine startup information."""
        logger.info(_LOG_SEPARATOR)
        logger.info("STARTING AI INSIGHT ENGINE")
        logger.info("Provider : %s", config.LLM_PROVIDER)
        logger.info("Model    : %s", self._llm.model)
        logger.info(_LOG_SEPARATOR)

    def _log_success(
        self,
        total_time: float,
        engine_time: float,
        build_time: float,
        report: AIReport,
    ) -> None:
        """Log successful AI generation metrics."""
        logger.info(_LOG_SEPARATOR)
        logger.info(
            "AI Insight Engine completed successfully."
        )
        logger.info("Provider : %s", config.LLM_PROVIDER)
        logger.info("Model    : %s", self._llm.model)
        logger.info(
            "Engine Generation : %.3f s",
            engine_time,
        )
        logger.info(
            "Report Build      : %.3f s",
            build_time,
        )
        logger.info(
            "Total Time        : %.3f s",
            total_time,
        )
        logger.info(
            "Prompt Count      : %d",
            report.prompt_count,
        )
        logger.info(
            "Recommendations   : %d",
            len(report.recommendations),
        )
        logger.info(
            "Explanations      : %d",
            len(report.explanations),
        )
        logger.info(
            "Narrative Length  : %d",
            len(report.narrative),
        )
        logger.info(
            "Executive Summary Length : %d",
            len(report.executive_summary),
        )
        logger.info(_LOG_SEPARATOR)

    def _log_failure(
        self,
        error: Exception,
        execution_time: float,
    ) -> None:
        """Log AI generation failure details."""
        logger.exception(
            "AI generation failed "
            "| Provider=%s "
            "| Model=%s "
            "| Time=%.3fs",
            config.LLM_PROVIDER,
            self._llm.model,
            execution_time,
        )
        logger.error(
            "Exception Type : %s",
            type(error).__name__,
        )
        logger.error(
            "Exception      : %s",
            error,
        )
        logger.info(_LOG_SEPARATOR)