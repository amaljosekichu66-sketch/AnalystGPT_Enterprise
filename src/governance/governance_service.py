"""
Cleaning Governance Orchestration Service.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.
Sprint 14 Remediation — Semantically Aware Null Governance.

Coordinates governed cleaning execution:
- Immutable raw artifact preservation and source DatasetVersion registration
- Policy execution + deterministic cleaners
- Separate cleaned analytical Parquet persistence + cleaned DatasetVersion registration
- Provenance auditing, quality comparison, and semantic policy recommendations
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pandas import DataFrame

from src.cleaning.cleaning_manager import CleaningManager
from src.core.logger import logger
from src.governance.models import (
    CleaningConfig,
    CleaningExecution,
    DatasetVersion,
    ExecutionStatus,
    MissingValuePolicy,
    QualityComparison,
    QualitySnapshot,
)
from src.governance.policies import MissingValuePolicyExecutor
from src.profiling.models import (
    AnalyticalRole,
    ColumnProfile,
    DatasetProfile,
    SemanticType,
)
from src.quality.quality_manager import QualityManager
from src.storage.artifact_store import ArtifactStore, LocalArtifactStore


@dataclass
class GovernedExecutionResult:
    """Carries in-process output and all governance metadata."""

    cleaned_df: DataFrame
    source_version: DatasetVersion
    cleaned_version: DatasetVersion
    cleaning_config: CleaningConfig
    execution: CleaningExecution
    quality_comparison: QualityComparison


class CleaningGovernanceService:
    """
    Main orchestrator for dataset versioning, governed cleaning, and lineage.
    """

    def __init__(
        self,
        artifact_store: ArtifactStore | None = None,
        quality_manager: QualityManager | None = None,
        cleaning_manager: CleaningManager | None = None,
        policy_executor: MissingValuePolicyExecutor | None = None,
    ) -> None:
        self.artifact_store = artifact_store or LocalArtifactStore()
        self.quality_manager = quality_manager or QualityManager()
        self.cleaning_manager = cleaning_manager or CleaningManager()
        self.policy_executor = policy_executor or MissingValuePolicyExecutor()

    def register_source_dataset(
        self,
        file_path_or_bytes: Path | bytes,
        filename: str,
        user_id: int | None = None,
    ) -> tuple[DatasetVersion, DataFrame]:
        """
        Preserve uploaded source file in ArtifactStore and build DatasetVersion.
        Loads source DataFrame in memory for processing.
        """
        version_id = str(uuid.uuid4())
        storage_path, checksum, byte_size = self.artifact_store.save_raw_artifact(
            file_path_or_bytes, filename=filename, version_id=version_id
        )

        from src.upload.upload_manager import UploadManager

        raw_df = UploadManager().upload(storage_path)

        source_version = DatasetVersion(
            version_id=version_id,
            source_filename=filename,
            byte_size=byte_size,
            checksum_sha256=checksum,
            row_count=len(raw_df),
            column_count=len(raw_df.columns),
            storage_path=storage_path,
            is_source=True,
            content_type="text/csv" if filename.endswith(".csv") else "application/octet-stream",
            user_id=user_id,
        )

        logger.info(
            "Registered source DatasetVersion: version_id=%s rows=%d cols=%d",
            version_id,
            source_version.row_count,
            source_version.column_count,
        )
        return source_version, raw_df

    def execute_governed_cleaning(
        self,
        raw_df: DataFrame,
        source_version: DatasetVersion,
        config: CleaningConfig,
        pipeline_run_id: int | None = None,
        user_id: int | None = None,
    ) -> GovernedExecutionResult:
        """
        Execute governed cleaning, save cleaned analytical dataset to storage,
        and generate auditable provenance record.
        """
        execution_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # 1. Pre-cleaning snapshot
        src_report = self.quality_manager.assess(raw_df)
        src_snapshot = QualitySnapshot.from_quality_report(
            src_report, row_count=len(raw_df), column_count=len(raw_df.columns)
        )

        try:
            # 2. Execute missing value policy
            policy_res = self.policy_executor.execute(raw_df, config)
            policy_df = policy_res.cleaned_df

            # 3. Execute deterministic cleaning pipeline
            cleaned_df = self.cleaning_manager.clean(policy_df)

            # 4. Post-cleaning snapshot
            cleaned_report = self.quality_manager.assess(cleaned_df)
            cleaned_snapshot = QualitySnapshot.from_quality_report(
                cleaned_report, row_count=len(cleaned_df), column_count=len(cleaned_df.columns)
            )

            quality_cmp = QualityComparison(source=src_snapshot, cleaned=cleaned_snapshot)

            # 5. Persist separate cleaned analytical artifact
            cleaned_version_id = str(uuid.uuid4())
            stem = Path(source_version.source_filename).stem
            storage_path, checksum, byte_size = self.artifact_store.save_cleaned_dataframe(
                cleaned_df, version_id=cleaned_version_id, stem_name=stem
            )

            cleaned_version = DatasetVersion(
                version_id=cleaned_version_id,
                source_filename=source_version.source_filename,
                byte_size=byte_size,
                checksum_sha256=checksum,
                row_count=len(cleaned_df),
                column_count=len(cleaned_df.columns),
                storage_path=storage_path,
                is_source=False,
                content_type="application/parquet",
                parent_version_id=source_version.version_id,
                user_id=user_id,
            )

            elapsed = time.perf_counter() - start_time

            # 6. Provenance audit record
            execution = CleaningExecution(
                execution_id=execution_id,
                source_version_id=source_version.version_id,
                cleaned_version_id=cleaned_version.version_id,
                config_id=config.config_id,
                execution_status=ExecutionStatus.SUCCESS,
                source_row_count=src_snapshot.row_count,
                cleaned_row_count=cleaned_snapshot.row_count,
                rows_removed=quality_cmp.rows_removed,
                pct_rows_removed=quality_cmp.pct_rows_removed,
                source_missing_count=src_snapshot.total_missing,
                cleaned_missing_count=cleaned_snapshot.total_missing,
                source_completeness_pct=src_snapshot.completeness_percentage,
                cleaned_completeness_pct=cleaned_snapshot.completeness_percentage,
                columns_removed=policy_res.columns_removed if policy_res.columns_removed else None,
                affected_columns_detail=(
                    policy_res.affected_columns_detail if policy_res.affected_columns_detail else None
                ),
                pipeline_run_id=pipeline_run_id,
                user_id=user_id,
                execution_time_seconds=round(elapsed, 4),
            )

            return GovernedExecutionResult(
                cleaned_df=cleaned_df,
                source_version=source_version,
                cleaned_version=cleaned_version,
                cleaning_config=config,
                execution=execution,
                quality_comparison=quality_cmp,
            )

        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            logger.exception("Governed cleaning execution failed: %s", exc)
            failed_execution = CleaningExecution(
                execution_id=execution_id,
                source_version_id=source_version.version_id,
                cleaned_version_id=None,
                config_id=config.config_id,
                execution_status=ExecutionStatus.FAILED,
                source_row_count=src_snapshot.row_count,
                error_message=str(exc),
                pipeline_run_id=pipeline_run_id,
                user_id=user_id,
                execution_time_seconds=round(elapsed, 4),
            )
            raise GovernedCleaningError(f"Governed cleaning failed: {exc}", execution=failed_execution) from exc

    def create_default_config(
        self,
        user_id: int | None = None,
        policy: MissingValuePolicy = MissingValuePolicy.DROP_ROWS,
    ) -> CleaningConfig:
        return CleaningConfig(
            config_id=str(uuid.uuid4()),
            missing_value_policy=policy,
            user_id=user_id,
        )

    def recommend_policy_for_column(self, column_profile: ColumnProfile) -> MissingValuePolicy:
        """
        Recommend semantically appropriate missing value policy for an individual column.
        Never recommends numeric mean/median on phones, postal codes, or identifiers.
        """
        if column_profile.missing_count == 0:
            return MissingValuePolicy.PRESERVE_NULLS

        sem = column_profile.semantic_type

        if sem in {SemanticType.PHONE, SemanticType.EMAIL, SemanticType.POSTAL_CODE, SemanticType.IDENTIFIER}:
            return (
                MissingValuePolicy.PRESERVE_NULLS
                if column_profile.missing_percentage < 20.0
                else MissingValuePolicy.DROP_ROWS
            )

        if sem in {SemanticType.NUMERIC_MEASURE, SemanticType.NUMERIC_DISCRETE}:
            return MissingValuePolicy.FILL_NUMERIC_MEDIAN

        if sem in {SemanticType.CATEGORICAL, SemanticType.CITY, SemanticType.STATE_REGION, SemanticType.COUNTRY}:
            return MissingValuePolicy.FILL_CATEGORICAL_MODE

        return MissingValuePolicy.DROP_ROWS

    def recommend_dataset_policy(self, profile: DatasetProfile) -> tuple[MissingValuePolicy, str]:
        """
        Recommend a dataset-level missing value policy and return an explanation.
        """
        if not profile.has_missing_values:
            return MissingValuePolicy.PRESERVE_NULLS, "No missing values detected in dataset."

        missing_cols = profile.get_columns_with_missing()
        num_missing_cols = [
            c for c in missing_cols if c.semantic_type in {SemanticType.NUMERIC_MEASURE, SemanticType.NUMERIC_DISCRETE}
        ]
        cat_missing_cols = [
            c
            for c in missing_cols
            if c.semantic_type
            in {SemanticType.CATEGORICAL, SemanticType.CITY, SemanticType.STATE_REGION, SemanticType.COUNTRY}
        ]

        if num_missing_cols and not cat_missing_cols:
            return (
                MissingValuePolicy.FILL_NUMERIC_MEDIAN,
                "Missing values are concentrated in numeric measures. Recommend median imputation.",
            )

        if cat_missing_cols and not num_missing_cols:
            return (
                MissingValuePolicy.FILL_CATEGORICAL_MODE,
                "Missing values are concentrated in categorical fields. Recommend mode imputation.",
            )

        max_miss_pct = max(c.missing_percentage for c in missing_cols)
        if max_miss_pct > 50.0:
            return (
                MissingValuePolicy.DROP_ROWS,
                f"Severe missingness ({max_miss_pct:.1f}% in {missing_cols[0].column_name}). Recommend dropping incomplete rows.",
            )

        return (
            MissingValuePolicy.DROP_ROWS,
            "Mixed missing values detected across dimensions and measures. Recommend dropping rows or configuring custom policy.",
        )


class GovernedCleaningError(Exception):
    def __init__(self, message: str, execution: CleaningExecution) -> None:
        super().__init__(message)
        self.execution = execution
