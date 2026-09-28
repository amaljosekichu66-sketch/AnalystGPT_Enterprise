"""
AI Manager Module for AnalystGPT Enterprise.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
Sprint 14 Phase 4 — AI Data Context & Analytical Integrity
Sprint 14 Remediation & Phase 2 Quality Gate — Evidence-Based Confidence and Explicit Structured Sections.

Orchestrates the AI insight generation pipeline via UnifiedReportEngine.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from src.ai.ai_report import AIReport
from src.ai.ai_result import AIResult
from src.ai.confidence_evaluator import compute_evidence_confidence
from src.ai.insight_validator import validate_insight_text
from src.ai.unified_report_engine import AISections, UnifiedReportEngine
from src.core import config
from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.llm_factory import LLMFactory
from src.reporting.reporting_report import ReportingReport

_LOG_SEPARATOR = "=" * 60
_PROMPT_COUNT = 1


class AIManager:
    """
    Coordinates the execution of the AI Insight Engine.
    """

    def __init__(self, llm: BaseLLM | None = None) -> None:
        logger.info("Initialising AI Manager...")
        self._llm = llm or LLMFactory.create()
        self._engine = UnifiedReportEngine(self._llm)

    @property
    def llm(self) -> BaseLLM:
        return self._llm

    def generate_ai_report(
        self,
        reporting_report: ReportingReport | None,
        data_context: Any | None = None,
    ) -> AIResult:
        """
        Generate a complete AI business insight report.
        """
        logger.info(_LOG_SEPARATOR)
        logger.info("Starting AI Insight Engine...")
        logger.info(_LOG_SEPARATOR)

        start_time = time.perf_counter()

        try:
            if reporting_report is None and data_context is None:
                raise ValueError("reporting_report cannot be None.")

            sections = self._generate_sections(
                reporting_report,
                data_context=data_context,
            )

            engine_time = time.perf_counter() - start_time
            build_start = time.perf_counter()

            report = self._build_report(
                sections,
                engine_time,
                reporting_report=reporting_report,
                data_context=data_context,
            )

            build_time = time.perf_counter() - build_start
            total_time = time.perf_counter() - start_time

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
            total_time = time.perf_counter() - start_time
            self._log_failure(
                exc,
                total_time,
            )
            return self._failure_result(
                exc,
                total_time,
            )

    def _generate_sections(
        self,
        reporting_report: ReportingReport | None,
        data_context: Any | None = None,
    ) -> AISections:
        logger.info("Calling UnifiedReportEngine.generate()...")
        if data_context is not None:
            sections = self._engine.generate(
                reporting_report,
                data_context=data_context,
            )
        else:
            sections = self._engine.generate(
                reporting_report,
            )

        if not isinstance(sections, AISections):
            logger.error(
                "UnifiedReportEngine returned invalid type: %s",
                type(sections).__name__,
            )
            raise TypeError("UnifiedReportEngine must return AISections.")

        for field_name in ("executive_summary", "recommendations", "explanations", "narrative"):
            if getattr(sections, field_name, None) is None:
                raise ValueError(f"Section '{field_name}' is None.")

        logger.info(_LOG_SEPARATOR)
        logger.info("Generated AI sections successfully.")
        logger.info("Executive Summary : %d chars", len(sections.executive_summary or ""))
        logger.info("Recommendations   : %d items", len(sections.recommendations or []))
        logger.info("Explanations      : %d items", len(sections.explanations or []))
        logger.info("Narrative         : %d chars", len(sections.narrative or ""))

        return sections

    def _build_report(
        self,
        sections: AISections,
        execution_time: float,
        reporting_report: ReportingReport | None = None,
        data_context: Any | None = None,
    ) -> AIReport:
        logger.info("Building AIReport object...")

        expls = sections.explanations or []
        recs = sections.recommendations or []

        # Extract analytics dictionary if present
        analytics_data: dict[str, Any] = {}
        if (
            reporting_report is not None
            and hasattr(reporting_report, "report")
            and hasattr(reporting_report.report, "analytics")
        ):
            raw_analytics = reporting_report.report.analytics
            if isinstance(raw_analytics, dict):
                analytics_data = raw_analytics

        # Evidence-based confidence evaluation
        confidence = compute_evidence_confidence(analytics_data, data_context=data_context)

        # Explicit structured fields without keyword matching
        key_findings = list(expls)
        actions = list(recs)
        opportunities = list(recs)
        business_implications = expls[:2] if expls else []

        # Dataset-grounded risks & limitations
        risks: list[str] = []
        if data_context and hasattr(data_context, "source") and data_context.source.total_missing > 0:
            risks.append(
                f"Source dataset contained {data_context.source.total_missing} missing cells requiring pre-processing governance."
            )
        else:
            risks.append("Dataset dimension distribution should be monitored for operational concentrations.")

        limitations: list[str] = [
            "Observational records describe correlation and distribution; causal conclusions require experimental validation.",
        ]
        desc = analytics_data.get("descriptive_statistics", {})
        if desc.get("numeric_column_count", 0) == 0:
            limitations.append(
                "The available dataset does not contain governed numerical measure columns; revenue/financial forecasting is unavailable."
            )

        # Validate generated prose against the deterministic analytics. Findings
        # are surfaced rather than raised: on local CPU inference a regeneration
        # costs minutes, so a flagged report is more useful than no report.
        validation_findings = validate_insight_text(
            "\n".join(
                [
                    sections.executive_summary or "",
                    sections.narrative or "",
                    *(recs or []),
                    *(expls or []),
                ]
            ),
            analytics_data,
        )

        for finding in validation_findings:
            logger.warning("AI insight validation: %s", finding)

        if validation_findings:
            limitations.append(
                f"Automated validation flagged {len(validation_findings)} "
                "statement(s) as unsupported by the deterministic analytics:"
            )
            limitations.extend(validation_findings)

        report = AIReport(
            executive_summary=sections.executive_summary,
            recommendations=recs,
            explanations=expls,
            narrative=sections.narrative,
            model=self._llm.model,
            provider=config.LLM_PROVIDER,
            execution_time=execution_time,
            prompt_count=_PROMPT_COUNT,
            generated_at=datetime.now(UTC),
            key_findings=key_findings,
            business_implications=business_implications,
            risks=risks,
            opportunities=opportunities,
            actions=actions,
            limitations=limitations,
            confidence=confidence,
        )

        return report

    def _success_result(
        self,
        report: AIReport,
        execution_time: float,
    ) -> AIResult:
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
        return AIResult(
            success=False,
            ai_report=None,
            execution_time=execution_time,
            error=error,
        )

    def _log_success(
        self,
        total_time: float,
        engine_time: float,
        build_time: float,
        report: AIReport,
    ) -> None:
        logger.info(_LOG_SEPARATOR)
        logger.info("AI Insight Engine completed successfully.")
        logger.info("Provider : %s", report.provider)
        logger.info("Model    : %s", report.model)
        logger.info("Engine Generation : %.3f s", engine_time)
        logger.info("Report Build      : %.3f s", build_time)
        logger.info("Total Time        : %.3f s", total_time)
        logger.info("Prompt Count      : %d", report.prompt_count)
        logger.info("Recommendations   : %d", len(report.recommendations))
        logger.info("Explanations      : %d", len(report.explanations))
        logger.info("Narrative Length  : %d", len(report.narrative))
        logger.info("Executive Summary Length : %d", len(report.executive_summary))
        logger.info("Assigned Confidence : %s", report.confidence)
        logger.info(_LOG_SEPARATOR)

    def _log_failure(
        self,
        error: Exception,
        total_time: float,
    ) -> None:
        logger.error(_LOG_SEPARATOR)
        logger.error("AI Insight Engine failed.")
        logger.error("Error      : %s", error)
        logger.error("Total Time : %.3f s", total_time)
        logger.error(_LOG_SEPARATOR)
