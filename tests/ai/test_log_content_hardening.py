"""
Regression tests for L9 (audit 2026-09-29).

Full model responses, report objects and DataFrame previews were logged at
INFO, so dataset values (names, addresses) reached every log sink, and raw
newlines in model output forged log lines.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.application.app import _presence
from src.core import config
from src.core.logger import logger

SECRET_CELL = "Jane Q. Private, 12 Hidden Lane"


@pytest.fixture
def log_lines():
    lines: list[tuple[int, str]] = []

    class _Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            lines.append((record.levelno, record.getMessage()))

    handler = _Collect(level=logging.DEBUG)
    previous = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    yield lines
    logger.setLevel(previous)
    logger.removeHandler(handler)


def test_presence_hides_content() -> None:
    report = MagicMock(__str__=lambda self: SECRET_CELL)
    assert SECRET_CELL not in _presence(report)
    assert _presence(None) == "absent"


def test_llm_response_is_not_logged_by_default(log_lines, monkeypatch) -> None:
    from src.ai.unified_report_engine import UnifiedReportEngine

    monkeypatch.setattr(config, "LOG_LLM_RESPONSES", False)
    engine = UnifiedReportEngine.__new__(UnifiedReportEngine)
    monkeypatch.setattr(engine, "_build_prompt", lambda *a, **k: "prompt", raising=False)
    monkeypatch.setattr(
        engine, "_call_llm", lambda prompt: f"Top customer: {SECRET_CELL}\nFAKE | SECURITY_ALERT", raising=False
    )
    monkeypatch.setattr(engine, "_parse_sections", MagicMock(side_effect=RuntimeError("stop here")), raising=False)

    with pytest.raises(RuntimeError, match="stop here"):
        engine.generate(MagicMock())

    assert not any(SECRET_CELL in text for _, text in log_lines)
    assert any("LLM response:" in text and "sha256=" in text for _, text in log_lines)


def test_llm_response_debug_logging_is_flattened(log_lines, monkeypatch) -> None:
    from src.ai.unified_report_engine import UnifiedReportEngine

    monkeypatch.setattr(config, "LOG_LLM_RESPONSES", True)
    engine = UnifiedReportEngine.__new__(UnifiedReportEngine)
    monkeypatch.setattr(engine, "_build_prompt", lambda *a, **k: "prompt", raising=False)
    monkeypatch.setattr(engine, "_call_llm", lambda prompt: "line one\nSECURITY_ALERT | forged", raising=False)
    monkeypatch.setattr(engine, "_parse_sections", MagicMock(side_effect=RuntimeError("stop here")), raising=False)

    with pytest.raises(RuntimeError):
        engine.generate(MagicMock())

    debug = [text for level, text in log_lines if level == logging.DEBUG and "LLM response text" in text]
    assert debug and "\n" not in debug[0]


def test_dataset_previews_log_shape_only(log_lines, tmp_path) -> None:
    from src.application.app import Application

    path = tmp_path / "people.csv"
    pd.DataFrame({"name": [SECRET_CELL] * 3, "n": [1, 2, 3]}).to_csv(path, index=False)
    application = Application.__new__(Application)
    frame = pd.read_csv(path)
    application.governance_service = MagicMock(execute_governed_cleaning=lambda **_kwargs: MagicMock(cleaned_df=frame))

    result = application._clean_dataset_governed(frame, MagicMock(), MagicMock(), pipeline_run_id=1)

    assert len(result.cleaned_df) == 3
    assert not any(SECRET_CELL in text for _, text in log_lines)
    assert any("3 rows x 2 columns" in text for _, text in log_lines)
