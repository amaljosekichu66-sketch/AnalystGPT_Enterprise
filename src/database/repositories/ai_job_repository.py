"""
AI Job repository for AnalystGPT Enterprise.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.ai.models import AIFailureCategory, AIJob, AIJobStatus
from src.database.database_connection import DatabaseConnection
from src.database.repositories.base_repository import BaseRepository


class AIJobRepository(BaseRepository):
    """
    Coordinates database persistence for AI generation jobs.
    """

    TABLE_NAME = "ai_jobs"

    def __init__(self, connection: DatabaseConnection) -> None:
        super().__init__(connection)

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
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
            updated_at = ?
        WHERE job_id = ? AND status = ?;
        """

        cursor = self.execute(
            update_query,
            (
                AIJobStatus.GENERATING.value,
                now,
                now,
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
            updated_at = ?
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
        Transition job to FAILED state.
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
            updated_at = ?
        WHERE job_id = ?;
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
        Transition a GENERATING job back to PENDING for retry.
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
            updated_at = ?
        WHERE job_id = ?;
        """
        cursor = self.execute(
            query,
            (
                AIJobStatus.PENDING.value,
                error,
                category_str,
                now,
                job_id,
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

    def recover_stale_jobs(self) -> int:
        """
        Recover stale jobs left in GENERATING state (e.g. from an abrupt process termination).

        - Jobs with attempt_count < max_attempts are reset to PENDING for retry.
        - Jobs with attempt_count >= max_attempts are marked FAILED (SYSTEM_ERROR).

        Returns total count of recovered jobs.
        """
        now = datetime.now(UTC).isoformat()

        # 1. Reset retryable GENERATING jobs to PENDING
        retryable_query = f"""
        UPDATE {self.TABLE_NAME}
        SET status = '{AIJobStatus.PENDING.value}',
            error = 'Recovered from interrupted process state',
            updated_at = ?
        WHERE status = '{AIJobStatus.GENERATING.value}'
          AND attempt_count < max_attempts;
        """
        cursor1 = self.execute(retryable_query, (now,))
        recovered_pending = cursor1.rowcount if cursor1 else 0

        # 2. Mark exhausted GENERATING jobs as FAILED
        exhausted_query = f"""
        UPDATE {self.TABLE_NAME}
        SET status = '{AIJobStatus.FAILED.value}',
            failure_category = '{AIFailureCategory.SYSTEM_ERROR.value}',
            error = 'Process terminated while job was executing (attempts exhausted)',
            completed_at = ?,
            updated_at = ?
        WHERE status = '{AIJobStatus.GENERATING.value}'
          AND attempt_count >= max_attempts;
        """
        cursor2 = self.execute(exhausted_query, (now, now))
        exhausted_failed = cursor2.rowcount if cursor2 else 0

        return (recovered_pending or 0) + (exhausted_failed or 0)
