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
        logger.info(
            "Submitting AI job '%s' to background worker pool...",
            job_id,
        )
        self._executor.submit(
            self.execute_job_sync,
            job_id,
            reporting_report,
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
            ai_result = manager.generate_ai_report(
                reporting_report,
                data_context=data_context,
            )

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
                error_obj = ai_result.error or RuntimeError(
                    "AI generation returned no report."
                )
                self._handle_failure(
                    job=job,
                    error=error_obj,
                    reporting_report=reporting_report,
                    job_repo=job_repo,
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

        if is_retryable and job.attempt_count < job.max_attempts:
            # Schedule Retry
            logger.warning(
                "AI job '%s' failed with retryable error (%s). "
                "Attempt %d/%d. Scheduling retry...",
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
            timer = threading.Timer(
                backoff_delay,
                self.submit_job,
                args=(job.job_id, reporting_report),
            )
            timer.daemon = True
            timer.start()
        else:
            # Permanent Failure
            logger.error(
                "AI job '%s' failed permanently (%s). "
                "Attempts exhausted or non-retryable. Marking FAILED.",
                job.job_id,
                category.value,
            )
            job_repo.mark_failed(
                job_id=job.job_id,
                error=error_msg,
                failure_category=category,
            )

    def _classify_error(self, error: Exception | str) -> AIFailureCategory:
        """
        Classify error into domain failure categories.
        """
        err_str = str(error).lower()
        err_type = type(error).__name__ if isinstance(error, Exception) else ""

        if "timeout" in err_str or "timed out" in err_str:
            return AIFailureCategory.TIMEOUT
        if (
            "connection" in err_str
            or "refused" in err_str
            or "unavailable" in err_str
            or "responseerror" in err_str
        ):
            return AIFailureCategory.PROVIDER_UNAVAILABLE
        if (
            "parse" in err_str
            or "invalid" in err_str
            or "valuerror" in err_type.lower()
            or "typeerror" in err_type.lower()
        ):
            return AIFailureCategory.MODEL_ERROR
        return AIFailureCategory.SYSTEM_ERROR

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def shutdown(self, wait: bool = False) -> None:
        """
        Shutdown worker thread pool and cancel any pending timers.
        """
        self._executor.shutdown(wait=wait)
