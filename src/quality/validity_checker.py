"""
Validity Checker Module

Evaluates basic data validity.
"""

from pandas import DataFrame

from src.core.logger import logger


class ValidityChecker:
    """
    Evaluates basic data validity.
    """

    def check(self, dataframe: DataFrame) -> dict:
        """
        Assess column data types and null counts.
        """

        logger.info("Assessing data validity.")

        results = {}

        for column in dataframe.columns:

            results[column] = {
                "data_type": str(dataframe[column].dtype),
                "null_values": int(dataframe[column].isnull().sum()),
                "non_null_values": int(dataframe[column].count()),
            }

        logger.info("Validity assessment completed.")

        return results