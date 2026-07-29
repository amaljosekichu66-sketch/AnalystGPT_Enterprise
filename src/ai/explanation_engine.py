"""
Explanation generation engine.

Generates explainable analytics using the configured
Large Language Model provider.
"""

import time

from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.prompt_builder import PromptBuilder
from src.reporting.reporting_report import ReportingReport


class ExplanationEngine:
    """
    Generates explainable business interpretations
    of analytical results.
    """

    def __init__(
        self,
        llm: BaseLLM,
    ) -> None:
        """
        Initialise the explanation engine.

        Parameters
        ----------
        llm : BaseLLM
            Language model implementation.
        """

        self._llm = llm

    def generate_explanations(
        self,
        reporting_report: ReportingReport,
    ) -> list[str]:
        """
        Generate explainable analytics.

        Parameters
        ----------
        reporting_report : ReportingReport
            Reporting module output.

        Returns
        -------
        list[str]
            Business-friendly explanations.
        """

        logger.info(
            "Generating explainable analytics..."
        )

        start_time = time.perf_counter()

        try:

            prompt = PromptBuilder.explanations(
                reporting_report
            )

            response = self._llm.generate(
                prompt
            )

            explanations = [
                line.strip("-•* ").strip()
                for line in response.splitlines()
                if line.strip()
            ]

            if not explanations:
                raise ValueError(
                    "LLM returned no explanations."
                )

            execution_time = (
                time.perf_counter()
                - start_time
            )

            logger.info(
                "Generated %d explanations "
                "(%.3f seconds).",
                len(explanations),
                execution_time,
            )

            return explanations

        except Exception:

            logger.exception(
                "Explanation generation failed."
            )

            raise