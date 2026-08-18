from typing import Any

from pandas import DataFrame

from src.core.logger import logger
from src.profiling.models import AnalyticalRole, DatasetProfile, SemanticType


class CategoricalAnalysis:
    """
    Performs analysis on categorical columns with semantic profiling awareness.
    """

    def analyze(
        self,
        dataframe: DataFrame,
        profile: DatasetProfile | None = None,
    ) -> dict[str, Any]:
        """
        Analyze all valid categorical dimension columns.

        Returns:
            Dictionary containing statistics for each categorical column.
        """

        logger.info("Analyzing categorical columns.")

        if profile is not None:
            eligible_columns = [
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
            categorical_dataframe = dataframe[eligible_columns]
        else:
            raw_cat = dataframe.select_dtypes(
                include=["object", "string", "category", "bool"]
            )
            # Exclude unique identifier columns and constant columns
            valid_cols = [
                col
                for col in raw_cat.columns
                if (
                    len(dataframe) <= 5
                    or (
                        raw_cat[col].nunique(dropna=True) < len(dataframe)
                        and raw_cat[col].nunique(dropna=True) > 1
                    )
                )
            ]
            categorical_dataframe = dataframe[valid_cols] if valid_cols else DataFrame()

        results = {}

        if categorical_dataframe.empty:
            logger.info("No categorical columns found.")
            return results

        for column in categorical_dataframe.columns:

            series = categorical_dataframe[column]

            value_counts = series.value_counts(dropna=False)

            top_value = (
                value_counts.index[0]
                if not value_counts.empty
                else None
            )

            top_frequency = (
                int(value_counts.iloc[0])
                if not value_counts.empty
                else 0
            )

            results[column] = {
                "count": int(series.count()),
                "missing_values": int(series.isna().sum()),
                "unique_values": int(series.nunique(dropna=True)),
                "top_value": (
                    str(top_value)
                    if top_value is not None
                    else None
                ),
                "top_frequency": top_frequency,
                "value_distribution": {
                    str(key): int(value)
                    for key, value in value_counts.items()
                },
            }

        logger.info("Categorical analysis completed.")

        return results