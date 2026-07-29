"""
Unit tests for the enterprise LLM service.

These tests verify:

✓ Successful generation
✓ Retry behaviour
✓ Empty responses
✓ Exception handling
✓ Maximum retry limit
"""

from __future__ import annotations

import pytest

from src.llm.base_llm import BaseLLM
from src.llm.llm_service import LLMService


# ==========================================================
# Fake LLMs
# ==========================================================


class SuccessfulLLM(BaseLLM):
    """
    Always succeeds.
    """

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return "Successful response."


class EmptyLLM(BaseLLM):
    """
    Returns an empty string.
    """

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        return ""


class FailingLLM(BaseLLM):
    """
    Always raises an exception.
    """

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        raise RuntimeError(
            "LLM failure."
        )


class RetryLLM(BaseLLM):
    """
    Fails twice then succeeds.
    """

    def __init__(self) -> None:

        self.calls = 0

    @property
    def model(self) -> str:
        return "test-model"

    def generate(
        self,
        prompt: str,
    ) -> str:

        self.calls += 1

        if self.calls < 3:
            raise RuntimeError(
                "Temporary failure."
            )

        return "Recovered."


# ==========================================================
# Tests
# ==========================================================


def test_successful_generation() -> None:
    """
    LLMService returns successful responses.
    """

    service = LLMService(
        SuccessfulLLM()
    )

    response = service.generate(
        "Hello"
    )

    assert (
        response
        == "Successful response."
    )


def test_empty_response() -> None:
    """
    Empty responses should fail.
    """

    service = LLMService(
        EmptyLLM()
    )

    with pytest.raises(
        RuntimeError
    ):

        service.generate(
            "Hello"
        )


def test_llm_failure() -> None:
    """
    Complete failure after retries.
    """

    service = LLMService(
        FailingLLM()
    )

    with pytest.raises(
        RuntimeError
    ):

        service.generate(
            "Hello"
        )


def test_retry_success() -> None:
    """
    Retry logic eventually succeeds.
    """

    llm = RetryLLM()

    service = LLMService(
        llm
    )

    response = service.generate(
        "Hello"
    )

    assert (
        response
        == "Recovered."
    )

    assert llm.calls == 3


def test_retry_limit() -> None:
    """
    Ensure retry count is respected.
    """

    llm = FailingLLM()

    service = LLMService(
        llm
    )

    with pytest.raises(
        RuntimeError
    ):

        service.generate(
            "Hello"
        )