"""
Categorical Analysis Module

Performs analysis on categorical columns.
"""

from pandas import DataFrame

from src.core.logger import logger


class CategoricalAnalysis:
    """
    Performs analysis on categorical columns.
    """

    def analyze(self, dataframe: DataFrame) -> dict:
        """
        Analyze all categorical columns.

        Returns:
            Dictionary containing statistics for each categorical column.
        """

        logger.info("Analyzing categorical columns.")

        categorical_dataframe = dataframe.select_dtypes(
            include=["object", "string", "category", "bool"]
        )

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