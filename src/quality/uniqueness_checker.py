"""
Uniqueness Checker Module

Evaluates dataset uniqueness.
"""

from pandas import DataFrame

from src.core.logger import logger


class UniquenessChecker:
    """
    Evaluates dataset uniqueness.
    """

    def check(self, dataframe: DataFrame) -> dict:
        """
        Assess duplicate records.
        """

        logger.info("Assessing data uniqueness.")

        duplicate_rows = int(dataframe.duplicated().sum())

        duplicate_percentage = (
            (duplicate_rows / len(dataframe) * 100)
            if len(dataframe) > 0
            else 0
        )

        logger.info("Uniqueness assessment completed.")

        return {
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": round(
                duplicate_percentage,
                2,
            ),
        }