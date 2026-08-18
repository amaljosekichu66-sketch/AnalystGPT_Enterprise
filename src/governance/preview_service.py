"""
Non-Destructive Cleaning Preview Service.

Sprint 14 Phase 3 — Data Cleaning Governance & Lineage.

Runs cleaning policies in-memory on isolated DataFrame copies.
Guarantees NO mutation of stored artifacts, NO pipeline run records created,
and NO persistent database changes.
"""

from __future__ import annotations

from typing import Any

from pandas import DataFrame

from src.cleaning.cleaning_manager import CleaningManager
from src.governance.models import (
    CleaningConfig,
    QualityComparison,
    QualitySnapshot,
)
from src.governance.policies import MissingValuePolicyExecutor
from src.quality.quality_manager import QualityManager


class CleaningPreviewResult:
    """
    Preview evaluation summary.
    """

    def __init__(
        self,
        quality_comparison: QualityComparison,
        columns_removed: list[str],
        affected_columns_detail: dict[str, str],
        preview_sample_source: list[dict[str, Any]],
        preview_sample_cleaned: list[dict[str, Any]],
    ) -> None:
        self.quality_comparison = quality_comparison
        self.columns_removed = columns_removed
        self.affected_columns_detail = affected_columns_detail
        self.preview_sample_source = preview_sample_source
        self.preview_sample_cleaned = preview_sample_cleaned

    def to_dict(self) -> dict[str, Any]:
        return {
            "quality_comparison": self.quality_comparison.to_dict(),
            "columns_removed": self.columns_removed,
            "affected_columns_detail": self.affected_columns_detail,
            "preview_sample_source": self.preview_sample_source,
            "preview_sample_cleaned": self.preview_sample_cleaned,
        }


class CleaningPreviewService:
    """
    Non-destructive preview service.
    """

    def __init__(
        self,
        quality_manager: QualityManager | None = None,
        cleaning_manager: CleaningManager | None = None,
        policy_executor: MissingValuePolicyExecutor | None = None,
    ) -> None:
        self.quality_manager = quality_manager or QualityManager()
        self.cleaning_manager = cleaning_manager or CleaningManager()
        self.policy_executor = policy_executor or MissingValuePolicyExecutor()

    def preview(
        self,
        raw_dataframe: DataFrame,
        config: CleaningConfig,
        sample_rows: int = 10,
    ) -> CleaningPreviewResult:
        """
        Execute an isolated, non-destructive preview.
        """
        df_copy = raw_dataframe.copy()

        # 1. Pre-cleaning snapshot
        src_report = self.quality_manager.assess(df_copy)
        src_snapshot = QualitySnapshot.from_quality_report(
            src_report, row_count=len(df_copy), column_count=len(df_copy.columns)
        )

        # 2. In-memory policy execution
        policy_res = self.policy_executor.execute(df_copy, config)
        policy_df = policy_res.cleaned_df

        # 3. Deterministic cleaners pass
        cleaned_df = self.cleaning_manager.clean(policy_df)

        # 4. Post-cleaning snapshot
        cleaned_report = self.quality_manager.assess(cleaned_df)
        cleaned_snapshot = QualitySnapshot.from_quality_report(
            cleaned_report, row_count=len(cleaned_df), column_count=len(cleaned_df.columns)
        )

        comparison = QualityComparison(source=src_snapshot, cleaned=cleaned_snapshot)

        return CleaningPreviewResult(
            quality_comparison=comparison,
            columns_removed=policy_res.columns_removed,
            affected_columns_detail=policy_res.affected_columns_detail,
            preview_sample_source=raw_dataframe.head(sample_rows).to_dict(orient="records"),
            preview_sample_cleaned=cleaned_df.head(sample_rows).to_dict(orient="records"),
        )
