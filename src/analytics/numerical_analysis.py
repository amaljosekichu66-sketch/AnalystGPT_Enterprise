"""
Numerical Analysis Module

Performs descriptive statistical analysis on numerical columns.
"""

from pandas import DataFrame

from src.core.logger import logger


class NumericalAnalysis:
    """
    Performs descriptive statistical analysis on numerical columns.
    """

    def analyze(self, dataframe: DataFrame) -> dict:
        """
        Analyze all numerical columns.

        Returns:
            Dictionary containing descriptive statistics for each
            numerical column.
        """

        logger.info("Analyzing numerical columns.")

        numerical_dataframe = dataframe.select_dtypes(include=["number"])

        results = {}

        if numerical_dataframe.empty:
            logger.info("No numerical columns found.")

            return results

        for column in numerical_dataframe.columns:

            series = numerical_dataframe[column]

            mode = series.mode()

            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))

            results[column] = {
                "count": int(series.count()),
                "mean": round(float(series.mean()), 4),
                "median": round(float(series.median()), 4),
                "mode": (
                    round(float(mode.iloc[0]), 4)
                    if not mode.empty
                    else None
                ),
                "minimum": round(float(series.min()), 4),
                "maximum": round(float(series.max()), 4),
                "range": round(
                    float(series.max() - series.min()),
                    4,
                ),
                "variance": round(float(series.var()), 4),
                "standard_deviation": round(
                    float(series.std()),
                    4,
                ),
                "first_quartile": round(q1, 4),
                "third_quartile": round(q3, 4),
                "interquartile_range": round(q3 - q1, 4),
            }

        logger.info("Numerical analysis completed.")

        return results