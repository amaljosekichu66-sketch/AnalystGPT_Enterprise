"""
Text Cleaner Module

Standardizes text values across string columns.
"""

from pandas import DataFrame


class TextCleaner:
    """
    Cleans text values in string columns.
    """

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Standardize text values.
        """

        text_columns = dataframe.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in text_columns:
            dataframe[column] = (
                dataframe[column]
                .astype(str)
                .str.strip()
                .str.title()
            )

        return dataframe