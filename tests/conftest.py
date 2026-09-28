"""
Shared pytest configuration for the AnalystGPT Enterprise test suite.

Responsibilities
----------------
- Cap the LLM timeout for ordinary unit-test runs, without touching production.
- Leave integration runs on their full live-inference budget.
- Drain AI background worker pools at session teardown.

Why the cap is applied here, at import time
-------------------------------------------
`OllamaClient.__init__` passes `config.AI_TIMEOUT` to its httpx client, and
`src/api/dependencies/application_dependency.py` builds an `Application` (and
therefore an `OllamaClient`) at MODULE IMPORT time. The timeout is captured
once, at construction: mutating `config.AI_TIMEOUT` afterwards has no effect on
a client that already exists. Verified directly:

    config.AI_TIMEOUT = 15.0          -> live httpx timeout stays Timeout(300.0)

So the only reliable lever is the environment variable, set before anything
under `src/` is imported. This module is imported before test collection, which
is where those imports happen.

Why a cap and not a default
---------------------------
An earlier version used `os.environ.setdefault("AI_TIMEOUT", "15")`. That is
wrong in the documented developer workflow: after running the app with
`$env:AI_TIMEOUT="300"`, a `pytest -q` in the same shell inherited 300s, and no
fixture could correct it because the clients were already frozen. Taking the
minimum of the configured value and the unit-test ceiling makes the cap hold
regardless of the shell, while still allowing a developer to request something
*shorter* than the ceiling.

Integration runs are exempt: they exercise real inference deliberately.
"""

from __future__ import annotations

import atexit
import logging
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

# ==========================================================
# Persistence isolation
# ==========================================================
#
# The database path, the report output directory and the artifact store are
# module-level constants in `src/core/config.py`, and
# `src/api/dependencies/application_dependency.py` builds an `Application` -
# opening a connection and an artifact store - at MODULE IMPORT time. A
# fixture therefore runs far too late to redirect any of them.
#
# Measured cost of not doing this, for a single `pytest -q` (580 tests):
#
#     users            +11      dataset_versions  +38
#     ai_jobs          +19      pipeline_runs     +20
#     reports          +19      artifact dirs     +47
#     reports/*.txt    +19 files
#     reports/analystgpt_report.txt  and  .pdf  OVERWRITTEN
#
# 199 of the 203 user rows in the developer's database were test residue.
#
# Redirecting via the environment, before anything under `src/` is imported,
# is the only lever that works. The directory is removed at interpreter exit.

_TEST_STATE_ROOT: Path | None = None


def _isolate_persistence_roots() -> None:
    """Point the database, reports and artifact store at a temporary tree."""
    global _TEST_STATE_ROOT

    if _TEST_STATE_ROOT is not None:
        return

    root = Path(tempfile.mkdtemp(prefix="analystgpt-tests-"))
    _TEST_STATE_ROOT = root

    reports_dir = root / "reports"
    artifacts_dir = root / "artifacts"
    reports_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # setdefault, not assignment: a developer debugging against a specific
    # fixture database should be able to pin these explicitly.
    os.environ.setdefault("SQLITE_DATABASE_PATH", str(root / "analystgpt-test.db"))
    os.environ.setdefault("REPORT_OUTPUT_DIRECTORY", str(reports_dir))
    os.environ.setdefault("ARTIFACT_STORE_DIRECTORY", str(artifacts_dir))

    atexit.register(shutil.rmtree, root, True)


# Must run before anything under `src/` is imported.
_isolate_persistence_roots()


# ==========================================================
# Timeout ceiling for ordinary unit-test runs
# ==========================================================

#: Ordinary tests must never block on real inference for longer than this.
UNIT_TEST_AI_TIMEOUT_CEILING = 15.0

#: Budget for joining lingering AI worker threads at session teardown. Must
#: exceed the ceiling above so an in-flight call can finish on its own.
AI_WORKER_JOIN_TIMEOUT_SECONDS = 45.0


def _integration_selected(argv: list[str]) -> bool:
    """
    Return True when this run explicitly selects integration tests.

    Only an explicit `-m` expression on the command line counts. The default
    `-m "not integration"` lives in `addopts` and never reaches `sys.argv`.
    """
    for index, arg in enumerate(argv):
        expression: str | None = None

        if arg == "-m" and index + 1 < len(argv):
            expression = argv[index + 1]
        elif arg.startswith("-m") and len(arg) > 2:
            expression = arg[2:]

        if expression is None:
            continue

        # Remove negated mentions first, then ask whether integration is still
        # selected. This distinguishes the three documented expressions:
        #   "not integration"                -> excluded      -> cap applies
        #   "integration"                    -> selected      -> no cap
        #   "integration or not integration" -> selected      -> no cap
        normalised = expression.lower()
        remaining = re.sub(r"\bnot\s+integration\b", "", normalised)

        if "integration" in remaining:
            return True

    return False


def _apply_unit_test_timeout_ceiling() -> None:
    """Clamp AI_TIMEOUT for unit-test runs; leave integration runs alone."""
    if _integration_selected(sys.argv[1:]):
        return

    ceiling = UNIT_TEST_AI_TIMEOUT_CEILING
    configured = os.environ.get("AI_TIMEOUT")

    if configured is not None:
        try:
            ceiling = min(float(configured), UNIT_TEST_AI_TIMEOUT_CEILING)
        except ValueError:
            ceiling = UNIT_TEST_AI_TIMEOUT_CEILING

    os.environ["AI_TIMEOUT"] = str(ceiling)


# Must run before anything under `src/` is imported.
_apply_unit_test_timeout_ceiling()

import pytest  # noqa: E402

from src.ai.job_executor import shutdown_all_executors  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def drain_ai_workers() -> Iterator[None]:
    """
    Cancel queued AI jobs and join worker threads once the session ends.

    `AIJobExecutor` wraps a `ThreadPoolExecutor` whose workers are non-daemon,
    and `concurrent.futures` joins them at interpreter shutdown. Without this,
    an executor holding an in-flight Ollama call kept the pytest process alive
    long after the summary line was printed.
    """
    yield

    # A worker logging after pytest releases its output capture would print a
    # full traceback per record, because the handler's stream is closed by then.
    logging.raiseExceptions = False

    shutdown_all_executors(
        wait=True,
        cancel_pending=True,
        timeout=AI_WORKER_JOIN_TIMEOUT_SECONDS,
    )
