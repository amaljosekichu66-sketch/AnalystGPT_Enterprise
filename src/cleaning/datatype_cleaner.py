"""
Data Type Cleaner Module

Converts DataFrame columns to configured data types.
"""

from pandas import DataFrame

from src.core.logger import logger


class DataTypeCleaner:
    """
    Converts DataFrame columns to the required data types.
    """

    def __init__(self, datatype_map=None):
        """
        datatype_map example:

        {
            "age": "int",
            "salary": "float",
            "joining_date": "datetime",
            "name": "string"
        }
        """

        self.datatype_map = datatype_map or {}

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Convert columns to the specified data types.
        """

        logger.info("Converting column data types.")

        for column, datatype in self.datatype_map.items():

            if column not in dataframe.columns:
                continue

            try:

                if datatype == "datetime":
                    dataframe[column] = dataframe[column].astype(
                        "datetime64[ns]"
                    )
                else:
                    dataframe[column] = dataframe[column].astype(
                        datatype
                    )

            except Exception:

                logger.warning(
                    "Could not convert column '%s' to %s.",
                    column,
                    datatype,
                )

        logger.info("Data type conversion completed.")

        return dataframe