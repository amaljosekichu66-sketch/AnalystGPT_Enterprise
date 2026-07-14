"""
CSV Reader Module
"""

from pathlib import Path

import pandas as pd

from src.core.exceptions import FileReadError
from src.core.logger import logger


class CSVReader:
    """Reads CSV files and returns a Pandas DataFrame."""

    def read(self, file_path: str | Path) -> pd.DataFrame:
        """
        Read a CSV file and return its contents as a Pandas DataFrame.
        """
        try:
            logger.info(f"Reading CSV file: {file_path}")
            return pd.read_csv(file_path)

        except Exception as error:
            logger.error(f"Failed to read CSV file: {error}")
            raise FileReadError(
                f"Unable to read CSV file: {file_path}"
            ) from error