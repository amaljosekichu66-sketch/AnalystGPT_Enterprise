"""
Excel Reader Module
"""

from pathlib import Path

import pandas as pd

from src.core.exceptions import FileReadError
from src.core.logger import logger


class ExcelReader:
    """Reads Excel files and returns a Pandas DataFrame."""

    def read(self, file_path: str | Path) -> pd.DataFrame:
        """
        Read an Excel file and return its contents as a Pandas DataFrame.
        """
        try:
            logger.info(f"Reading Excel file: {file_path}")
            return pd.read_excel(file_path)

        except Exception as error:
            logger.error(f"Failed to read Excel file: {error}")
            raise FileReadError(
                f"Unable to read Excel file: {file_path}"
            ) from error