"""
Consistency Checker Module

Detects simple consistency issues in text columns.
"""

from pandas import DataFrame

from src.core.logger import logger


class ConsistencyChecker:
    """
    Detects simple consistency issues in text columns.
    """

    def check(self, dataframe: DataFrame) -> dict:
        """
        Assess leading and trailing whitespace in text columns.

        Returns:
        - Leading whitespace count per text column
        - Trailing whitespace count per text column
        """

        logger.info("Assessing data consistency.")

        results = {}

        text_columns = dataframe.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in text_columns:

            leading_spaces = (
                dataframe[column]
                .dropna()
                .astype(str)
                .str.startswith(" ")
                .sum()
            )

            trailing_spaces = (
                dataframe[column]
                .dropna()
                .astype(str)
                .str.endswith(" ")
                .sum()
            )

            results[column] = {
                "leading_spaces": int(leading_spaces),
                "trailing_spaces": int(trailing_spaces),
            }

        logger.info("Consistency assessment completed.")

        return results