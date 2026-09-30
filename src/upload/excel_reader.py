"""
Excel Reader Module
"""

from pathlib import Path

import pandas as pd

from src.core.exceptions import FileReadError
from src.core.logger import logger
from src.upload.bounded_parse import read_excel_bounded
from src.upload.upload_policy import UploadRejectedError


class ExcelReader:
    """Reads Excel files and returns a Pandas DataFrame."""

    def read(self, file_path: str | Path) -> pd.DataFrame:
        """
        Read an Excel file and return its contents as a Pandas DataFrame.
        """
        try:
            logger.info(f"Reading Excel file: {file_path}")
            return read_excel_bounded(file_path)

        except UploadRejectedError:
            # Shape and size limits (M5) keep their own status codes.
            raise

        except Exception as error:
            logger.error(f"Failed to read Excel file: {error}")
            raise FileReadError(f"Unable to read Excel file: {file_path}") from error
