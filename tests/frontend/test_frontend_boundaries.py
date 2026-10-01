"""
Regression tests for P2-05, P2-07 and P2-08 (Sprint 15 readiness gate).

- P2-05: the Streamlit process ran the profiler, the planner, the governance
  service and the preview service itself. It may import only src.frontend,
  src.core and the upload guards.
- P2-07: every rerun re-uploaded the file and created a new dataset version;
  config.toml was not in the image.
- P2-08: raw "HTTP 422: {json}" text reached users.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from src.frontend.services.errors import UNAVAILABLE, friendly_error

REPO = Path(__file__).resolve().parents[2]
FORBIDDEN = (
    "src.application",
    "src.persistence",
    "src.profiling",
    "src.governance",
    "src.analytics",
    "src.database",
    "src.identity",
    "src.ai",
    "src.llm",
    "src.reporting",
)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def test_frontend_imports_no_backend_package() -> None:
    offenders = {
        str(path.relative_to(REPO)): sorted(name for name in _imports(path) if name.startswith(FORBIDDEN))
        for path in (REPO / "src" / "frontend").rglob("*.py")
    }
    assert {path: names for path, names in offenders.items() if names} == {}


class TestUploadIsNotRepeated:
    @pytest.fixture(autouse=True)
    def clean(self):
        st.session_state.clear()
        yield
        st.session_state.clear()

    def test_rerun_with_the_same_file_does_not_upload_again(self) -> None:
        from src.frontend.components import uploader

        uploaded = MagicMock(size=20)
        uploaded.name = "a.csv"
        uploaded.getvalue.return_value = b"a,b\n1,2\n"
        with (
            patch.object(uploader.st, "file_uploader", return_value=uploaded),
            patch.object(uploader, "upload_to_backend", return_value="v-1") as upload,
        ):
            uploader.render_uploader()
            uploader.render_uploader()
        assert upload.call_count == 1

    def test_a_different_file_is_uploaded(self) -> None:
        from src.frontend.components import uploader

        first, second = MagicMock(size=20), MagicMock(size=20)
        first.name = second.name = "a.csv"
        first.getvalue.return_value = b"a,b\n1,2\n"
        second.getvalue.return_value = b"a,b\n3,4\n"
        with (
            patch.object(uploader.st, "file_uploader", side_effect=[first, second]),
            patch.object(uploader, "upload_to_backend", side_effect=["v-1", "v-2"]) as upload,
        ):
            uploader.render_uploader()
            uploader.render_uploader()
        assert upload.call_count == 2


def test_streamlit_config_is_copied_into_the_image() -> None:
    dockerfile = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert ".streamlit/config.toml /app/.streamlit/config.toml" in dockerfile


class TestFriendlyErrors:
    def test_validation_errors_do_not_show_json(self) -> None:
        message = friendly_error(RuntimeError('Backend returned HTTP 422: {"detail": [{"loc": ["body"]}]}'), "login")
        assert "{" not in message and "422" not in message

    def test_api_down(self) -> None:
        assert friendly_error(RuntimeError("Unable to connect to backend: refused")) == UNAVAILABLE

    def test_user_facing_400_detail_is_kept(self) -> None:
        message = friendly_error(RuntimeError("Backend returned HTTP 400: Password is too common."), "registration")
        assert message == "Password is too common."

    def test_server_errors_are_generic(self) -> None:
        message = friendly_error(RuntimeError("Backend returned HTTP 500: Traceback at C:\\x"), "export")
        assert "Traceback" not in message
