"""
Cleaning Manager Module

Coordinates the execution of all data cleaning operations.
"""

import time

from pandas import DataFrame

from src.cleaning.column_cleaner import ColumnCleaner
from src.cleaning.datatype_cleaner import DataTypeCleaner
from src.cleaning.duplicate_cleaner import DuplicateCleaner
from src.cleaning.missing_value_cleaner import MissingValueCleaner
from src.cleaning.text_cleaner import TextCleaner

from src.core.config import (
    DEFAULT_DATATYPE_MAP,
    RESET_INDEX_AFTER_CLEANING,
)
from src.core.logger import logger


class CleaningManager:
    """
    Coordinates the execution of all data cleaning operations.
    """

    def __init__(self) -> None:
        """
        Initialize the cleaning pipeline.
        """

        self.column_cleaner = ColumnCleaner()
        self.text_cleaner = TextCleaner()
        self.missing_value_cleaner = MissingValueCleaner()
        self.duplicate_cleaner = DuplicateCleaner()
        self.datatype_cleaner = DataTypeCleaner(
            DEFAULT_DATATYPE_MAP
        )

    def clean(
        self,
        dataframe: DataFrame,
    ) -> DataFrame:
        """
        Execute the complete data cleaning pipeline.

        Args:
            dataframe: Input DataFrame.

        Returns:
            Cleaned DataFrame.
        """

        start_time = time.perf_counter()

        logger.info("Starting cleaning pipeline.")

        logger.info("Running ColumnCleaner...")
        dataframe = self.column_cleaner.clean(dataframe)

        logger.info("Running TextCleaner...")
        dataframe = self.text_cleaner.clean(dataframe)

        logger.info("Running MissingValueCleaner...")
        dataframe = self.missing_value_cleaner.clean(dataframe)

        logger.info("Running DuplicateCleaner...")
        dataframe = self.duplicate_cleaner.clean(dataframe)

        logger.info("Running DataTypeCleaner...")
        dataframe = self.datatype_cleaner.clean(dataframe)

        if RESET_INDEX_AFTER_CLEANING:
            logger.info("Resetting DataFrame index...")
            dataframe = dataframe.reset_index(
                drop=True,
            )

        elapsed_time = time.perf_counter() - start_time

        logger.info(
            f"Cleaning pipeline completed successfully in "
            f"{elapsed_time:.4f} seconds."
        )

        return dataframe