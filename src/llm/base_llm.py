"""
Abstract interface for Large Language Model providers.

Every LLM implementation (Ollama, OpenAI, Gemini, Claude, etc.)
must implement this interface.

The AI layer communicates only with this abstraction and never
depends on a concrete provider.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class BaseLLM(ABC):
    """
    Abstract base class for all LLM providers.
    """

    @property
    @abstractmethod
    def model(
        self,
    ) -> str:
        """
        Return the configured model name.
        """

        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from the language model.

        Parameters
        ----------
        prompt:
            Prompt sent to the language model.

        Returns
        -------
        str
            Generated response.
        """

        raise NotImplementedError