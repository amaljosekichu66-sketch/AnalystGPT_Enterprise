"""
Regression tests for L7 and the 422 part of I10 (audit 2026-09-29).

- L7: the AI retry route returned f"...{exc}", AI job responses carried the
  raw stored error, and the Streamlit app showed full tracebacks
  (`st.exception`) to any visitor.
- I10: 422 responses echoed every invalid input back, passwords included.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.ai.exceptions import AIJobNotFoundError, AIStateTransitionError
from src.api.dependencies.application_dependency import get_application
from src.api.routes.ai import public_job_error
from src.api.server import app
from src.core import config

REPO = Path(__file__).resolve().parents[2]
SECRET_DETAIL = r"Traceback: C:\srv\analystgpt\secret_module.py line 12 http://10.0.0.5:11434"
ANALYST = {"X-User-Id": "4242", "X-User-Name": "l7_analyst", "X-User-Role": "ANALYST"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", True)
    return TestClient(app)


def _job(error: str | None, category: str | None) -> dict:
    return {
        "job_id": "job-1",
        "pipeline_run_id": 1,
        "status": "FAILED",
        "provider": "ollama",
        "model": "m",
        "error": error,
        "failure_category": category,
    }


@pytest.mark.parametrize(
    "category, expected",
    [("TIMEOUT", "AI generation timed out."), ("SYSTEM_ERROR", "AI generation failed because of an internal error.")],
)
def test_job_errors_are_mapped_to_fixed_messages(category: str, expected: str) -> None:
    assert public_job_error(category, SECRET_DETAIL) == expected
    assert public_job_error(None, SECRET_DETAIL) == "AI generation failed."
    assert public_job_error(None, None) is None


def test_job_response_does_not_carry_the_stored_error(client: TestClient, monkeypatch) -> None:
    service = get_application().ai_job_service
    monkeypatch.setattr(service, "get_job_with_report", lambda **_: _job(SECRET_DETAIL, "PROVIDER_UNAVAILABLE"))

    res = client.get("/api/ai/jobs/job-1", headers=ANALYST)

    assert res.status_code == 200
    assert res.json()["error"] == "The AI provider is unavailable."
    assert "secret_module" not in res.text and "10.0.0.5" not in res.text


class TestRetryRoute:
    def _retry(self, client: TestClient, monkeypatch, exc: Exception):
        def fail(**_):
            raise exc

        monkeypatch.setattr(get_application().ai_job_service, "retry_job", fail)
        return client.post("/api/ai/jobs/job-1/retry", headers=ANALYST)

    def test_unexpected_error_text_is_not_returned(self, client: TestClient, monkeypatch) -> None:
        res = self._retry(client, monkeypatch, RuntimeError(SECRET_DETAIL))
        assert res.status_code == 400
        assert "secret_module" not in res.text

    def test_missing_job_is_404(self, client: TestClient, monkeypatch) -> None:
        assert self._retry(client, monkeypatch, AIJobNotFoundError("x")).status_code == 404

    def test_job_in_wrong_state_is_400_with_a_clear_reason(self, client: TestClient, monkeypatch) -> None:
        res = self._retry(client, monkeypatch, AIStateTransitionError("x"))
        assert res.status_code == 400
        assert "Only a failed AI job can be retried." in res.text


def test_validation_errors_do_not_echo_input(client: TestClient) -> None:
    secret = "MyS3cret-" + "p" * 130
    res = client.post("/api/auth/login", json={"username": "someone", "password": secret})

    assert res.status_code == 422
    assert secret not in res.text
    assert res.json()["detail"][0]["loc"] == ["body", "password"]


def test_streamlit_shows_no_tracebacks() -> None:
    app_source = (REPO / "src" / "frontend" / "streamlit_app.py").read_text(encoding="utf-8")
    uploader_source = (REPO / "src" / "frontend" / "components" / "uploader.py").read_text(encoding="utf-8")
    streamlit_config = (REPO / ".streamlit" / "config.toml").read_text(encoding="utf-8")

    assert "st.exception(" not in app_source
    assert "{error}" not in uploader_source.split("except Exception as error:")[-1]
    assert 'showErrorDetails = "none"' in streamlit_config
