"""
Duplicate Cleaner Module

Removes duplicate records from a DataFrame.
"""

from pandas import DataFrame

from src.core.logger import logger


class DuplicateCleaner:
    """
    Removes duplicate records from a DataFrame.
    """

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Remove duplicate rows while keeping the first occurrence.
        """

        rows_before = len(dataframe)

        dataframe = dataframe.drop_duplicates()

        rows_after = len(dataframe)

        logger.info(
            f"DuplicateCleaner removed "
            f"{rows_before - rows_after} duplicate rows "
            f"({rows_before} -> {rows_after})."
        )

        return dataframe