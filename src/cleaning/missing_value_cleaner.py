"""
Missing Value Cleaner Module

Handles missing values using configurable cleaning strategies.
"""

from typing import Any

from pandas import DataFrame

from src.core.logger import logger


class MissingValueCleaner:
    """
    Handles missing values using configurable cleaning strategies.
    """

    def __init__(
        self,
        strategy: str = "drop",
        subset: list[str] | None = None,
        fill_value: Any = None,
    ) -> None:
        """
        Initialize the missing value cleaner.

        Args:
            strategy: Cleaning strategy ("drop", "fill", or "mean").
            subset: Columns to consider when dropping missing values.
            fill_value: Value used when applying the "fill" strategy.
        """

        self.strategy = strategy
        self.subset = subset
        self.fill_value = fill_value

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Clean missing values according to the selected strategy.

        Args:
            dataframe: Input DataFrame.

        Returns:
            Cleaned DataFrame.
        """

        rows_before = len(dataframe)

        if self.strategy == "drop":
            dataframe = dataframe.dropna(
                subset=self.subset,
            )

        elif self.strategy == "fill":
            dataframe = dataframe.fillna(
                self.fill_value,
            )

        elif self.strategy == "mean":
            dataframe = dataframe.fillna(
                dataframe.mean(
                    numeric_only=True,
                )
            )

        else:
            raise ValueError(
                f"Unknown missing value strategy: {self.strategy}"
            )

        rows_after = len(dataframe)

        logger.info(
            f"MissingValueCleaner removed "
            f"{rows_before - rows_after} rows "
            f"({rows_before} -> {rows_after})."
        )

        return dataframe