"""
Outlier Checker Module

Detects statistical outliers using the IQR method.
"""

from pandas import DataFrame

from src.core.logger import logger


class OutlierChecker:
    """
    Detects statistical outliers using the IQR method.
    """

    def check(self, dataframe: DataFrame) -> dict:
        """
        Assess numeric columns for outliers.
        """

        logger.info("Assessing dataset outliers.")

        results = {}

        numeric_columns = dataframe.select_dtypes(include="number").columns

        for column in numeric_columns:

            q1 = dataframe[column].quantile(0.25)
            q3 = dataframe[column].quantile(0.75)

            iqr = q3 - q1

            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            outliers = dataframe[
                (dataframe[column] < lower_bound)
                | (dataframe[column] > upper_bound)
            ]

            results[column] = {
                "outlier_count": len(outliers),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
            }

        logger.info("Outlier assessment completed.")

        return results