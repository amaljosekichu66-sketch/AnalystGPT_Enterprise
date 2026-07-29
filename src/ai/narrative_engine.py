"""
Narrative generation engine.

Generates publication-ready business narratives using the configured
Large Language Model provider.
"""

import time

from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.prompt_builder import PromptBuilder
from src.reporting.reporting_report import ReportingReport


class NarrativeEngine:
    """
    Generates enterprise business narratives.
    """

    def __init__(
        self,
        llm: BaseLLM,
    ) -> None:

        self._llm = llm

    def generate_narrative(
        self,
        reporting_report: ReportingReport,
    ) -> str:

        logger.info(
            "Generating narrative..."
        )

        start_time = time.perf_counter()

        try:

            prompt = PromptBuilder.narrative(
                reporting_report
            )

            narrative = self._llm.generate(
                prompt
            ).strip()

            if not narrative:
                raise ValueError(
                    "LLM returned an empty narrative."
                )

            logger.info(
                "Narrative generated successfully "
                "(%.3f seconds).",
                time.perf_counter()
                - start_time,
            )

            return narrative

        except Exception:

            logger.exception(
                "Narrative generation failed."
            )

            raise