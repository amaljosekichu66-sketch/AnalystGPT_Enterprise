"""
Column Cleaner Module

Standardizes DataFrame column names.
"""

from pandas import DataFrame

from src.core.logger import logger


class ColumnCleaner:
    """
    Standardizes DataFrame column names.
    """

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Standardize DataFrame column names.

        Operations:
        - Remove leading/trailing whitespace
        - Convert to lowercase
        - Replace spaces with underscores
        """

        logger.info("Standardizing column names.")

        dataframe.columns = (
            dataframe.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_", regex=False)
        )

        logger.info("Column name standardization completed.")

        return dataframe