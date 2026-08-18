"""
Data Profiler Orchestrator for AnalystGPT Enterprise.

Extracts comprehensive structural, statistical, and semantic metadata
from DataFrames to power downstream analytics, visualization planning,
null governance, and reporting.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import pandas as pd

from src.core.logger import logger
from src.profiling.models import (
    AnalyticalRole,
    ColumnProfile,
    DatasetProfile,
    SemanticType,
)
from src.profiling.semantic_classifier import SemanticClassifier


class DataProfiler:
    """
    Authoritative dataset profiler executing semantic inference, cardinality analysis,
    and visualization suitability planning.
    """

    def __init__(self, classifier: SemanticClassifier | None = None) -> None:
        self._classifier = classifier or SemanticClassifier()

    def profile_dataset(self, dataframe: pd.DataFrame) -> DatasetProfile:
        """
        Profile a DataFrame and produce an immutable DatasetProfile.
        """
        row_count = len(dataframe)
        column_count = len(dataframe.columns)
        total_cells = row_count * column_count if column_count > 0 else 0

        logger.info("Profiling dataset (%d rows, %d columns)...", row_count, column_count)

        column_profiles: dict[str, ColumnProfile] = {}
        semantic_counts: dict[str, int] = {}
        role_counts: dict[str, int] = {}
        total_missing = 0

        for col in dataframe.columns:
            series = dataframe[col]
            missing_count = int(series.isna().sum())
            total_missing += missing_count
            non_null_count = row_count - missing_count
            missing_pct = round((missing_count / row_count) * 100, 2) if row_count > 0 else 0.0
            unique_count = int(series.dropna().nunique())
            uniqueness_pct = round((unique_count / non_null_count) * 100, 2) if non_null_count > 0 else 0.0

            sem_type, role, confidence, card_class, vis_suit, gov_rec = self._classifier.classify_column(
                column_name=str(col),
                series=series,
                total_rows=row_count,
            )

            # Determine whether this column is visualizable in dashboard charts
            is_visualizable = (
                vis_suit != "excluded"
                and role
                not in {
                    AnalyticalRole.IDENTIFIER,
                    AnalyticalRole.CONTACT_IDENTIFIER,
                    AnalyticalRole.CONSTANT_ATTRIBUTE,
                }
                and sem_type
                not in {
                    SemanticType.PHONE,
                    SemanticType.EMAIL,
                    SemanticType.IDENTIFIER,
                    SemanticType.CONSTANT,
                    SemanticType.FREE_TEXT,
                }
            )

            profile = ColumnProfile(
                column_name=str(col),
                physical_dtype=str(series.dtype),
                semantic_type=sem_type,
                analytical_role=role,
                missing_count=missing_count,
                missing_percentage=missing_pct,
                non_null_count=non_null_count,
                unique_count=unique_count,
                uniqueness_percentage=uniqueness_pct,
                cardinality_classification=card_class,
                inference_confidence=confidence,
                is_visualizable=is_visualizable,
                visualization_suitability=vis_suit,
                governance_recommendation=gov_rec,
            )

            column_profiles[str(col)] = profile
            semantic_counts[sem_type.value] = semantic_counts.get(sem_type.value, 0) + 1
            role_counts[role.value] = role_counts.get(role.value, 0) + 1

        overall_completeness = (
            round(((total_cells - total_missing) / total_cells) * 100, 2) if total_cells > 0 else 100.0
        )
        memory_bytes = int(dataframe.memory_usage(deep=True).sum()) if row_count > 0 else 0

        logger.info(
            "Dataset profiling completed. Completeness: %.2f%% | Semantic classes: %s",
            overall_completeness,
            semantic_counts,
        )

        return DatasetProfile(
            row_count=row_count,
            column_count=column_count,
            column_profiles=column_profiles,
            memory_bytes=memory_bytes,
            has_missing_values=total_missing > 0,
            total_missing_cells=total_missing,
            overall_completeness_pct=overall_completeness,
            semantic_counts=semantic_counts,
            role_counts=role_counts,
        )

    def create_analytical_view(
        self,
        dataframe: pd.DataFrame,
        profile: DatasetProfile,
    ) -> pd.DataFrame:
        """
        Produce an in-memory DataFrame view where string-encoded numeric columns
        are cast to numeric for numerical computation without mutating raw data
        or corrupting postal codes / phone numbers.
        """
        df_view = dataframe.copy()
        for col_name, cp in profile.column_profiles.items():
            if cp.semantic_type in {SemanticType.NUMERIC_MEASURE, SemanticType.NUMERIC_DISCRETE}:
                if not pd.api.types.is_numeric_dtype(df_view[col_name]):
                    cleaned_series = (
                        df_view[col_name]
                        .astype(str)
                        .str.replace(r"[\$,€,£,¥,₹]", "", regex=True)
                        .str.replace(",", "", regex=False)
                        .str.strip()
                    )
                    df_view[col_name] = pd.to_numeric(cleaned_series, errors="coerce")
            elif cp.semantic_type == SemanticType.POSTAL_CODE:
                # Ensure postal code strings preserve leading zeros and formatting
                df_view[col_name] = df_view[col_name].astype(str).str.strip()
        return df_view
