"""
Unit tests for OllamaClient.
"""

from unittest.mock import patch

from src.core import config
from src.llm.ollama_client import OllamaClient


@patch.object(config, "OLLAMA_MODEL", "test-model")
def test_model_name():
    """
    Verify the configured model.
    """
    client = OllamaClient()
    assert client.model == "test-model"


@patch.object(config, "OLLAMA_MODEL", "test-model")
@patch.object(config, "OLLAMA_HOST", "http://localhost:11434")
def test_client_initialization():
    """
    Test client initialization.
    """
    client = OllamaClient()
    # The host attribute is not exposed; instead, check that the client
    # has been initialized correctly by checking the model.
    assert client.model == "test-model"


def test_real_model_name():
    """
    Integration test that uses the actual configuration.
    This test does not assert a specific value; it just confirms the
    model attribute is a non‑empty string.
    """
    client = OllamaClient()
    assert isinstance(client.model, str)
    assert client.model != ""