from typing import Any

import pandas as pd
from pandas import DataFrame

from src.core.logger import logger
from src.profiling.models import AnalyticalRole, DatasetProfile, SemanticType


class DistributionAnalysis:
    """
    Analyzes the statistical distribution of numerical columns with semantic profiling awareness.
    """

    def analyze(
        self,
        dataframe: DataFrame,
        profile: DatasetProfile | None = None,
    ) -> dict[str, Any]:
        """
        Analyze distribution characteristics of numerical columns.

        Returns:
            Dictionary containing distribution statistics.
        """

        logger.info("Analyzing data distributions.")

        if profile is not None:
            eligible_columns = [
                col
                for col, cp in profile.column_profiles.items()
                if (
                    cp.semantic_type in {SemanticType.NUMERIC_MEASURE, SemanticType.NUMERIC_DISCRETE}
                    or cp.analytical_role in {AnalyticalRole.MEASURE, AnalyticalRole.DEMOGRAPHIC_MEASURE}
                )
                and cp.semantic_type not in {SemanticType.POSTAL_CODE, SemanticType.PHONE, SemanticType.IDENTIFIER}
                and col in dataframe.columns
                and pd.api.types.is_numeric_dtype(dataframe[col])
            ]
            numerical_dataframe = dataframe[eligible_columns]
        else:
            numerical_dataframe = dataframe.select_dtypes(include=["number"])

        results = {}

        if numerical_dataframe.empty:

            logger.info("No numerical columns found.")

            return results

        for column in numerical_dataframe.columns:

            series = numerical_dataframe[column].dropna()

            if series.empty:
                continue

            skewness = float(series.skew())
            kurtosis = float(series.kurt())

            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1

            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            outlier_count = int(
                (
                    (series < lower_bound)
                    | (series > upper_bound)
                ).sum()
            )

            outlier_percentage = (
                (outlier_count / len(series)) * 100
                if len(series) > 0
                else 0
            )

            if abs(skewness) < 0.5:
                distribution_shape = "Approximately Symmetric"
            elif abs(skewness) < 1:
                distribution_shape = "Moderately Skewed"
            else:
                distribution_shape = "Highly Skewed"

            if kurtosis < -1:
                tail_type = "Light-tailed"
            elif kurtosis <= 1:
                tail_type = "Mesokurtic"
            else:
                tail_type = "Heavy-tailed"

            results[column] = {
                "skewness": round(skewness, 4),
                "kurtosis": round(kurtosis, 4),
                "distribution_shape": distribution_shape,
                "tail_type": tail_type,
                "lower_outlier_bound": round(lower_bound, 4),
                "upper_outlier_bound": round(upper_bound, 4),
                "outlier_count": outlier_count,
                "outlier_percentage": round(
                    outlier_percentage,
                    2,
                ),
            }

        logger.info("Distribution analysis completed.")

        return results