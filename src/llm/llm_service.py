"""
Enterprise LLM service.

Provides a high-level interface for AI engines while managing
provider selection, retries, logging and execution timing.
"""

import time

from src.core import config
from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.llm_factory import LLMFactory


class LLMService:
    """
    Enterprise wrapper around language model providers.
    """

    def __init__(
        self,
        llm: BaseLLM | None = None,
    ) -> None:
        """
        Initialise the language model service.
        """

        self._llm = llm or LLMFactory.create()

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate text from the configured provider.
        """

        last_exception = None

        for attempt in range(
            config.AI_MAX_RETRIES
        ):

            start_time = time.perf_counter()

            try:

                logger.info(
                    "LLM request (%d/%d)",
                    attempt + 1,
                    config.AI_MAX_RETRIES,
                )

                response = self._llm.generate(
                    prompt
                )

                execution_time = (
                    time.perf_counter()
                    - start_time
                )

                logger.info(
                    "LLM response received (%.3f s)",
                    execution_time,
                )

                if not response.strip():
                    raise ValueError(
                        "LLM returned an empty response."
                    )

                return response

            except Exception as exc:

                last_exception = exc

                logger.warning(
                    "LLM request failed (%d/%d): %s",
                    attempt + 1,
                    config.AI_MAX_RETRIES,
                    exc,
                )

        raise RuntimeError(
            "LLM request failed after "
            f"{config.AI_MAX_RETRIES} attempts."
        ) from last_exception