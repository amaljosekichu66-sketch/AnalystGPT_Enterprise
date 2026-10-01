"""
AI Job repository for AnalystGPT Enterprise.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from src.ai.models import AIFailureCategory, AIJob, AIJobStatus
from src.core import config
from src.database.database_connection import DatabaseConnection
from src.database.repositories.base_repository import BaseRepository

#: Stored on jobs that were interrupted (restart, lost worker) before finishing.
INTERRUPTED_ERROR = "Interrupted before completion. Run the pipeline again to regenerate insights."


def pending_lease() -> float:
    """Lease for a job waiting for a worker (L12)."""
    return time.time() + int(config.AI_JOB_PENDING_TTL_SECONDS)


def running_lease() -> float:
    """Lease for one generation attempt (L12)."""
    return time.time() + float(config.AI_TIMEOUT) + int(config.AI_JOB_LEASE_MARGIN_SECONDS)


class AIJobRepository(BaseRepository):
    """
    Coordinates database persistence for AI generation jobs.
    """

    TABLE_NAME = "ai_jobs"

    def __init__(self, connection: DatabaseConnection) -> None:
        super().__init__(connection)
        #: Set by `recover_stale_jobs`: the jobs it put back to PENDING.
        self.requeued_job_ids: list[str] = []

    # ==========================================================
    # Create / Idempotent Create
    # ==========================================================

    def create_job(
        self,
        job_id: str,
        pipeline_run_id: int,
        user_id: int | None = None,
        report_id: int | None = None,
        provider: str = "ollama",
        model: str = "gemma3:4b",
        max_attempts: int = 3,
        report_payload: str | None = None,
    ) -> AIJob:
        """
        Create a new AI job idempotently.

        If a job already exists for the given pipeline_run_id, returns the existing job.
        """
        # Idempotency check: check if job already exists for pipeline_run_id
        existing = self.get_by_pipeline_run_id(pipeline_run_id, user_id=user_id)
        if existing is not None:
            return existing

        now = datetime.now(UTC).isoformat()

        query = f"""
        INSERT INTO {self.TABLE_NAME} (
            job_id,
            pipeline_run_id,
            user_id,
            report_id,
            status,
            provider,
            model,
            attempt_count,
            max_attempts,
            created_at,
            updated_at,
            lease_expires_at,
            report_payload
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        try:
            record_id = self.insert_and_return_id(
                query,
                (
                    job_id,
                    pipeline_run_id,
                    user_id,
                    report_id,
                    AIJobStatus.PENDING.value,
                    provider,
                    model,
                    0,
                    max_attempts,
                    now,
                    now,
                    pending_lease(),
                    report_payload,
                ),
            )

            job = self.get_by_id(record_id)
            if job is not None:
                return AIJob.from_dict(job)

            return AIJob(
                id=record_id,
                job_id=job_id,
                pipeline_run_id=pipeline_run_id,
                user_id=user_id,
                report_id=report_id,
                status=AIJobStatus.PENDING,
                provider=provider,
                model=model,
                attempt_count=0,
                max_attempts=max_attempts,
                created_at=now,
                updated_at=now,
            )
        except Exception:
            # In case of concurrent insert race condition, return the existing record
            existing_after_race = self.get_by_pipeline_run_id(pipeline_run_id, user_id=user_id)
            if existing_after_race is not None:
                return existing_after_race
            raise

    # ==========================================================
    # Getters & Lookups
    # ==========================================================

    def get_by_job_id(
        self,
        job_id: str,
        user_id: int | None = None,
    ) -> AIJob | None:
        """
        Retrieve an AI job by its UUID string with optional user scoping.
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE job_id = ? AND user_id = ?;
            """
            row = self.fetch_one(query, (job_id, user_id))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE job_id = ?;
            """
            row = self.fetch_one(query, (job_id,))

        if row is None:
            return None

        return AIJob.from_dict(row)

    def get_by_pipeline_run_id(
        self,
        pipeline_run_id: int,
        user_id: int | None = None,
    ) -> AIJob | None:
        """
        Retrieve an AI job by pipeline run ID with optional user scoping.
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE pipeline_run_id = ? AND user_id = ?;
            """
            row = self.fetch_one(query, (pipeline_run_id, user_id))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE pipeline_run_id = ?;
            """
            row = self.fetch_one(query, (pipeline_run_id,))

        if row is None:
            return None

        return AIJob.from_dict(row)

    def get_by_report_id(
        self,
        report_id: int,
        user_id: int | None = None,
    ) -> AIJob | None:
        """
        Retrieve an AI job by its associated report_id with optional user scoping.
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE report_id = ? AND user_id = ?;
            """
            row = self.fetch_one(query, (report_id, user_id))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE report_id = ?;
            """
            row = self.fetch_one(query, (report_id,))

        if row is None:
            return None

        return AIJob.from_dict(row)

    def get_latest_for_user(
        self,
        user_id: int | None = None,
    ) -> AIJob | None:
        """
        Retrieve the latest AI job for a user (or globally if user_id is None).
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1;
            """
            row = self.fetch_one(query, (user_id,))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            ORDER BY id DESC
            LIMIT 1;
            """
            row = self.fetch_one(query)

        if row is None:
            return None

        return AIJob.from_dict(row)

    def count_active_for_user(self, user_id: int) -> int:
        """Unfinished (PENDING or GENERATING) jobs owned by the user (M7)."""
        row = self.fetch_one(
            f"SELECT COUNT(*) AS active FROM {self.TABLE_NAME} WHERE user_id = ? AND status IN (?, ?);",
            (user_id, AIJobStatus.PENDING.value, AIJobStatus.GENERATING.value),
        )
        return int((row or {}).get("active") or 0)

    # ==========================================================
    # Atomic Claim & Concurrency
    # ==========================================================

    def claim_next_pending_job(self) -> AIJob | None:
        """
        Atomically claim the next available PENDING job.

        Transitions status from PENDING to GENERATING and increments attempt_count.
        Returns the claimed AIJob, or None if no pending job was successfully claimed.
        """
        # Find candidate pending job
        candidate_query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        WHERE status = '{AIJobStatus.PENDING.value}'
        ORDER BY id ASC
        LIMIT 1;
        """
        candidate = self.fetch_one(candidate_query)
        if candidate is None:
            return None

        now = datetime.now(UTC).isoformat()
        job_id = candidate["job_id"]

        # Atomic conditional update
        update_query = f"""
        UPDATE {self.TABLE_NAME}
        SET status = ?,
            started_at = ?,
            attempt_count = attempt_count + 1,
            updated_at = ?,
            lease_expires_at = ?
        WHERE job_id = ? AND status = ?;
        """

        cursor = self.execute(
            update_query,
            (
                AIJobStatus.GENERATING.value,
                now,
                now,
                running_lease(),
                job_id,
                AIJobStatus.PENDING.value,
            ),
        )

        if cursor.rowcount > 0:
            # Claim succeeded
            updated = self.get_by_job_id(job_id)
            return updated

        return None

    # ==========================================================
    # State Transitions & Updates
    # ==========================================================

    def mark_ready(
        self,
        job_id: str,
    ) -> bool:
        """
        Transition job to READY state upon successful AI generation.
        """
        now = datetime.now(UTC).isoformat()
        query = f"""
        UPDATE {self.TABLE_NAME}
        SET status = ?,
            completed_at = ?,
            error = NULL,
            failure_category = NULL,
            updated_at = ?,
            lease_expires_at = NULL
        WHERE job_id = ? AND status = ?;
        """
        cursor = self.execute(
            query,
            (
                AIJobStatus.READY.value,
                now,
                now,
                job_id,
                AIJobStatus.GENERATING.value,
            ),
        )
        return cursor.rowcount > 0

    def mark_failed(
        self,
        job_id: str,
        error: str,
        failure_category: AIFailureCategory | str | None = None,
    ) -> bool:
        """
        Transition an unfinished (PENDING or GENERATING) job to FAILED.

        Conditional (L12): a job that already reached READY or FAILED is left
        alone, so a late failure cannot overwrite a finished result.
        """
        now = datetime.now(UTC).isoformat()
        category_str = (
            failure_category.value
            if isinstance(failure_category, AIFailureCategory)
            else (str(failure_category) if failure_category else None)
        )
        query = f"""
        UPDATE {self.TABLE_NAME}
        SET status = ?,
            completed_at = ?,
            error = ?,
            failure_category = ?,
            updated_at = ?,
            lease_expires_at = NULL
        WHERE job_id = ? AND status IN (?, ?);
        """
        cursor = self.execute(
            query,
            (
                AIJobStatus.FAILED.value,
                now,
                error,
                category_str,
                now,
                job_id,
                AIJobStatus.PENDING.value,
                AIJobStatus.GENERATING.value,
            ),
        )
        return cursor.rowcount > 0

    def schedule_retry(
        self,
        job_id: str,
        error: str,
        failure_category: AIFailureCategory | str | None = None,
    ) -> bool:
        """
        Transition a GENERATING (automatic) or FAILED / CANCELLED (manual) job back to PENDING.

        Conditional (L12): READY and already-PENDING jobs are not touched.
        """
        now = datetime.now(UTC).isoformat()
        category_str = (
            failure_category.value
            if isinstance(failure_category, AIFailureCategory)
            else (str(failure_category) if failure_category else None)
        )
        query = f"""
        UPDATE {self.TABLE_NAME}
        SET status = ?,
            error = ?,
            failure_category = ?,
            updated_at = ?,
            lease_expires_at = ?
        WHERE job_id = ? AND status IN (?, ?, ?);
        """
        cursor = self.execute(
            query,
            (
                AIJobStatus.PENDING.value,
                error,
                category_str,
                now,
                pending_lease(),
                job_id,
                AIJobStatus.GENERATING.value,
                AIJobStatus.FAILED.value,
                AIJobStatus.CANCELLED.value,
            ),
        )
        return cursor.rowcount > 0

    def list_jobs_scoped(
        self,
        user_id: int | None = None,
        limit: int = 50,
    ) -> list[AIJob]:
        """
        List AI jobs with optional user scoping.
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?;
            """
            rows = self.fetch_all(query, (user_id, limit))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            ORDER BY id DESC
            LIMIT ?;
            """
            rows = self.fetch_all(query, (limit,))

        return [AIJob.from_dict(row) for row in rows]

    def get_report_payload(self, job_id: str) -> str | None:
        """The persisted ReportingReport JSON the job runs from (P2-01), if any."""
        row = self.fetch_one(f"SELECT report_payload FROM {self.TABLE_NAME} WHERE job_id = ?;", (job_id,))
        return None if row is None else row.get("report_payload")

    def cancel(self, job_id: str) -> bool:
        """Cancel an unfinished job (P2-02). A worker's later result is discarded."""
        now = datetime.now(UTC).isoformat()
        cursor = self.execute(
            f"""
            UPDATE {self.TABLE_NAME}
            SET status = ?, completed_at = ?, updated_at = ?, lease_expires_at = NULL
            WHERE job_id = ? AND status IN (?, ?);
            """,
            (
                AIJobStatus.CANCELLED.value,
                now,
                now,
                job_id,
                AIJobStatus.PENDING.value,
                AIJobStatus.GENERATING.value,
            ),
        )
        return cursor.rowcount > 0

    def recover_stale_jobs(self, ignore_lease: bool = False) -> int:
        """
        Bring interrupted jobs back to a state that will finish (L12, P2-02).

        "Interrupted" means unfinished with an expired lease, or - with
        `ignore_lease`, used at startup of a single-worker deployment - every
        unfinished job, since no other process can be running it.

        - Jobs with attempts left and a persisted report payload go back to
          PENDING with a fresh lease. Their ids are left in
          `requeued_job_ids` for the caller to dispatch.
        - Every other interrupted job (attempts exhausted, or created before
          payloads were persisted) is marked FAILED with a retryable reason.

        Returns the number of jobs requeued or failed.
        """
        now = time.time()
        now_iso = datetime.now(UTC).isoformat()
        lease_clause = "" if ignore_lease else "AND (lease_expires_at IS NULL OR lease_expires_at < ?)"
        lease_args: tuple = () if ignore_lease else (now,)
        unfinished = (AIJobStatus.PENDING.value, AIJobStatus.GENERATING.value)

        rows = self.fetch_all(
            f"""
            SELECT job_id FROM {self.TABLE_NAME}
            WHERE status IN (?, ?) {lease_clause}
              AND attempt_count < max_attempts AND report_payload IS NOT NULL;
            """,
            (*unfinished, *lease_args),
        )
        requeued = [row["job_id"] for row in rows]
        for job_id in requeued:
            self.execute(
                f"""
                UPDATE {self.TABLE_NAME}
                SET status = ?, error = ?, updated_at = ?, lease_expires_at = ?
                WHERE job_id = ? AND status IN (?, ?);
                """,
                (
                    AIJobStatus.PENDING.value,
                    "Requeued after an interruption.",
                    now_iso,
                    pending_lease(),
                    job_id,
                    *unfinished,
                ),
            )

        cursor = self.execute(
            f"""
            UPDATE {self.TABLE_NAME}
            SET status = ?, failure_category = ?, error = ?, completed_at = ?, updated_at = ?,
                lease_expires_at = NULL
            WHERE status IN (?, ?) {lease_clause}
              AND NOT (attempt_count < max_attempts AND report_payload IS NOT NULL);
            """,
            (
                AIJobStatus.FAILED.value,
                AIFailureCategory.SYSTEM_ERROR.value,
                INTERRUPTED_ERROR,
                now_iso,
                now_iso,
                *unfinished,
                *lease_args,
            ),
        )
        self.requeued_job_ids = requeued
        failed = (cursor.rowcount if cursor else 0) or 0
        return len(requeued) + failed
