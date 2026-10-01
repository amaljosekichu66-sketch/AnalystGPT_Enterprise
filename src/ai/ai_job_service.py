"""
AI Job Service for AnalystGPT Enterprise.

Coordinates domain-level AI job lifecycle management, retrieval,
and retry orchestration.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from src.ai.exceptions import AIJobNotFoundError, AIRetryUnavailableError, AIStateTransitionError
from src.ai.job_executor import AIJobExecutor
from src.ai.models import AIJob, AIJobStatus
from src.core import config
from src.core.exceptions import TooManyConcurrentJobsError
from src.core.logger import logger
from src.database.connection_factory import ConnectionFactory
from src.database.database_connection import DatabaseConnection
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.database.schema_manager import SchemaManager
from src.reporting.reporting_report import ReportingReport

#: States a manual retry may start from.
_RETRYABLE = {AIJobStatus.FAILED, AIJobStatus.CANCELLED}


class AIJobService:
    """
    Coordinates AI generation job operations.
    """

    def __init__(
        self,
        connection: DatabaseConnection | None = None,
        job_executor: AIJobExecutor | None = None,
    ) -> None:
        self._connection = connection
        self._job_executor = job_executor

    @contextmanager
    def _session(self) -> Iterator[DatabaseConnection]:
        """
        A connection for one operation (P2-20).

        An injected connection is reused and left open (its owner closes it);
        otherwise a fresh one is opened and always closed. Every call used to
        open a connection that was never closed.
        """
        if self._connection is not None:
            if self._connection.get_connection() is None:
                self._connection.connect()
            yield self._connection
            return
        conn = ConnectionFactory.create_connection()
        conn.connect()
        try:
            yield conn
        finally:
            conn.disconnect()

    def ensure_capacity(self, user_id: int | None) -> None:
        """
        Refuse new AI work for a user who already has the maximum unfinished (M7).

        Sequential pipeline runs never hit the concurrent-job cap, yet each
        queued an LLM job on a shared 4-worker pool: one account could starve
        every other user's insights.
        """
        if user_id is None:
            return
        limit = max(1, int(config.MAX_ACTIVE_AI_JOBS_PER_USER))
        # Interrupted jobs must not hold the quota forever (L12).
        self.recover_stale_jobs()
        with self._session() as conn:
            active = AIJobRepository(conn).count_active_for_user(user_id)
        if active >= limit:
            raise TooManyConcurrentJobsError(
                f"You already have {limit} AI insight jobs in progress. Wait for one to finish and retry."
            )

    # ==========================================================
    # Create / Dispatch
    # ==========================================================

    def create_and_dispatch_job(
        self,
        pipeline_run_id: int,
        reporting_report: ReportingReport,
        user_id: int | None = None,
        report_id: int | None = None,
        provider: str | None = None,
        model: str | None = None,
        max_attempts: int | None = None,
    ) -> AIJob:
        """
        Create a persistent AI job idempotently and dispatch background execution.

        The job's input (the ReportingReport) is persisted with it, so a
        retry or a restart can run it again (P2-01, P2-02).
        """
        eff_provider = provider or config.LLM_PROVIDER
        eff_model = model or config.OLLAMA_MODEL
        eff_max_attempts = max_attempts if max_attempts is not None else getattr(config, "AI_MAX_RETRIES", 3)

        job_id = f"ai_job_{uuid.uuid4().hex[:12]}"

        with self._session() as conn:
            job = AIJobRepository(conn).create_job(
                job_id=job_id,
                pipeline_run_id=pipeline_run_id,
                user_id=user_id,
                report_id=report_id,
                provider=eff_provider,
                model=eff_model,
                max_attempts=eff_max_attempts,
                report_payload=reporting_report.to_payload(),
            )

        logger.info(
            "Created AI job '%s' (Status=%s) for Pipeline Run %d.",
            job.job_id,
            job.status.value,
            pipeline_run_id,
        )

        # Dispatch background worker if executor configured
        if self._job_executor is not None and job.status == AIJobStatus.PENDING:
            self._job_executor.submit_job(
                job_id=job.job_id,
                reporting_report=reporting_report,
            )

        return job

    # ==========================================================
    # Getters & Lookups
    # ==========================================================

    def get_job(
        self,
        job_id: str,
        user_id: int | None = None,
    ) -> AIJob | None:
        """
        Retrieve an AI job with ownership scoping.
        """
        with self._session() as conn:
            return AIJobRepository(conn).get_by_job_id(job_id, user_id=user_id)

    def get_job_with_report(
        self,
        job_id: str,
        user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve an AI job and its generated report (if READY).
        """
        with self._session() as conn:
            job = AIJobRepository(conn).get_by_job_id(job_id, user_id=user_id)
            if job is None:
                return None
            return self._with_report(job, AIReportRepository(conn), user_id)

    def get_latest_job_for_user(
        self,
        user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve latest AI job and report for the given user.
        """
        with self._session() as conn:
            job = AIJobRepository(conn).get_latest_for_user(user_id=user_id)
            if job is None:
                return None
            return self._with_report(job, AIReportRepository(conn), user_id)

    def get_job_for_pipeline_run(self, pipeline_run_id: int, user_id: int | None = None) -> dict[str, Any] | None:
        """The AI job of one pipeline run, so a view shows the insights of the dataset on screen (P2-06)."""
        with self._session() as conn:
            job = AIJobRepository(conn).get_by_pipeline_run_id(pipeline_run_id, user_id=user_id)
            if job is None:
                return None
            return self._with_report(job, AIReportRepository(conn), user_id)

    @staticmethod
    def _with_report(job: AIJob, report_repo: AIReportRepository, user_id: int | None) -> dict[str, Any]:
        job_dict = job.to_dict()
        job_dict["ai_report"] = (
            report_repo.get_by_job_id(job.job_id, user_id=user_id) if job.status == AIJobStatus.READY else None
        )
        return job_dict

    # ==========================================================
    # Retry, cancel and recovery
    # ==========================================================

    def retry_job(
        self,
        job_id: str,
        reporting_report: ReportingReport | None = None,
        user_id: int | None = None,
        report_provider: Callable[[AIJob], ReportingReport | None] | None = None,
    ) -> AIJob:
        """
        Run a FAILED or CANCELLED job again (P2-01).

        The input comes from, in order: the caller, `report_provider` (the
        in-memory result cache), or the payload persisted with the job. Only a
        job created before payloads were persisted - with nothing cached - is
        refused, rather than left PENDING forever.
        """
        with self._session() as conn:
            job_repo = AIJobRepository(conn)
            job = job_repo.get_by_job_id(job_id, user_id=user_id)
            if job is None:
                raise AIJobNotFoundError(f"AI job '{job_id}' not found.")

            if job.status not in _RETRYABLE:
                raise AIStateTransitionError(
                    f"Cannot retry job in '{job.status.value}' state. Only FAILED or CANCELLED jobs can be retried."
                )

            self.ensure_capacity(job.user_id)

            if reporting_report is None and report_provider is not None:
                reporting_report = report_provider(job)
            if reporting_report is None:
                payload = job_repo.get_report_payload(job_id)
                reporting_report = ReportingReport.from_payload(payload) if payload else None
            if self._job_executor is not None and reporting_report is None:
                raise AIRetryUnavailableError(
                    "This job's pipeline result is no longer available. Run the pipeline again to regenerate insights."
                )

            job_repo.schedule_retry(
                job_id=job_id,
                error="Manual retry requested",
                failure_category=None,
            )

            updated_job = job_repo.get_by_job_id(job_id, user_id=user_id)
            if updated_job is None:
                raise AIJobNotFoundError(f"AI job '{job_id}' not found after update.")

        if self._job_executor is not None and reporting_report is not None:
            self._job_executor.submit_job(
                job_id=job_id,
                reporting_report=reporting_report,
            )

        return updated_job

    def cancel_job(self, job_id: str, user_id: int | None = None) -> AIJob:
        """
        Cancel a PENDING or GENERATING job (P2-02).

        A generation already running finishes in its worker, but its result
        is discarded: the job's state transitions are conditional.
        """
        with self._session() as conn:
            job_repo = AIJobRepository(conn)
            job = job_repo.get_by_job_id(job_id, user_id=user_id)
            if job is None:
                raise AIJobNotFoundError(f"AI job '{job_id}' not found.")
            if not job_repo.cancel(job_id):
                raise AIStateTransitionError(f"Cannot cancel job in '{job.status.value}' state.")
            cancelled = job_repo.get_by_job_id(job_id, user_id=user_id)
        assert cancelled is not None
        logger.info("AI job '%s' cancelled.", job_id)
        return cancelled

    def recover_stale_jobs(self, ignore_lease: bool = False) -> int:
        """
        Requeue or fail interrupted jobs, then dispatch the requeued ones (P2-02).

        The schema is initialised first: on a fresh database recovery used to
        run before `ai_jobs` existed.
        """
        with self._session() as conn:
            SchemaManager(conn).initialize_schema()
            repo = AIJobRepository(conn)
            count = repo.recover_stale_jobs(ignore_lease=ignore_lease)
            requeued = [(job_id, repo.get_report_payload(job_id)) for job_id in repo.requeued_job_ids]

        if self._job_executor is not None:
            for job_id, payload in requeued:
                if payload:
                    logger.info("Resuming interrupted AI job '%s'.", job_id)
                    self._job_executor.submit_job(job_id=job_id, reporting_report=ReportingReport.from_payload(payload))
        return count
