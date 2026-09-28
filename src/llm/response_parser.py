"""
Response parser for Large Language Model outputs.
"""

from __future__ import annotations

import re

from src.core.constants import AI_STOP_SEQUENCE


class ResponseParser:
    """
    Utility class for cleaning LLM responses.
    """

    _THINKING_PATTERNS = (
        r"<think>.*?</think>",
        r"<thinking>.*?</thinking>",
        r"<reasoning>.*?</reasoning>",
    )

    @classmethod
    def parse(
        cls,
        response: str,
    ) -> str:
        """
        Clean a language model response.
        """

        if not response:
            return ""

        cleaned = response

        # ======================================================
        # Remove reasoning blocks
        # ======================================================

        for pattern in cls._THINKING_PATTERNS:

            cleaned = re.sub(
                pattern,
                "",
                cleaned,
                flags=re.DOTALL | re.IGNORECASE,
            )

        # ======================================================
        # Remove stop sequence
        # ======================================================

        cleaned = cleaned.replace(
            AI_STOP_SEQUENCE,
            "",
        )

        # ======================================================
        # Remove fenced code blocks
        # ======================================================

        cleaned = re.sub(
            r"```(?:[\w+-]*)?\n?(.*?)```",
            r"\1",
            cleaned,
            flags=re.DOTALL,
        )

        # ======================================================
        # Remove inline code
        # ======================================================

        cleaned = cleaned.replace(
            "`",
            "",
        )

        # ======================================================
        # Remove markdown headings
        # ======================================================

        cleaned = re.sub(
            r"^#{1,6}\s*",
            "",
            cleaned,
            flags=re.MULTILINE,
        )

        # ======================================================
        # Normalise line endings
        # ======================================================

        cleaned = cleaned.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        # ======================================================
        # Remove trailing whitespace
        # ======================================================

        cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())

        # ======================================================
        # Collapse spaces
        # ======================================================

        cleaned = re.sub(
            r"[ \t]{2,}",
            " ",
            cleaned,
        )

        # ======================================================
        # Collapse blank lines
        # ======================================================

        cleaned = re.sub(
            r"\n{3,}",
            "\n\n",
            cleaned,
        )

        return cleaned.strip()
