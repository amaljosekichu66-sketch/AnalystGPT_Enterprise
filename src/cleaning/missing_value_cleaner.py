from pandas import DataFrame
class MissingValueCleaner:
    """
    Handles missing values.
    """

    def clean(self, dataframe):
        """
        Remove rows containing missing values.
        """

        dataframe = dataframe.dropna()

        return dataframe

from src.core.logger import logger


class MissingValueCleaner:
    """
    Handles missing values using configurable cleaning strategies.
    """

    def __init__(
        self,
        strategy: str = "drop",
        subset=None,
        fill_value=None,
    ):
        self.strategy = strategy
        self.subset = subset
        self.fill_value = fill_value

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Clean missing values according to the selected strategy.
        """

        rows_before = len(dataframe)

        if self.strategy == "drop":
            dataframe = dataframe.dropna(subset=self.subset)

        elif self.strategy == "fill":
            dataframe = dataframe.fillna(self.fill_value)

        elif self.strategy == "mean":
            dataframe = dataframe.fillna(
                dataframe.mean(numeric_only=True)
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