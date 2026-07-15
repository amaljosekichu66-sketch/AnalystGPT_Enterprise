"""
Completeness Checker Module

Evaluates dataset completeness by measuring missing values.
"""

from pandas import DataFrame

from src.core.logger import logger


class CompletenessChecker:
    """
    Evaluates dataset completeness by measuring missing values.
    """

    def check(self, dataframe: DataFrame) -> dict:
        """
        Assess missing values across the dataset.

        Returns:
        - Total missing values
        - Missing percentage
        - Complete percentage
        - Missing values per column
        """

        logger.info("Assessing dataset completeness.")

        total_cells = dataframe.shape[0] * dataframe.shape[1]

        missing_per_column = dataframe.isnull().sum()

        total_missing = int(missing_per_column.sum())

        missing_percentage = (
            (total_missing / total_cells) * 100
            if total_cells > 0
            else 0
        )

        complete_percentage = 100 - missing_percentage

        logger.info("Completeness assessment completed.")

        return {
            "total_missing": total_missing,
            "missing_percentage": round(missing_percentage, 2),
            "complete_percentage": round(complete_percentage, 2),
            "missing_per_column": missing_per_column.to_dict(),
        }