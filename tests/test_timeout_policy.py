"""
Regression tests for the unit-test / integration / production timeout split.

Context
-------
`OllamaClient` captures `config.AI_TIMEOUT` when its httpx client is built, and
`src/api/dependencies/application_dependency.py` builds an `Application` at
module import time. The timeout is therefore frozen before any fixture runs,
so the environment variable is the only reliable lever.

An earlier version of conftest used `os.environ.setdefault("AI_TIMEOUT", "15")`.
In the documented workflow - run the app with `$env:AI_TIMEOUT="300"`, then run
`pytest -q` in the same shell - that default did not apply and ordinary tests
inherited a 300s inference timeout.
"""

from __future__ import annotations

import os

from tests.conftest import (
    UNIT_TEST_AI_TIMEOUT_CEILING,
    _apply_unit_test_timeout_ceiling,
    _integration_selected,
)

# ==========================================================
# Integration selection
# ==========================================================


def test_explicit_integration_selection_is_detected() -> None:
    assert _integration_selected(["-m", "integration", "-v"]) is True
    assert _integration_selected(["-mintegration"]) is True
    assert _integration_selected(["-m", "integration or not integration"]) is True


def test_default_and_negated_selection_are_not_integration() -> None:
    assert _integration_selected([]) is False
    assert _integration_selected(["-q"]) is False
    assert _integration_selected(["-m", "not integration"]) is False
    assert _integration_selected(["-m", "not integration", "-q"]) is False


def test_dangling_m_flag_does_not_crash() -> None:
    assert _integration_selected(["-m"]) is False


# ==========================================================
# Ceiling behaviour
# ==========================================================


def _with_env(value: str | None, argv: list[str]) -> str | None:
    """Apply the ceiling under a given env value and argv, then restore."""
    original_env = os.environ.get("AI_TIMEOUT")
    original_argv = list(os.sys.argv)

    try:
        if value is None:
            os.environ.pop("AI_TIMEOUT", None)
        else:
            os.environ["AI_TIMEOUT"] = value

        os.sys.argv = ["pytest", *argv]
        _apply_unit_test_timeout_ceiling()
        return os.environ.get("AI_TIMEOUT")
    finally:
        os.sys.argv = original_argv
        if original_env is None:
            os.environ.pop("AI_TIMEOUT", None)
        else:
            os.environ["AI_TIMEOUT"] = original_env


def test_unset_timeout_gets_the_unit_test_ceiling() -> None:
    assert float(_with_env(None, ["-q"])) == UNIT_TEST_AI_TIMEOUT_CEILING


def test_production_style_timeout_is_capped_for_unit_tests() -> None:
    """The documented $env:AI_TIMEOUT="300" shell must not slow unit tests."""
    assert float(_with_env("300", ["-q"])) == UNIT_TEST_AI_TIMEOUT_CEILING


def test_a_shorter_developer_timeout_is_respected() -> None:
    """The ceiling clamps; it does not raise a deliberately shorter value."""
    assert float(_with_env("5", ["-q"])) == 5.0


def test_malformed_timeout_falls_back_to_the_ceiling() -> None:
    assert float(_with_env("not-a-number", ["-q"])) == UNIT_TEST_AI_TIMEOUT_CEILING


def test_integration_runs_keep_their_full_budget() -> None:
    """Integration tests exercise real inference and must not be capped."""
    assert _with_env("300", ["-m", "integration"]) == "300"


def test_integration_runs_are_untouched_when_unset() -> None:
    assert _with_env(None, ["-m", "integration"]) is None


# ==========================================================
# Effective state of the current run
# ==========================================================


def test_current_unit_test_run_is_within_the_ceiling() -> None:
    """
    This assertion runs inside an ordinary `pytest -q`, so it pins the real
    effective timeout rather than a simulated one.
    """
    from src.core import config

    assert config.AI_TIMEOUT <= UNIT_TEST_AI_TIMEOUT_CEILING
