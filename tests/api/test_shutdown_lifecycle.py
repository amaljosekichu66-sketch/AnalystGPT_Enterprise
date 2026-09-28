"""
Regression tests: API shutdown must drain the AI subsystem.

The defect
----------
The FastAPI `lifespan` logged "Stopping AnalystGPT Enterprise API..." and
returned. It never called `Application.shutdown()`, and nothing else did:
grepping `src/` and `main.py` found the method's only callers were tests.

Observed before the fix, driving the real app through `with TestClient(app)`:

    AFTER lifespan exit:
        executor._is_shutdown : False
        ai-worker threads     : 1  (alive, daemon=False)

`ThreadPoolExecutor` workers are non-daemon and `concurrent.futures` joins them
from an atexit hook, so the server process blocks on exit until every in-flight
AI job completes - up to `AI_TIMEOUT` each, measured in minutes on CPU
inference. Outstanding retry timers could also still resubmit work into a pool
that was supposed to be closing.

Scope note
----------
These tests swap the module-level `Application` singleton for a throwaway
instance, because `lifespan` shuts down whatever it finds. Without that, this
module would close the shared executor for every test that ran afterwards.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.server import app


@pytest.fixture()
def disposable_application(monkeypatch: pytest.MonkeyPatch) -> Iterator:
    """
    Install a throwaway Application as the singleton for one test.

    Restored by monkeypatch, so the shared instance other tests rely on is
    never shut down.
    """
    from src.application.app import Application

    instance = Application()
    monkeypatch.setattr(
        "src.api.dependencies.application_dependency._application",
        instance,
        raising=False,
    )

    yield instance

    # Belt and braces: the test may have left it running on failure.
    try:
        instance.shutdown()
    except Exception:
        pass


def _ai_worker_threads() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name.startswith("ai-worker")]


# ==========================================================
# The drain itself
# ==========================================================


def test_lifespan_shutdown_marks_the_executor_shut_down(
    disposable_application,
) -> None:
    """The reproduction case: executor left running after lifespan exit."""
    executor = disposable_application.ai_job_executor

    assert executor._is_shutdown is False

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200

    assert executor._is_shutdown is True


def test_shutdown_refuses_new_ai_work(disposable_application) -> None:
    """
    After shutdown no further job may be dispatched.

    A refused submission leaves the row PENDING for stale-job recovery, which
    is the correct lifecycle outcome; accepting it would queue work into a
    closing pool.
    """
    executor = disposable_application.ai_job_executor

    with TestClient(app):
        pass

    submitted: list[tuple] = []
    executor._executor.submit = lambda *args, **kwargs: submitted.append(args)

    executor.submit_job("job-after-shutdown", None)

    assert submitted == []


def test_shutdown_cancels_outstanding_retry_timers(
    disposable_application,
) -> None:
    """A pending retry must not fire into a drained pool."""
    executor = disposable_application.ai_job_executor
    fired: list[str] = []
    executor.submit_job = lambda job_id, report: fired.append(job_id)

    executor._schedule_retry_timer(
        delay=0.3,
        job_id="job-pending-retry",
        reporting_report=None,
    )
    assert len(executor._retry_timers) == 1

    with TestClient(app):
        pass

    assert executor._retry_timers == set()

    time.sleep(0.6)
    assert fired == []


def test_executor_leaves_the_live_registry(disposable_application) -> None:
    """`shutdown_all_executors()` must not keep finding a drained executor."""
    import src.ai.job_executor as job_executor

    executor = disposable_application.ai_job_executor

    with TestClient(app):
        pass

    assert executor not in list(job_executor._ACTIVE_EXECUTORS)


# ==========================================================
# What the drain must NOT do
# ==========================================================


def test_in_flight_work_is_not_abandoned(disposable_application) -> None:
    """
    `Application.shutdown()` passes `wait=False` on purpose.

    A job already talking to the model is left to finish rather than being
    abandoned mid-generation with its database row stuck in GENERATING.
    """
    executor = disposable_application.ai_job_executor
    completed = threading.Event()

    executor._executor.submit(lambda: (time.sleep(0.3), completed.set()))

    with TestClient(app):
        pass

    assert completed.wait(timeout=5.0), "in-flight work was abandoned"


def test_shutdown_failure_does_not_break_the_lifespan(
    monkeypatch: pytest.MonkeyPatch,
    disposable_application,
) -> None:
    """
    A drain that raises must not turn server shutdown into an exception.

    It is logged rather than swallowed, but it cannot mask the real reason the
    process is stopping.
    """

    def explode() -> None:
        raise RuntimeError("drain failed")

    monkeypatch.setattr(disposable_application, "shutdown", explode)

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
