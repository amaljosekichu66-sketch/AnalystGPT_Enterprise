"""
Live integration tests that drive the ACTUAL application LLM path.

Why this file exists
--------------------
`test_ollama_connection.py` builds a raw `ollama.Client` of its own, with its
own `OLLAMA_TEST_TIMEOUT` budget and literal `num_predict` values, and never
sets `num_ctx`. It therefore proves the Ollama *server* works. It proves
nothing about whether `AI_TIMEOUT`, `AI_MAX_TOKENS` or `AI_CONTEXT_WINDOW` ever
reach a live request through `OllamaClient`.

That gap was not theoretical. `test_large_prompt` passed at 147.4s only because
it used its own 300s budget; the production default at the time was 120s, so
the identical workload would have timed out in the application while the
integration suite stayed green.

These tests close that gap: everything here goes through `LLMFactory` ->
`OllamaClient` -> a real Ollama request, and asserts on what the production
objects actually did.

Run with:   pytest -m integration tests/ai/test_ollama_production_path.py -v
"""

from __future__ import annotations

import importlib
import time
from typing import Any

import pytest

from src.core import config


def _is_ollama_available() -> bool:
    try:
        from ollama import Client

        Client(host=config.OLLAMA_HOST, timeout=2.0).list()
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _is_ollama_available(),
        reason=f"Ollama server is not reachable at {config.OLLAMA_HOST}",
    ),
]


@pytest.fixture()
def ollama_client():
    """A client built exactly the way production builds one."""
    from src.llm.llm_factory import LLMFactory

    return LLMFactory.create()


@pytest.fixture()
def captured_requests(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """
    Record the options of every live Ollama request, then call through.

    Spying rather than stubbing: the request is genuinely executed, so these
    remain integration tests rather than assertions about a mock.
    """
    from ollama import Client

    recorded: list[dict[str, Any]] = []
    original = Client.generate

    def spy(self, *args: Any, **kwargs: Any):
        recorded.append(dict(kwargs))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Client, "generate", spy)
    return recorded


# ==========================================================
# The configured values must reach the live client
# ==========================================================


def test_ai_timeout_reaches_the_live_http_client(ollama_client) -> None:
    """
    `OllamaClient.__init__` freezes `config.AI_TIMEOUT` into its httpx client.
    Nothing downstream can change it afterwards, so this is the only place the
    production timeout can be observed.
    """
    httpx_client = ollama_client._client._client

    assert float(httpx_client.timeout.read) == pytest.approx(config.AI_TIMEOUT)


def test_ai_max_tokens_reaches_the_live_request(
    ollama_client,
    captured_requests: list[dict[str, Any]],
) -> None:
    ollama_client.generate("Reply with the single word: ok. Then write END RESPONSE")

    assert captured_requests, "no live Ollama request was issued"
    assert captured_requests[-1]["options"]["num_predict"] == config.AI_MAX_TOKENS


def test_ai_context_window_reaches_the_live_request(
    ollama_client,
    captured_requests: list[dict[str, Any]],
) -> None:
    ollama_client.generate("Reply with the single word: ok. Then write END RESPONSE")

    assert captured_requests[-1]["options"]["num_ctx"] == config.AI_CONTEXT_WINDOW


def test_generation_parameters_reach_the_live_request(
    ollama_client,
    captured_requests: list[dict[str, Any]],
) -> None:
    ollama_client.generate("Reply with the single word: ok. Then write END RESPONSE")

    options = captured_requests[-1]["options"]

    assert options["temperature"] == pytest.approx(config.AI_TEMPERATURE)
    assert options["top_p"] == pytest.approx(config.AI_TOP_P)
    assert captured_requests[-1]["keep_alive"] == config.OLLAMA_KEEP_ALIVE


def test_configured_model_is_the_model_requested(
    ollama_client,
    captured_requests: list[dict[str, Any]],
) -> None:
    ollama_client.generate("Reply with the single word: ok. Then write END RESPONSE")

    assert captured_requests[-1]["model"] == config.OLLAMA_MODEL
    assert ollama_client.model == config.OLLAMA_MODEL


