"""
AI Data Context Builder for AnalystGPT Enterprise.

Sprint 14 Phase 4 — AI Data Context & Analytical Integrity.

Assembles and reconstructs typed AIDataContext entities from either in-memory
pipeline objects or persisted database records (across asynchronous worker boundaries)
with strict multi-user ownership enforcement.
"""

from __future__ import annotations

import json
from typing import Any

from src.ai.context import (
    AIDataContext,
    AnalyticalDataContext,
    CleaningContext,
    LineageContext,
    SourceDataContext,
)
from src.core.logger import logger
from src.database.database_connection import DatabaseConnection
from src.database.repositories.cleaning_execution_repository import CleaningExecutionRepository
from src.database.repositories.dataset_version_repository import DatasetVersionRepository
from src.database.repositories.pipeline_run_repository import PipelineRunRepository
from src.database.repositories.report_repository import ReportRepository
from src.governance.models import CleaningExecution, DatasetVersion, QualityComparison
from src.reporting.reporting_report import ReportingReport


class AIDataContextBuilder:
    """
    Constructs authoritative, typed AIDataContext domain entities.
    """

    @classmethod
    def build_from_pipeline_objects(
        cls,
        source_version: DatasetVersion,
        cleaned_version: DatasetVersion,
        cleaning_execution: CleaningExecution,
        reporting_report: ReportingReport,
        pipeline_run_id: int | None = None,
        user_id: int | None = None,
        report_id: int | None = None,
        quality_comparison: QualityComparison | None = None,
    ) -> AIDataContext:
        """
        Construct an AIDataContext from in-memory pipeline outputs.
        """
        # 1. Source Context
        source_missing = (
            cleaning_execution.source_missing_count
            if cleaning_execution.source_missing_count is not None
            else (quality_comparison.source.total_missing if quality_comparison else 0)
        )
        source_pct_missing = quality_comparison.source.missing_percentage if quality_comparison else 0.0
        source_completeness = (
            cleaning_execution.source_completeness_pct
            if cleaning_execution.source_completeness_pct is not None
            else (quality_comparison.source.completeness_percentage if quality_comparison else 100.0)
        )
        per_col_missing = quality_comparison.source.per_column_missing if quality_comparison else {}

        source_ctx = SourceDataContext(
            version_id=source_version.version_id,
            source_filename=source_version.source_filename,
            row_count=source_version.row_count,
            column_count=source_version.column_count,
            total_missing=source_missing,
            missing_percentage=source_pct_missing,
            completeness_percentage=source_completeness,
            per_column_missing=per_col_missing,
        )

        # 2. Cleaning Context
        rows_removed = (
            cleaning_execution.rows_removed
            if cleaning_execution.rows_removed is not None
            else max(0, source_version.row_count - cleaned_version.row_count)
        )
        pct_rows_removed = (
            cleaning_execution.pct_rows_removed
            if cleaning_execution.pct_rows_removed is not None
            else (round((rows_removed / source_version.row_count) * 100, 4) if source_version.row_count > 0 else 0.0)
        )
        columns_removed = cleaning_execution.columns_removed or []
        affected_cols = (
            list(cleaning_execution.affected_columns_detail.keys())
            if cleaning_execution.affected_columns_detail
            else []
        )

        cleaning_ctx = CleaningContext(
            config_id=cleaning_execution.config_id,
            missing_value_policy=getattr(cleaning_execution, "missing_value_policy", "DROP_ROWS"),
            rows_removed=rows_removed,
            pct_rows_removed=pct_rows_removed,
            columns_removed=columns_removed,
            values_imputed=0,
            affected_columns=affected_cols,
        )

        # 3. Analytical Context
        structured_report = reporting_report.report
        analytics_data = structured_report.analytics or {}
        kpis = structured_report.kpis or {}
        recommendations = structured_report.recommendations or []

        desc_stats = analytics_data.get("descriptive_statistics", {})
        correlations = analytics_data.get("correlation_analysis", {})
        distributions = analytics_data.get("distribution_analysis", {})
        categorical = analytics_data.get("categorical_analysis", {})

        cleaned_completeness = (
            cleaning_execution.cleaned_completeness_pct
            if cleaning_execution.cleaned_completeness_pct is not None
            else (quality_comparison.cleaned.completeness_percentage if quality_comparison else 100.0)
        )

        analytical_ctx = AnalyticalDataContext(
            cleaned_version_id=cleaned_version.version_id,
            row_count=cleaned_version.row_count,
            column_count=cleaned_version.column_count,
            completeness_percentage=cleaned_completeness,
            kpis=kpis,
            descriptive_statistics=desc_stats,
            correlations=correlations,
            distributions=distributions,
            categorical_insights=categorical,
            recommendations=recommendations,
        )

        # 4. Lineage Context
        lineage_ctx = LineageContext(
            pipeline_run_id=pipeline_run_id,
            source_version_id=source_version.version_id,
            cleaned_version_id=cleaned_version.version_id,
            cleaning_execution_id=cleaning_execution.execution_id,
            user_id=user_id,
            report_id=report_id,
            context_schema_version="v1.0",
        )

        return AIDataContext(
            source=source_ctx,
            cleaning=cleaning_ctx,
            analytics=analytical_ctx,
            lineage=lineage_ctx,
        )

    @classmethod
    def build_from_database(
        cls,
        connection: DatabaseConnection,
        pipeline_run_id: int,
        user_id: int | None = None,
    ) -> AIDataContext | None:
        """
        Reconstruct an authoritative AIDataContext across asynchronous worker boundaries.
        Enforces user ownership isolation on all queries.
        """
        pipeline_repo = PipelineRunRepository(connection)
        run_record = pipeline_repo.get_by_id(pipeline_run_id, user_id=user_id)
        if run_record is None:
            logger.warning(
                "Cannot build AIDataContext: Pipeline run %d not found or user_id=%s access denied.",
                pipeline_run_id,
                user_id,
            )
            return None

        # Verify strict tenant isolation: when user_id is requested, ownership must explicitly match
        if user_id is not None:
            record_user = run_record.get("user_id")
            if record_user is None or record_user != user_id:
                logger.warning(
                    "Security violation: user %s attempted to access pipeline run %d belonging to user %s.",
                    user_id,
                    pipeline_run_id,
                    record_user,
                )
                return None

        # Query Cleaning Execution
        exec_repo = CleaningExecutionRepository(connection)
        cleaning_exec_row = exec_repo.get_by_pipeline_run(pipeline_run_id, user_id=user_id)
        if cleaning_exec_row is None:
            logger.warning(
                "CleaningExecution record not found for pipeline run %d.",
                pipeline_run_id,
            )
            return None

        # Query Dataset Versions
        version_repo = DatasetVersionRepository(connection)
        source_version = version_repo.get_by_version_id(cleaning_exec_row["source_version_id"], user_id=user_id)
        if source_version is None:
            logger.warning(
                "Source DatasetVersion %s not found for pipeline run %d.",
                cleaning_exec_row["source_version_id"],
                pipeline_run_id,
            )
            return None

        cleaned_version = None
        if cleaning_exec_row.get("cleaned_version_id"):
            cleaned_version = version_repo.get_by_version_id(cleaning_exec_row["cleaned_version_id"], user_id=user_id)

        # Query Cleaning Config for authoritative policy
        from src.database.repositories.cleaning_config_repository import CleaningConfigRepository

        cfg_repo = CleaningConfigRepository(connection)
        cfg_row = cfg_repo.get_by_config_id(cleaning_exec_row["config_id"], user_id=user_id)
        authoritative_policy = cfg_row.get("missing_value_policy") if cfg_row else None

        # Query Report for analytical findings
        report_repo = ReportRepository(connection)
        report_record = report_repo.get_by_pipeline_run(pipeline_run_id, user_id=user_id)

        kpis: dict[str, Any] = {}
        analytics_data: dict[str, Any] = {}
        recommendations: list[str] = []
        report_id: int | None = None

        if report_record is not None:
            report_id = report_record.get("id")
            structured_content = report_record.get("content") or {}
            if isinstance(structured_content, str):
                try:
                    structured_content = json.loads(structured_content)
                except Exception:
                    structured_content = {}
            kpis = structured_content.get("kpis", {})
            analytics_data = structured_content.get("analytics", {})
            recommendations = structured_content.get("recommendations", [])

        # 1. Reconstruct Source Context
        source_missing_count = cleaning_exec_row.get("source_missing_count")
        source_completeness_pct = cleaning_exec_row.get("source_completeness_pct")
        source_missing_pct = round(100.0 - source_completeness_pct, 4) if source_completeness_pct is not None else None

        source_ctx = SourceDataContext(
            version_id=source_version["version_id"],
            source_filename=source_version["source_filename"],
            row_count=source_version["row_count"],
            column_count=source_version["column_count"],
            total_missing=source_missing_count,
            missing_percentage=source_missing_pct,
            completeness_percentage=source_completeness_pct,
            per_column_missing={},
            outliers_detected=None,
        )

        # 2. Reconstruct Cleaning Context
        rows_removed = (
            cleaning_exec_row["rows_removed"]
            if cleaning_exec_row.get("rows_removed") is not None
            else (max(0, source_version["row_count"] - cleaned_version["row_count"]) if cleaned_version else None)
        )
        pct_rows_removed = (
            cleaning_exec_row["pct_rows_removed"]
            if cleaning_exec_row.get("pct_rows_removed") is not None
            else (
                round((rows_removed / source_version["row_count"]) * 100, 4)
                if rows_removed is not None and source_version["row_count"] > 0
                else None
            )
        )

        cols_removed = cleaning_exec_row.get("columns_removed")
        if isinstance(cols_removed, str):
            try:
                cols_removed = json.loads(cols_removed)
            except Exception:
                cols_removed = []

        affected_detail = cleaning_exec_row.get("affected_columns_detail")
        if isinstance(affected_detail, str):
            try:
                affected_detail = json.loads(affected_detail)
            except Exception:
                affected_detail = {}

        cleaning_ctx = CleaningContext(
            config_id=cleaning_exec_row["config_id"],
            missing_value_policy=authoritative_policy,
            rows_removed=rows_removed,
            pct_rows_removed=pct_rows_removed,
            columns_removed=cols_removed or [],
            values_imputed=None,
            affected_columns=(list(affected_detail.keys()) if isinstance(affected_detail, dict) else []),
        )

        # 3. Reconstruct Analytical Context
        cleaned_rows = (
            cleaned_version["row_count"]
            if cleaned_version
            else (
                cleaning_exec_row["cleaned_row_count"]
                if cleaning_exec_row.get("cleaned_row_count") is not None
                else (
                    source_version["row_count"] - rows_removed
                    if rows_removed is not None
                    else source_version["row_count"]
                )
            )
        )
        cleaned_cols = cleaned_version["column_count"] if cleaned_version else source_version["column_count"]

        analytical_ctx = AnalyticalDataContext(
            cleaned_version_id=cleaned_version["version_id"] if cleaned_version else None,
            row_count=cleaned_rows,
            column_count=cleaned_cols,
            completeness_percentage=cleaning_exec_row.get("cleaned_completeness_pct") or 100.0,
            kpis=kpis,
            descriptive_statistics=analytics_data.get("descriptive_statistics", {}),
            correlations=analytics_data.get("correlation_analysis", {}),
            distributions=analytics_data.get("distribution_analysis", {}),
            categorical_insights=analytics_data.get("categorical_analysis", {}),
            recommendations=recommendations,
        )

        # 4. Lineage Context
        lineage_ctx = LineageContext(
            pipeline_run_id=pipeline_run_id,
            source_version_id=source_version["version_id"],
            cleaned_version_id=cleaned_version["version_id"] if cleaned_version else None,
            cleaning_execution_id=cleaning_exec_row["execution_id"],
            user_id=user_id,
            report_id=report_id,
            context_schema_version="v1.0",
        )

        return AIDataContext(
            source=source_ctx,
            cleaning=cleaning_ctx,
            analytics=analytical_ctx,
            lineage=lineage_ctx,
        )
