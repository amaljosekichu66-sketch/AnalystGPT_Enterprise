"""
Executive summary generation engine.

Generates concise executive summaries using the configured
Large Language Model provider.
"""

from __future__ import annotations

import time

from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.prompt_builder import PromptBuilder
from src.reporting.reporting_report import ReportingReport


class ExecutiveSummaryEngine:
    """
    Generates executive summaries from reporting results.
    """

    def __init__(
        self,
        llm: BaseLLM,
    ) -> None:
        """
        Initialise the language model.
        """

        self._llm = llm

    def generate_summary(
        self,
        reporting_report: ReportingReport,
    ) -> str:
        """
        Generate an executive summary.
        """

        logger.info("=" * 60)
        logger.info("EXECUTIVE SUMMARY ENGINE")
        logger.info("=" * 60)

        start_time = time.perf_counter()

        try:

            logger.info("Building executive summary prompt...")

            prompt = PromptBuilder.executive_summary(reporting_report)

            logger.info("Prompt built successfully.")

            logger.info(
                "Prompt Length : %d characters",
                len(prompt),
            )

            logger.info("Calling LLM.generate()...")

            summary = self._llm.generate(prompt)

            logger.info("LLM.generate() returned.")

            summary = summary.strip()

            logger.info(
                "Summary Length : %d characters",
                len(summary),
            )

            if not summary:

                raise ValueError("LLM returned an empty summary.")

            elapsed = time.perf_counter() - start_time

            logger.info(
                "Executive summary generated successfully " "(%.3f seconds).",
                elapsed,
            )

            logger.info("=" * 60)

            return summary

        except Exception as exc:

            logger.exception("Executive summary generation failed.")

            logger.error(
                "Exception Type : %s",
                type(exc).__name__,
            )

            logger.error(
                "Exception      : %s",
                exc,
            )

            raise