# ==========================================================
# Environment -> config -> client, end to end
# ==========================================================


def test_environment_overrides_flow_through_to_the_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The documented developer workflow:

        $env:AI_TIMEOUT="300"; $env:AI_MAX_TOKENS="600"; $env:AI_CONTEXT_WINDOW="8192"

    Values are read at import into module constants, so this reloads `config`
    and rebuilds the client - which is exactly what starting the process does.
    """
    monkeypatch.setenv("AI_TIMEOUT", "300")
    monkeypatch.setenv("AI_MAX_TOKENS", "600")
    monkeypatch.setenv("AI_CONTEXT_WINDOW", "8192")

    try:
        reloaded = importlib.reload(config)

        assert reloaded.AI_TIMEOUT == 300.0
        assert reloaded.AI_MAX_TOKENS == 600
        assert reloaded.AI_CONTEXT_WINDOW == 8192

        import src.llm.ollama_client as ollama_module

        importlib.reload(ollama_module)
        client = ollama_module.OllamaClient()

        assert float(client._client._client.timeout.read) == pytest.approx(300.0)
    finally:
        monkeypatch.undo()
        importlib.reload(config)
        import src.llm.ollama_client as ollama_module

        importlib.reload(ollama_module)


def test_production_timeout_covers_a_realistic_report_prompt(
    ollama_client,
) -> None:
    """
    The regression that a green `test_large_prompt` used to hide.

    A report-sized prompt is sent through the production client on the
    production budget. If `AI_TIMEOUT` is set below what this deployment needs,
    this fails here rather than in a user's report.
    """
    prompt = (
        "The report below is the only source of truth.\n"
        + ("Closed accounts for 89.0% of records. Email accounts for 74.7%. " * 120)
        + "\nSummarise in two sentences. Then write END RESPONSE"
    )

    started = time.perf_counter()
    response = ollama_client.generate(prompt)
    elapsed = time.perf_counter() - started

    assert response.strip()
    assert elapsed < config.AI_TIMEOUT, (
        f"A realistic report prompt took {elapsed:.1f}s against an AI_TIMEOUT "
        f"of {config.AI_TIMEOUT:.0f}s. Production would classify this as "
        "TIMEOUT. Raise AI_TIMEOUT or reduce the prompt/token budget."
    )


# ==========================================================
# The full AI path, not just the client
# ==========================================================


def _build_reporting_report():
    """
    Produce a real `ReportingReport` through the deterministic pipeline.

    Built rather than stubbed, so the prompt the model receives is the prompt
    production would build - including the authoritative distribution
    interpretation and the numerical statistics section.
    """
    import tempfile
    from pathlib import Path

    from src.analytics.analytics_manager import AnalyticsManager
    from src.reporting.reporting_manager import ReportingManager
    from tests.fixtures.sample_dataset import sample_dataframe

    analytics_report = AnalyticsManager().analyze(sample_dataframe())

    with tempfile.TemporaryDirectory() as directory:
        return ReportingManager().generate_report(
            analytics_report=analytics_report,
            output_path=Path(directory) / "integration_report.txt",
        )


def test_ai_manager_builds_a_report_through_the_live_model() -> None:
    """
    `LLMFactory` -> `OllamaClient` -> `UnifiedReportEngine` -> `AIManager`,
    against a real model. Exercises prompt construction, the live request and
    section parsing together - none of which the raw-client tests touch.
    """
    from src.ai.ai_manager import AIManager

    result = AIManager().generate_ai_report(_build_reporting_report())

    assert result.success, f"AI generation failed: {result.error}"
    assert result.ai_report is not None
    assert result.ai_report.executive_summary.strip()
    assert result.ai_report.narrative.strip()
    assert result.ai_report.model == config.OLLAMA_MODEL
    assert result.ai_report.provider == config.LLM_PROVIDER
