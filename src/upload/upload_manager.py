"""
Upload Manager Module

Coordinates file upload operations by delegating file reading
to the appropriate reader based on file extension.
"""

from pathlib import Path

import pandas as pd

from src.core.exceptions import (
    SourceFileNotFoundError,
    UnsupportedFileTypeError,
)
from src.core.logger import logger
from src.upload.csv_reader import CSVReader
from src.upload.excel_reader import ExcelReader
from src.upload.json_reader import JSONReader


class UploadManager:
    """
    Coordinates file upload operations.
    """

    def __init__(self):
        """Initialize supported file readers."""

        self.csv_reader = CSVReader()
        self.excel_reader = ExcelReader()
        self.json_reader = JSONReader()

    def upload(self, file_path: str | Path) -> pd.DataFrame:
        """
        Upload a file and return its contents as a Pandas DataFrame.
        """

        file_path = Path(file_path)

        logger.info(f"Uploading file: {file_path}")

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise SourceFileNotFoundError(
                f"File not found: {file_path}"
            )

        extension = file_path.suffix.lower()

        if extension == ".csv":
            return self.csv_reader.read(file_path)

        if extension in [".xlsx", ".xls"]:
            return self.excel_reader.read(file_path)

        if extension == ".json":
            return self.json_reader.read(file_path)

        logger.error(f"Unsupported file type: {extension}")

        raise UnsupportedFileTypeError(
            f"Unsupported file type: {extension}"
        )