"""
Ollama Large Language Model client.

Provides a concrete implementation of the BaseLLM interface using
a locally running Ollama server.
"""

from __future__ import annotations

import time

from ollama import Client
from ollama import ResponseError

from src.core import config
from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.response_parser import ResponseParser


class OllamaClient(BaseLLM):
    """
    Concrete implementation of BaseLLM using Ollama.
    """

    def __init__(
        self,
    ) -> None:

        self._model = config.OLLAMA_MODEL

        self._client = Client(
            host=config.OLLAMA_HOST,
            timeout=config.AI_TIMEOUT,
        )

        logger.info(
            "Connected to Ollama Host: %s",
            config.OLLAMA_HOST,
        )

        logger.info("Provider: Ollama")

        logger.info(
            (
                "LLM Configuration | "
                "model=%s | "
                "temperature=%.2f | "
                "max_tokens=%d | "
                "top_p=%.2f | "
                "keep_alive=%s"
            ),
            self._model,
            config.AI_TEMPERATURE,
            config.AI_MAX_TOKENS,
            config.AI_TOP_P,
            config.OLLAMA_KEEP_ALIVE,
        )

    # ==========================================================
    # Properties
    # ==========================================================

    @property
    def model(
        self,
    ) -> str:
        """
        Return the configured model.
        """

        return self._model

    # ==========================================================
    # Generation
    # ==========================================================

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from Ollama.
        """

        logger.info("=" * 60)
        logger.info("OLLAMA CLIENT")
        logger.info("=" * 60)

        logger.info(
            "Model: %s",
            self._model,
        )

        logger.info(
            "Prompt Length: %d characters",
            len(prompt),
        )

        logger.info(
            "Prompt Size: %.2f KB",
            len(prompt.encode("utf-8")) / 1024,
        )

        start_time = time.perf_counter()

        try:

            logger.info(
                "Sending request to Ollama..."
            )

            api_start = time.perf_counter()

            response = self._client.generate(
                model=self._model,
                prompt=prompt,
                options={
                    "temperature": config.AI_TEMPERATURE,
                    "top_p": config.AI_TOP_P,
                    "num_predict": config.AI_MAX_TOKENS,
                    "num_ctx": getattr(
                        config,
                        "AI_CONTEXT_WINDOW",
                        4096,
                    ),  # fallback if config missing
                    "repeat_penalty": 1.05,
                    "stop": [
                        "END RESPONSE",
                    ],
                },
                keep_alive=config.OLLAMA_KEEP_ALIVE,
            )

            api_time = (
                time.perf_counter()
                - api_start
            )

            logger.info(
                "Ollama API completed in %.2f seconds",
                api_time,
            )

            if response is None:

                raise RuntimeError(
                    "Ollama returned no response."
                )

            content = (
                response.get(
                    "response",
                    "",
                )
                or ""
            )

            logger.info(
                "Raw Response Length: %d",
                len(content),
            )

            logger.debug(
                "Raw Ollama Response:\n%s",
                content,
            )

            parsed = ResponseParser.parse(
                content
            )

            if not parsed:

                raise RuntimeError(
                    "Parsed response is empty."
                )

            word_count = len(
                parsed.split()
            )

            logger.info(
                "Approx Word Count: %d",
                word_count,
            )

            if api_time > 0:

                logger.info(
                    "Approx Throughput: %.2f words/sec",
                    word_count / api_time,
                )

            logger.info(
                "Total generate() time: %.2f seconds",
                time.perf_counter()
                - start_time,
            )

            return parsed

        except ResponseError:

            logger.exception(
                "Ollama server returned an error."
            )

            raise

        except TimeoutError:

            logger.exception(
                "Ollama request timed out."
            )

            raise

        except Exception:

            logger.exception(
                "Unexpected Ollama client error."
            )

            raise