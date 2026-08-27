"""
Integration tests for the Ollama client.

These tests verify:

✓ Ollama server is reachable
✓ Model exists
✓ Model generates responses
✓ Response is not empty
✓ Response time is acceptable
✓ Enterprise prompt works

Run:

pytest tests/ai/test_ollama_connection.py -v

or

python -m pytest tests/ai/test_ollama_connection.py -v
"""

from __future__ import annotations

import time

import pytest
from ollama import Client

from src.core import config


def _is_ollama_available() -> bool:
    """Check if the local Ollama server is running and reachable."""
    try:
        c = Client(host=config.OLLAMA_HOST, timeout=2.0)
        c.list()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _is_ollama_available(),
    reason=f"Ollama server is not reachable at {config.OLLAMA_HOST}",
)


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture(scope="module")
def client() -> Client:
    """
    Create Ollama client.
    """

    return Client(
        host=config.OLLAMA_HOST,
        timeout=config.AI_TIMEOUT,
    )


# ==========================================================
# Server Tests
# ==========================================================


def test_ollama_server_running(client: Client) -> None:
    """
    Verify Ollama server is running.
    """

    models = client.list()

    assert models is not None


def test_model_exists(client: Client) -> None:
    """
    Verify configured model exists.
    """

    models = client.list()

    installed = [
        model.model
        for model in models.models
    ]

    assert (
        config.OLLAMA_MODEL
        in installed
    ), (
        f"Configured model "
        f"{config.OLLAMA_MODEL} "
        f"not installed.\n"
        f"Installed models: {installed}"
    )


# ==========================================================
# Generation Tests
# ==========================================================


def test_simple_generation(client: Client) -> None:
    """
    Basic generation test.
    """

    start = time.perf_counter()

    response = client.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Reply in one short sentence."
                ),
            },
            {
                "role": "user",
                "content": "Say hello.",
            },
        ],
        options={
            "temperature": 0.0,
            "num_predict": 30,
        },
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        f"\nGeneration Time: "
        f"{elapsed:.2f} sec"
    )

    assert response is not None
    assert response.message is not None
    assert response.message.content.strip() != ""


def test_response_speed(client: Client) -> None:
    """
    Ensure the model responds in a reasonable time.

    This threshold may need adjustment depending on hardware.
    """

    start = time.perf_counter()

    client.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": "What is 2+2?",
            }
        ],
        options={
            "temperature": 0.0,
            "num_predict": 10,
        },
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        f"\nResponse Time: "
        f"{elapsed:.2f} sec"
    )

    assert elapsed < config.AI_TIMEOUT


# ==========================================================
# Enterprise Prompt Test
# ==========================================================


def test_business_prompt(client: Client) -> None:
    """
    Simulates AnalystGPT usage.
    """

    prompt = """
Enterprise Analytics Report

Rows : 1,000,000

Columns : 12

Completeness : 98.6%

Duplicate Rows : 0

Revenue increased 18%.

Customer churn decreased 6%.

Generate a concise executive summary.
"""

    response = client.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a business analytics assistant. "
                    "Reply directly. "
                    "Do not explain your reasoning."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        options={
            "temperature": 0.2,
            "num_predict": 200,
            "top_p": 0.9,
        },
    )

    text = (
        response.message.content
        .strip()
    )

    print("\n")
    print("=" * 60)
    print(text)
    print("=" * 60)

    assert len(text) > 20


# ==========================================================
# Stress Test
# ==========================================================


def test_multiple_requests(client: Client) -> None:
    """
    Ensure repeated requests remain stable.
    """

    for index in range(3):

        response = client.chat(
            model=config.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Reply with the number {index}."
                    ),
                }
            ],
            options={
                "temperature": 0.0,
                "num_predict": 20,
            },
        )

        assert (
            response.message.content.strip()
            != ""
        )


# ==========================================================
# Large Prompt Test
# ==========================================================


def test_large_prompt(client: Client) -> None:
    """
    Verify the model can process larger prompts.
    """

    report = (
        "Revenue increased by 12%. "
        * 500
    )

    response = client.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": report,
            }
        ],
        options={
            "temperature": 0.1,
            "num_predict": 100,
        },
    )

    assert (
        response.message.content.strip()
        != ""
    )