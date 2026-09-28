"""
AI orchestration layer.

Coordinates execution of the complete AI subsystem while
keeping the Application layer lightweight.
"""

import time

from src.ai.ai_manager import AIManager
from src.ai.ai_result import AIResult
from src.core.logger import logger
from src.reporting.reporting_report import ReportingReport


class AIOrchestrator:
    """
    Executes the complete AI subsystem.
    """

    def __init__(self) -> None:
        """
        Initialise AI manager.
        """

        self._manager = AIManager()

    def execute(
        self,
        reporting_report: ReportingReport,
    ) -> AIResult:
        """
        Execute the complete AI pipeline.
        """

        logger.info("-" * 60)
        logger.info("AI INSIGHT STAGE")
        logger.info("-" * 60)

        start = time.perf_counter()

        result = self._manager.generate_ai_report(reporting_report)

        logger.info(
            "AI execution completed in %.3f seconds.",
            time.perf_counter() - start,
        )

        return result
