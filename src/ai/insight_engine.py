"""
Insight generation engine.

The InsightEngine is responsible for analysing a ReportingReport and
producing high-level business observations.

Responsibilities
----------------
- Analyse reporting outputs
- Identify significant findings
- Generate business observations

Non-Responsibilities
--------------------
- Explain statistical concepts
- Produce executive narratives
- Manage LLM communication details
"""

from typing import List

from src.llm.llm_factory import LLMFactory
from src.llm.prompt_builder import PromptBuilder
from src.reporting.reporting_report import ReportingReport


class InsightEngine:
    """
    Generates business insights from a ReportingReport.

    The engine delegates prompt generation to PromptBuilder and
    language-model interaction to the configured LLM provider.
    """

    def __init__(self) -> None:
        """
        Initialise the configured language model.
        """
        self._llm = LLMFactory.create()

    def generate_insights(
        self,
        reporting_report: ReportingReport,
    ) -> List[str]:
        """
        Generate business insights from a reporting report.

        Parameters
        ----------
        reporting_report : ReportingReport
            Reporting module output.

        Returns
        -------
        List[str]
            Collection of generated business insights.
        """

        prompt = PromptBuilder.recommendations(reporting_report)

        response = self._llm.generate(prompt)

        insights = []

        for line in response.splitlines():

            line = line.strip()

            if not line:
                continue

            # Remove common numbering prefixes.
            line = line.lstrip("-•* ")

            if "." in line[:4]:
                _, remainder = line.split(".", 1)
                line = remainder.strip()

            if line:
                insights.append(line)

        return insights
