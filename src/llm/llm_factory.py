"""
Factory responsible for creating the configured
Large Language Model provider.
"""

from __future__ import annotations

from src.core import config
from src.core.logger import logger
from src.llm.base_llm import BaseLLM
from src.llm.ollama_client import OllamaClient


class LLMFactory:
    """
    Creates the configured language model.
    """

    _PROVIDERS = {
        "ollama": OllamaClient,
    }

    @classmethod
    def create(
        cls,
    ) -> BaseLLM:
        """
        Create the configured language model.

        Returns
        -------
        BaseLLM
            Configured provider.
        """
        provider = config.LLM_PROVIDER.strip().lower()

        logger.info(
            "Initialising LLM Provider: %s",
            provider,
        )

        provider_class = cls._PROVIDERS.get(
            provider,
        )

        if provider_class is not None:
            llm = provider_class()
            logger.info(
                "LLM Initialised | Provider=%s | Model=%s",
                provider,
                llm.model,
            )
            return llm

        logger.error(
            "Unsupported LLM Provider: %s",
            provider,
        )
        raise ValueError(f"Unsupported LLM Provider: {provider}")

    @classmethod
    def create_llm(cls) -> BaseLLM:
        """Alias for create() for backwards compatibility."""
        return cls.create()
