"""
Ollama Large Language Model client.

Provides a concrete implementation of the BaseLLM interface using
a locally running Ollama server.
"""

from __future__ import annotations

import time

from ollama import Client, ResponseError

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
    # Context budget
    # ==========================================================

    #: Characters per token for English prose. Measured on this deployment's
    #: real prompts: 17,923 characters tokenised to 4,653 tokens (3.85).
    #: Rounded down, so the estimate errs towards over-reporting the size.
    _CHARS_PER_TOKEN = 3.8

    def _warn_if_context_window_too_small(self, prompt: str) -> None:
        """
        Log loudly when the prompt plus the response cannot fit `num_ctx`.

        An overflow is silent at the Ollama layer: llama.cpp simply discards
        the oldest tokens, which is the HEAD of the prompt - the role, the
        objective and the analytical integrity rules. The model then answers
        without the constraints it was supposed to be bound by, and the
        truncated tail shows up much later as "Missing required AI sections",
        which points the reader at the model instead of the budget.

        This does not raise. The request may still produce a usable report,
        and refusing it outright would turn a degraded result into no result.
        It does make the cause findable.
        """
        context_window = getattr(config, "AI_CONTEXT_WINDOW", 4096)
        max_tokens = getattr(config, "AI_MAX_TOKENS", 1024)

        estimated_prompt_tokens = int(len(prompt) / self._CHARS_PER_TOKEN)
        required = estimated_prompt_tokens + max_tokens

        if required <= context_window:
            logger.info(
                "Context budget OK | prompt~%d + max_tokens=%d = %d of num_ctx=%d",
                estimated_prompt_tokens,
                max_tokens,
                required,
                context_window,
            )
            return

        logger.error(
            "CONTEXT WINDOW OVERFLOW | prompt~%d tokens + AI_MAX_TOKENS=%d = %d, "
            "but AI_CONTEXT_WINDOW=%d (short by %d). Ollama will silently drop "
            "the OLDEST tokens - the role and the analytical integrity rules at "
            "the head of the prompt - and may run out of room before the final "
            "section. Raise AI_CONTEXT_WINDOW to at least %d, or reduce "
            "AI_MAX_TOKENS / the serialised report.",
            estimated_prompt_tokens,
            max_tokens,
            required,
            context_window,
            required - context_window,
            1 << (required - 1).bit_length(),
        )

    @staticmethod
    def _warn_if_output_budget_too_small() -> None:
        """
        Log loudly when `AI_MAX_TOKENS` is below the prose the prompt requests.

        The prompt states per-section word limits. When the token budget is
        smaller than those limits imply, Ollama stops at `num_predict` and
        reports `done_reason: "length"` - which the application never inspects.
        The response simply ends mid-sentence, and if the cut lands before the
        final heading, `_parse_sections` reports "Missing required AI sections"
        and blames the model.

        Measured on this deployment with `AI_MAX_TOKENS=600`: the prompt asks
        for 680 words (~904 tokens), generation stopped at exactly 600 tokens,
        `done_reason: length`, and the text ended without punctuation.

        The counterpart to `_warn_if_context_window_too_small`: the context
        window bounds prompt + response, this bounds the response alone. Like
        that guard, it reports and continues rather than raising.
        """
        from src.llm.prompt_builder import (
            OUTPUT_BUDGET_HEADROOM,
            estimated_output_tokens,
        )

        max_tokens = getattr(config, "AI_MAX_TOKENS", 1024)
        requested = estimated_output_tokens()
        ceiling = max_tokens * OUTPUT_BUDGET_HEADROOM

        if requested <= ceiling:
            return

        logger.error(
            "OUTPUT BUDGET TOO SMALL | the prompt asks for ~%d tokens of prose "
            "but AI_MAX_TOKENS=%d (usable ~%d after structure). Generation will "
            "stop at the limit with done_reason='length', truncating the last "
            "section mid-sentence. Raise AI_MAX_TOKENS to at least %d, or lower "
            "the per-section word limits in prompt_builder.",
            requested,
            max_tokens,
            int(ceiling),
            int(requested / OUTPUT_BUDGET_HEADROOM) + 1,
        )

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

        self._warn_if_context_window_too_small(prompt)
        self._warn_if_output_budget_too_small()

        start_time = time.perf_counter()

        try:

            logger.info("Sending request to Ollama...")

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

            api_time = time.perf_counter() - api_start

            logger.info(
                "Ollama API completed in %.2f seconds",
                api_time,
            )

            if response is None:

                raise RuntimeError("Ollama returned no response.")

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

            parsed = ResponseParser.parse(content)

            if not parsed:

                raise RuntimeError("Parsed response is empty.")

            word_count = len(parsed.split())

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
                time.perf_counter() - start_time,
            )

            return parsed

        except ResponseError:

            logger.exception("Ollama server returned an error.")

            raise

        except TimeoutError:

            logger.exception("Ollama request timed out.")

            raise

        except Exception:

            logger.exception("Unexpected Ollama client error.")

            raise
