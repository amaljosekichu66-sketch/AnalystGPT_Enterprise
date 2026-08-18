"""
AI Job Service for AnalystGPT Enterprise.

Coordinates domain-level AI job lifecycle management, retrieval,
and retry orchestration.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import uuid
from typing import Any

from src.ai.exceptions import AIJobNotFoundError, AIStateTransitionError
from src.ai.job_executor import AIJobExecutor
from src.ai.models import AIJob, AIJobStatus
from src.core import config
from src.core.logger import logger
from src.database.connection_factory import ConnectionFactory
from src.database.database_connection import DatabaseConnection
from src.database.repositories.ai_job_repository import AIJobRepository
from src.database.repositories.ai_report_repository import AIReportRepository
from src.reporting.reporting_report import ReportingReport


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

    def _get_connection(self) -> DatabaseConnection:
        if self._connection is not None:
            if self._connection.get_connection() is None:
                self._connection.connect()
            return self._connection
        conn = ConnectionFactory.create_connection()
        conn.connect()
        return conn

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
        """
        conn = self._get_connection()
        job_repo = AIJobRepository(conn)

        eff_provider = provider or config.LLM_PROVIDER
        eff_model = model or config.OLLAMA_MODEL
        eff_max_attempts = (
            max_attempts
            if max_attempts is not None
            else getattr(config, "AI_MAX_RETRIES", 3)
        )

        job_id = f"ai_job_{uuid.uuid4().hex[:12]}"

        job = job_repo.create_job(
            job_id=job_id,
            pipeline_run_id=pipeline_run_id,
            user_id=user_id,
            report_id=report_id,
            provider=eff_provider,
            model=eff_model,
            max_attempts=eff_max_attempts,
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
        conn = self._get_connection()
        job_repo = AIJobRepository(conn)
        return job_repo.get_by_job_id(job_id, user_id=user_id)

    def get_job_with_report(
        self,
        job_id: str,
        user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve an AI job and its generated report (if READY).
        """
        conn = self._get_connection()
        job_repo = AIJobRepository(conn)
        report_repo = AIReportRepository(conn)

        job = job_repo.get_by_job_id(job_id, user_id=user_id)
        if job is None:
            return None

        job_dict = job.to_dict()

        if job.status == AIJobStatus.READY:
            ai_report_data = report_repo.get_by_job_id(job_id, user_id=user_id)
            job_dict["ai_report"] = ai_report_data
        else:
            job_dict["ai_report"] = None

        return job_dict

    def get_latest_job_for_user(
        self,
        user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve latest AI job and report for the given user.
        """
        conn = self._get_connection()
        job_repo = AIJobRepository(conn)
        report_repo = AIReportRepository(conn)

        job = job_repo.get_latest_for_user(user_id=user_id)
        if job is None:
            return None

        job_dict = job.to_dict()

        if job.status == AIJobStatus.READY:
            ai_report_data = report_repo.get_by_job_id(
                job.job_id, user_id=user_id
            )
            job_dict["ai_report"] = ai_report_data
        else:
            job_dict["ai_report"] = None

        return job_dict

    # ==========================================================
    # Retry Trigger
    # ==========================================================

    def retry_job(
        self,
        job_id: str,
        reporting_report: ReportingReport | None = None,
        user_id: int | None = None,
    ) -> AIJob:
        """
        Manually trigger a retry for a FAILED job.
        """
        conn = self._get_connection()
        job_repo = AIJobRepository(conn)

        job = job_repo.get_by_job_id(job_id, user_id=user_id)
        if job is None:
            raise AIJobNotFoundError(f"AI job '{job_id}' not found.")

        if job.status != AIJobStatus.FAILED:
            raise AIStateTransitionError(
                f"Cannot retry job in '{job.status.value}' state. "
                "Only FAILED jobs can be retried."
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

    def recover_stale_jobs(self) -> int:
        """
        Recovers jobs stuck in GENERATING or PENDING upon restart.
        """
        repo = AIJobRepository(self._get_connection())
        return repo.recover_stale_jobs()
