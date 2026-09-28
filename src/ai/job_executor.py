"""
AI background job executor for AnalystGPT Enterprise.

Coordinates asynchronous execution of AI insight generation jobs,
managing atomic claiming, retry policies, exponential backoff,
and failure isolation.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from src.ai.ai_manager import AIManager
from src.ai.models import AIFailureCategory, AIJob, AIJobStatus
from src.core import config
from src.core.logger import logger
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.reporting.reporting_report import ReportingReport

# ==========================================================
# Live Executor Registry
# ==========================================================
#
# ThreadPoolExecutor worker threads are NON-daemon, and concurrent.futures
# installs an atexit hook that joins them at interpreter shutdown. An executor
# that is never shut down therefore keeps the owning process alive until every
# in-flight AI job finishes - up to AI_TIMEOUT per job, which on CPU inference
# is measured in minutes, not seconds.
#
# Every executor registers itself here so that a test session, a CLI run, or
# any other host process can drain all of them deterministically via
# shutdown_all_executors(). The registry holds weak references only, so it
# never keeps an otherwise-unreachable executor alive.

_ACTIVE_EXECUTORS: weakref.WeakSet[AIJobExecutor] = weakref.WeakSet()
_REGISTRY_LOCK = threading.Lock()


def shutdown_all_executors(
    wait: bool = True,
    cancel_pending: bool = True,
    timeout: float | None = None,
) -> int:
    """
    Shut down every live AIJobExecutor instance.

    Parameters
    ----------
    wait:
        Block until in-flight jobs finish.
    cancel_pending:
        Drop queued jobs that have not started yet.
    timeout:
        Optional overall budget, in seconds, for joining worker threads.

    Returns
    -------
    int
        Number of executors that were shut down.
    """
    with _REGISTRY_LOCK:
        executors = list(_ACTIVE_EXECUTORS)

    for executor in executors:
        executor.shutdown(
            wait=False,
            cancel_pending=cancel_pending,
        )

    if wait:
        _join_worker_threads(timeout=timeout)

    return len(executors)


def _join_worker_threads(timeout: float | None = None) -> None:
    """
    Join any lingering 'ai-worker' threads within the given budget.
    """
    deadline = None if timeout is None else time.monotonic() + timeout

    for thread in threading.enumerate():
        if not thread.name.startswith("ai-worker"):
            continue
        if not thread.is_alive() or thread is threading.current_thread():
            continue

        remaining = None
        if deadline is not None:
            remaining = max(0.0, deadline - time.monotonic())
            if remaining == 0.0:
                logger.warning(
                    "Timed out joining AI worker threads; '%s' is still running.",
                    thread.name,
                )
                return

        thread.join(timeout=remaining)


class AIJobExecutor:
    """
    Asynchronous executor for persistent AI generation jobs.
    """

    def __init__(
        self,
        max_workers: int = 4,
        ai_manager: AIManager | None = None,
    ) -> None:
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="ai-worker",
        )
        self._ai_manager = ai_manager or AIManager()
        self._lock = threading.Lock()

        # Outstanding retry timers, so shutdown() can cancel a retry that
        # would otherwise resubmit work into an already-drained pool.
        self._retry_timers: set[threading.Timer] = set()
        self._is_shutdown = False

        with _REGISTRY_LOCK:
            _ACTIVE_EXECUTORS.add(self)

    # ==========================================================
    # Asynchronous Submission
    # ==========================================================

    def submit_job(
        self,
        job_id: str,
        reporting_report: ReportingReport,
    ) -> None:
        """
        Dispatch background execution of an AI generation job.
        """
        # A shut-down pool raises RuntimeError from submit(). That exception
        # would propagate out of the request handler that created the job,
        # turning an orderly shutdown into a 500 and leaving the job row
        # PENDING with no explanation. Refusing the work is the correct
        # lifecycle behaviour: after shutdown, no new work is accepted.
        with self._lock:
            if self._is_shutdown:
                logger.warning(
                    "Executor is shut down; refusing to submit AI job '%s'. "
                    "The job remains PENDING and will be picked up by stale-job "
                    "recovery on next startup.",
                    job_id,
                )
                return

        logger.info(
            "Submitting AI job '%s' to background worker pool...",
            job_id,
        )

        try:
            self._executor.submit(
                self.execute_job_sync,
                job_id,
                reporting_report,
            )
        except RuntimeError:
            # Shutdown landed between the check above and this submit.
            logger.warning(
                "Executor shut down while submitting AI job '%s'; job remains " "PENDING for stale-job recovery.",
                job_id,
            )

    # ==========================================================
    # Synchronous Execution Logic
    # ==========================================================

    def execute_job_sync(
        self,
        job_id: str,
        reporting_report: ReportingReport,
        ai_manager_override: AIManager | None = None,
    ) -> bool:
        """
        Execute an AI job synchronously with atomic claiming and failure isolation.

        Returns True if the job reached READY, False if FAILED or retrying.
        """
        connection = ConnectionFactory.create_connection()
        connection.connect()
        job_repo = AIJobRepository(connection)
        report_repo = AIReportRepository(connection)
        manager = ai_manager_override or self._ai_manager

        try:
            # 1. Inspect job
            job = job_repo.get_by_job_id(job_id)
            if job is None:
                logger.error("AI job '%s' not found in database.", job_id)
                return False

            if job.status == AIJobStatus.READY:
                logger.info("AI job '%s' is already READY. Skipping.", job_id)
                return True

            # 2. Atomic claim if in PENDING
            if job.status == AIJobStatus.PENDING:
                now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                claim_query = f"""
                UPDATE {job_repo.TABLE_NAME}
                SET status = ?,
                    started_at = ?,
                    attempt_count = attempt_count + 1,
                    updated_at = ?
                WHERE job_id = ? AND status = ?;
                """
                cursor = job_repo.execute(
                    claim_query,
                    (
                        AIJobStatus.GENERATING.value,
                        now_str,
                        now_str,
                        job_id,
                        AIJobStatus.PENDING.value,
                    ),
                )
                if cursor.rowcount == 0:
                    logger.warning(
                        "AI job '%s' could not be claimed (already claimed or running).",
                        job_id,
                    )
                    return False
                job = job_repo.get_by_job_id(job_id)

            logger.info(
                "Starting AI generation for job '%s' (Attempt %d/%d)...",
                job_id,
                job.attempt_count,
                job.max_attempts,
            )

            # Reconstruct authoritative AIDataContext across asynchronous worker boundary
            from src.ai.context_builder import AIDataContextBuilder

            data_context = AIDataContextBuilder.build_from_database(
                connection=connection,
                pipeline_run_id=job.pipeline_run_id,
                user_id=job.user_id,
            )

            # 3. Execute AI Insight generation
            attempt_started = time.monotonic()
            ai_result = manager.generate_ai_report(
                reporting_report,
                data_context=data_context,
            )
            attempt_seconds = time.monotonic() - attempt_started

            # 4. Handle Result
            if ai_result.success and ai_result.ai_report is not None:
                # Save generated AI report with durable provenance
                src_v_id = data_context.source.version_id if data_context else None
                cln_v_id = data_context.analytics.cleaned_version_id if data_context else None
                cln_exec_id = data_context.lineage.cleaning_execution_id if data_context else None

                report_repo.save_ai_report(
                    job_id=job.job_id,
                    pipeline_run_id=job.pipeline_run_id,
                    ai_report=ai_result.ai_report,
                    user_id=job.user_id,
                    report_id=job.report_id,
                    source_version_id=src_v_id,
                    cleaned_version_id=cln_v_id,
                    cleaning_execution_id=cln_exec_id,
                    context_version="v1.0",
                )
                # Mark job as READY
                job_repo.mark_ready(job.job_id)
                logger.info(
                    "AI job '%s' completed successfully -> READY.",
                    job_id,
                )
                return True
            else:
                # Handle generation error
                error_obj = ai_result.error or RuntimeError("AI generation returned no report.")
                self._handle_failure(
                    job=job,
                    error=error_obj,
                    reporting_report=reporting_report,
                    job_repo=job_repo,
                    attempt_seconds=attempt_seconds,
                )
                return False

        except Exception as exc:
            logger.exception(
                "Unexpected exception during AI job '%s' execution.",
                job_id,
            )
            # Re-fetch job to ensure up-to-date state
            current_job = job_repo.get_by_job_id(job_id)
            if current_job is not None:
                self._handle_failure(
                    job=current_job,
                    error=exc,
                    reporting_report=reporting_report,
                    job_repo=job_repo,
                )
            return False

        finally:
            connection.close()

    # ==========================================================
    # Failure & Retry Handling
    # ==========================================================

    def _handle_failure(
        self,
        job: AIJob,
        error: Exception | str,
        reporting_report: ReportingReport,
        job_repo: AIJobRepository,
        attempt_seconds: float | None = None,
    ) -> None:
        """
        Evaluate retry eligibility and transition job to PENDING (retry) or FAILED.
        """
        error_msg = str(error)
        category = self._classify_error(error)

        is_retryable = category in {
            AIFailureCategory.TIMEOUT,
            AIFailureCategory.PROVIDER_UNAVAILABLE,
            AIFailureCategory.MODEL_ERROR,
        }

        if is_retryable and self._timeout_is_systematic(category, attempt_seconds):
            # A timeout that consumed the entire budget is a capacity limit,
            # not a transient blip: the next attempt runs the same prompt, on
            # the same hardware, against the same budget, and fails the same
            # way. Retrying costs another full AI_TIMEOUT of CPU per attempt -
            # on this deployment roughly five minutes each - and still ends in
            # a permanent failure.
            #
            # Note the deliberate asymmetry: a timeout that failed EARLY is
            # still retried, because that one really can be transient.
            is_retryable = False
            error_msg = (
                f"{error_msg} (inference used {attempt_seconds:.1f}s of the "
                f"{config.AI_TIMEOUT:.0f}s AI_TIMEOUT budget; treating as a "
                "capacity limit rather than a transient failure. Raise "
                "AI_TIMEOUT, reduce AI_MAX_TOKENS/AI_CONTEXT_WINDOW, or use "
                "faster inference hardware.)"
            )
            logger.error(
                "AI job '%s' exhausted its inference budget (%.1fs of %.0fs). "
                "Not retrying: an identical retry would fail identically.",
                job.job_id,
                attempt_seconds,
                config.AI_TIMEOUT,
            )

        if is_retryable and job.attempt_count < job.max_attempts:
            # Schedule Retry
            logger.warning(
                "AI job '%s' failed with retryable error (%s). " "Attempt %d/%d. Scheduling retry...",
                job.job_id,
                category.value,
                job.attempt_count,
                job.max_attempts,
            )
            job_repo.schedule_retry(
                job_id=job.job_id,
                error=error_msg,
                failure_category=category,
            )

            # Compute exponential backoff delay
            base_delay = getattr(config, "AI_RETRY_BASE_DELAY", 2.0)
            backoff_delay = base_delay * (2 ** (job.attempt_count - 1))

            # Dispatch delayed retry task
            self._schedule_retry_timer(
                delay=backoff_delay,
                job_id=job.job_id,
                reporting_report=reporting_report,
            )
        else:
            # Permanent Failure
            logger.error(
                "AI job '%s' failed permanently (%s). " "Attempts exhausted or non-retryable. Marking FAILED.",
                job.job_id,
                category.value,
            )
            job_repo.mark_failed(
                job_id=job.job_id,
                error=error_msg,
                failure_category=category,
            )

    def _schedule_retry_timer(
        self,
        delay: float,
        job_id: str,
        reporting_report: ReportingReport,
    ) -> None:
        """
        Schedule a delayed retry, tracking the timer so shutdown() can cancel it.
        """
        with self._lock:
            if self._is_shutdown:
                logger.debug(
                    "Executor is shut down; not scheduling retry for AI job '%s'.",
                    job_id,
                )
                return

        timer: threading.Timer

        def _fire() -> None:
            with self._lock:
                self._retry_timers.discard(timer)
                if self._is_shutdown:
                    return
            self.submit_job(job_id, reporting_report)

        timer = threading.Timer(delay, _fire)
        timer.daemon = True

        with self._lock:
            self._retry_timers.add(timer)

        timer.start()

    #: Fraction of AI_TIMEOUT above which a timeout counts as systematic
    #: rather than transient.
    TIMEOUT_EXHAUSTION_RATIO = 0.95

    @classmethod
    def _timeout_is_systematic(
        cls,
        category: AIFailureCategory,
        attempt_seconds: float | None,
    ) -> bool:
        """
        Return True when a TIMEOUT reflects capacity rather than bad luck.

        Distinguishes the two cases by how much of the budget the attempt
        actually used. A request that ran to the full AI_TIMEOUT was still
        making progress when it was cut off - more time is what it needed, so
        an identical retry is futile. A request that failed after a fraction of
        the budget hit something transient and is worth retrying.

        Returns False when the duration is unknown, so the previous
        retry-everything behaviour is what happens without evidence.
        """
        if category is not AIFailureCategory.TIMEOUT:
            return False

        if attempt_seconds is None:
            return False

        budget = float(getattr(config, "AI_TIMEOUT", 0.0) or 0.0)

        if budget <= 0:
            return False

        return attempt_seconds >= budget * cls.TIMEOUT_EXHAUSTION_RATIO

    @staticmethod
    def _iter_error_chain(error: Exception | str) -> list[Exception | str]:
        """
        Walk an exception and its __cause__ / __context__ chain.

        Domain code wraps provider failures (for example
        `raise RuntimeError("LLM generation failed.") from httpx.ReadTimeout`),
        so the signal needed for classification lives on the cause, not on the
        outermost exception.
        """
        if not isinstance(error, Exception):
            return [error]

        chain: list[Exception | str] = []
        seen: set[int] = set()
        current: BaseException | None = error

        while current is not None and id(current) not in seen:
            seen.add(id(current))
            chain.append(current)  # type: ignore[arg-type]
            current = current.__cause__ or current.__context__

        return chain

    def _classify_error(self, error: Exception | str) -> AIFailureCategory:
        """
        Classify error into domain failure categories.

        Inspects the full exception chain so that a wrapped provider timeout is
        still classified as TIMEOUT (and therefore retryable) rather than
        falling through to a permanent SYSTEM_ERROR.
        """
        chain = self._iter_error_chain(error)

        messages = " ".join(str(link).lower() for link in chain)
        type_names = " ".join(type(link).__name__.lower() for link in chain if isinstance(link, Exception))
        haystack = f"{messages} {type_names}"

        if "timeout" in haystack or "timed out" in haystack:
            return AIFailureCategory.TIMEOUT
        if (
            "connection" in haystack
            or "refused" in haystack
            or "unavailable" in haystack
            or "responseerror" in haystack
            or "connecterror" in haystack
        ):
            return AIFailureCategory.PROVIDER_UNAVAILABLE
        if "parse" in haystack or "invalid" in haystack or "valueerror" in type_names or "typeerror" in type_names:
            return AIFailureCategory.MODEL_ERROR
        return AIFailureCategory.SYSTEM_ERROR

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def shutdown(
        self,
        wait: bool = False,
        cancel_pending: bool = False,
    ) -> None:
        """
        Shutdown worker thread pool and cancel any pending retry timers.

        Parameters
        ----------
        wait:
            Block until in-flight jobs finish.
        cancel_pending:
            Drop queued jobs that have not started executing yet. Left False by
            default to preserve the previous fire-and-forget semantics for
            application shutdown; test teardown passes True.
        """
        with self._lock:
            self._is_shutdown = True
            timers = list(self._retry_timers)
            self._retry_timers.clear()

        for timer in timers:
            timer.cancel()

        self._executor.shutdown(
            wait=wait,
            cancel_futures=cancel_pending,
        )

        with _REGISTRY_LOCK:
            _ACTIVE_EXECUTORS.discard(self)
