"""
Text Cleaner Module

Standardizes text values across string columns.
"""

from pandas import DataFrame

from src.core.logger import logger


class TextCleaner:
    """
    Cleans text values in string columns.
    """

    EXCLUDED_KEYWORDS = {
        "email",
        "mail",
        "id",
        "code",
        "sku",
        "url",
        "uri",
        "website",
        "phone",
        "mobile",
        "number",
    }

    def clean(self, dataframe: DataFrame) -> DataFrame:
        """
        Standardize text values while preserving structured fields.

        Args:
            dataframe: Input DataFrame.

        Returns:
            Cleaned DataFrame.
        """

        logger.info("Cleaning text columns.")

        text_columns = dataframe.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in text_columns:

            column_name = column.lower()

            series = dataframe[column].astype(str).str.strip()

            if any(
                keyword in column_name
                for keyword in self.EXCLUDED_KEYWORDS
            ):
                dataframe[column] = series
            else:
                dataframe[column] = series.str.title()

        logger.info("Text cleaning completed.")

        return dataframe