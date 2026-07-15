"""
Descriptive Statistics Module

Generates high-level descriptive statistics for the dataset.
"""

from pandas import DataFrame

from src.core.logger import logger


class DescriptiveStatistics:
    """
    Generates high-level descriptive statistics for the dataset.
    """

    def analyze(self, dataframe: DataFrame) -> dict:
        """
        Analyze overall dataset characteristics.

        Returns:
            Dictionary containing descriptive statistics.
        """

        logger.info("Analyzing dataset descriptive statistics.")

        total_rows = dataframe.shape[0]
        total_columns = dataframe.shape[1]

        numeric_columns = dataframe.select_dtypes(
            include=["number"]
        ).columns.tolist()

        categorical_columns = dataframe.select_dtypes(
            include=["object", "string", "category", "bool"]
        ).columns.tolist()

        datetime_columns = dataframe.select_dtypes(
            include=["datetime", "datetimetz"]
        ).columns.tolist()

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