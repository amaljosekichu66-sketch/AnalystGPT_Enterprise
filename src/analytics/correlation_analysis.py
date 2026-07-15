"""
Correlation Analysis Module

Computes relationships between numerical variables.
"""

from pandas import DataFrame

from src.core.logger import logger


class CorrelationAnalysis:
    """
    Computes relationships between numerical variables.
    """

    def analyze(self, dataframe: DataFrame) -> dict:
        """
        Analyze correlations among numerical columns.

        Returns:
            Dictionary containing correlation matrix and strongest
            positive and negative relationships.
        """

        logger.info("Analyzing correlations.")

        numerical_dataframe = dataframe.select_dtypes(include=["number"])

        if numerical_dataframe.shape[1] < 2:

            logger.info(
                "Correlation analysis skipped. Less than two numerical columns."
            )

            return {
                "correlation_matrix": {},
                "strongest_positive": None,
                "strongest_negative": None,
            }

        correlation_matrix = numerical_dataframe.corr(
            method="pearson"
        )

        strongest_positive = None
        strongest_negative = None

        max_positive = float("-inf")
        max_negative = float("inf")

        columns = correlation_matrix.columns.tolist()

        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):

                value = correlation_matrix.iloc[i, j]

                if value > max_positive:
                    max_positive = value
                    strongest_positive = {
                        "column_1": columns[i],
                        "column_2": columns[j],
                        "correlation": round(float(value), 4),
                    }

                if value < max_negative:
                    max_negative = value
                    strongest_negative = {
                        "column_1": columns[i],
                        "column_2": columns[j],
                        "correlation": round(float(value), 4),
                    }

        logger.info("Correlation analysis completed.")

        return {
            "correlation_matrix": correlation_matrix.round(4).to_dict(),
            "strongest_positive": strongest_positive,
            "strongest_negative": strongest_negative,
        }