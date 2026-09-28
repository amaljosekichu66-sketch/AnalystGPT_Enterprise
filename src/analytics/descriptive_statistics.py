from typing import Any

from pandas import DataFrame

from src.core.logger import logger
from src.profiling.models import AnalyticalRole, DatasetProfile, SemanticType


class DescriptiveStatistics:
    """
    Generates high-level descriptive statistics for the dataset with semantic profiling awareness.
    """

    def analyze(
        self,
        dataframe: DataFrame,
        profile: DatasetProfile | None = None,
    ) -> dict[str, Any]:
        """
        Analyze overall dataset characteristics.

        Returns:
            Dictionary containing descriptive statistics.
        """

        logger.info("Analyzing dataset descriptive statistics.")

        total_rows = dataframe.shape[0]
        total_columns = dataframe.shape[1]

        if profile is not None:
            numeric_columns = [
                col
                for col, cp in profile.column_profiles.items()
                if (
                    cp.semantic_type in {SemanticType.NUMERIC_MEASURE, SemanticType.NUMERIC_DISCRETE}
                    or cp.analytical_role in {AnalyticalRole.MEASURE, AnalyticalRole.DEMOGRAPHIC_MEASURE}
                )
                and cp.semantic_type not in {SemanticType.POSTAL_CODE, SemanticType.PHONE, SemanticType.IDENTIFIER}
                and col in dataframe.columns
            ]
            categorical_columns = [
                col
                for col, cp in profile.column_profiles.items()
                if (
                    cp.analytical_role in {AnalyticalRole.CATEGORICAL_DIMENSION, AnalyticalRole.GEOGRAPHIC_DIMENSION}
                    or cp.semantic_type
                    in {
                        SemanticType.CATEGORICAL,
                        SemanticType.STATE_REGION,
                        SemanticType.CITY,
                        SemanticType.COUNTRY,
                        SemanticType.BOOLEAN,
                    }
                )
                and cp.analytical_role
                not in {
                    AnalyticalRole.IDENTIFIER,
                    AnalyticalRole.CONTACT_IDENTIFIER,
                    AnalyticalRole.CONSTANT_ATTRIBUTE,
                    AnalyticalRole.DESCRIPTIVE_ATTRIBUTE,
                }
                and cp.semantic_type
                not in {
                    SemanticType.PHONE,
                    SemanticType.EMAIL,
                    SemanticType.IDENTIFIER,
                    SemanticType.CONSTANT,
                    SemanticType.PERSON_NAME,
                    SemanticType.ADDRESS,
                    SemanticType.FREE_TEXT,
                }
                and col in dataframe.columns
            ]
            datetime_columns = [
                col
                for col, cp in profile.column_profiles.items()
                if (
                    cp.semantic_type in {SemanticType.DATETIME, SemanticType.DATE}
                    or cp.analytical_role == AnalyticalRole.TEMPORAL_DIMENSION
                )
                and col in dataframe.columns
            ]
        else:
            numeric_columns = dataframe.select_dtypes(include=["number"]).columns.tolist()

            categorical_columns = dataframe.select_dtypes(
                include=["object", "string", "category", "bool"]
            ).columns.tolist()

            datetime_columns = dataframe.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

        memory_usage_mb = round(
            dataframe.memory_usage(deep=True).sum() / (1024 * 1024),
            2,
        )

        logger.info("Descriptive statistics analysis completed.")

        return {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
            "numeric_column_count": len(numeric_columns),
            "categorical_column_count": len(categorical_columns),
            "datetime_column_count": len(datetime_columns),
            "memory_usage_mb": memory_usage_mb,
        }
