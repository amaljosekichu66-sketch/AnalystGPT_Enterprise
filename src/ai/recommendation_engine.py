"""
Recommendation generation engine.

Generates actionable business recommendations using the configured
Large Language Model provider.
"""

import time

from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.prompt_builder import PromptBuilder
from src.reporting.reporting_report import ReportingReport


class RecommendationEngine:
    """
    Generates actionable business recommendations.
    """

    def __init__(
        self,
        llm: BaseLLM,
    ) -> None:

        self._llm = llm

    def generate_recommendations(
        self,
        reporting_report: ReportingReport,
    ) -> list[str]:

        logger.info("Generating recommendations...")

        start_time = time.perf_counter()

        try:

            prompt = PromptBuilder.recommendations(reporting_report)

            response = self._llm.generate(prompt)

            recommendations = [line.strip("-•* ").strip() for line in response.splitlines() if line.strip()]

            if not recommendations:
                raise ValueError("LLM returned no recommendations.")

            logger.info(
                "Generated %d recommendations " "(%.3f seconds).",
                len(recommendations),
                time.perf_counter() - start_time,
            )

            return recommendations

        except Exception:

            logger.exception("Recommendation generation failed.")

            raise
