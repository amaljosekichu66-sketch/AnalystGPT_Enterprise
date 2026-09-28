"""
Cleaning Execution Repository.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Audits all cleaning executions and maps provenance lineage.
"""

from __future__ import annotations

from src.database.database_connection import DatabaseConnection
from src.database.repositories.base_repository import BaseRepository
from src.governance.models import CleaningExecution


class CleaningExecutionRepository(BaseRepository):
    TABLE_NAME = "cleaning_executions"

    def __init__(self, connection: DatabaseConnection) -> None:
        super().__init__(connection)

    def create(self, execution: CleaningExecution) -> int:
        query = """
        INSERT INTO cleaning_executions (
            execution_id,
            pipeline_run_id,
            user_id,
            source_version_id,
            cleaned_version_id,
            config_id,
            execution_status,
            error_message,
            source_row_count,
            cleaned_row_count,
            rows_removed,
            pct_rows_removed,
            source_missing_count,
            cleaned_missing_count,
            source_completeness_pct,
            cleaned_completeness_pct,
            columns_removed,
            affected_columns_detail,
            execution_time_seconds,
            executed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        return self.insert_and_return_id(
            query,
            (
                execution.execution_id,
                execution.pipeline_run_id,
                execution.user_id,
                execution.source_version_id,
                execution.cleaned_version_id,
                execution.config_id,
                execution.execution_status.value,
                execution.error_message,
                execution.source_row_count,
                execution.cleaned_row_count,
                execution.rows_removed,
                execution.pct_rows_removed,
                execution.source_missing_count,
                execution.cleaned_missing_count,
                execution.source_completeness_pct,
                execution.cleaned_completeness_pct,
                execution.columns_removed_json(),
                execution.affected_columns_detail_json(),
                execution.execution_time_seconds,
                execution.executed_at,
            ),
        )

    def get_by_execution_id(self, execution_id: str, user_id: int | None = None) -> dict | None:
        if user_id is not None:
            query = "SELECT * FROM cleaning_executions WHERE execution_id = ? AND user_id = ?;"
            return self.fetch_one(query, (execution_id, user_id))
        query = "SELECT * FROM cleaning_executions WHERE execution_id = ?;"
        return self.fetch_one(query, (execution_id,))

    def get_by_pipeline_run(self, pipeline_run_id: int, user_id: int | None = None) -> dict | None:
        if user_id is not None:
            query = (
                "SELECT * FROM cleaning_executions WHERE pipeline_run_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1;"
            )
            return self.fetch_one(query, (pipeline_run_id, user_id))
        query = "SELECT * FROM cleaning_executions WHERE pipeline_run_id = ? ORDER BY id DESC LIMIT 1;"
        return self.fetch_one(query, (pipeline_run_id,))

    def get_by_source_version(self, source_version_id: str, user_id: int | None = None) -> list[dict]:
        if user_id is not None:
            query = "SELECT * FROM cleaning_executions WHERE source_version_id = ? AND user_id = ? ORDER BY id DESC;"
            return self.fetch_all(query, (source_version_id, user_id))
        query = "SELECT * FROM cleaning_executions WHERE source_version_id = ? ORDER BY id DESC;"
        return self.fetch_all(query, (source_version_id,))

    def get_all(self, user_id: int | None = None) -> list[dict]:
        return self.get_all_scoped(user_id=user_id)
