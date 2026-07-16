"""
Duplicate Cleaner Module

Removes duplicate rows from a DataFrame.
"""

from pandas import DataFrame

from src.core.logger import logger


class DuplicateCleaner:
    """
    Removes duplicate rows from a DataFrame.
    """

    def clean(
        self,
        dataframe: DataFrame,
    ) -> DataFrame:
        """
        Remove duplicate rows.

        Args:
            dataframe: Input DataFrame.

        Returns:
            DataFrame with duplicate rows removed.
        """

        logger.info("Removing duplicate rows.")

        rows_before = len(dataframe)

        dataframe = dataframe.drop_duplicates()

        rows_after = len(dataframe)

        logger.info(
            f"DuplicateCleaner removed "
            f"{rows_before - rows_after} duplicate rows "
            f"({rows_before} -> {rows_after})."
        )

        return dataframe