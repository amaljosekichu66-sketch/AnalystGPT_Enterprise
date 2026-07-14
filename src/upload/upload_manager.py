from pathlib import Path

import pandas as pd

from core.config import MAX_UPLOAD_SIZE_MB
from core.exceptions import (
    FileTooLargeError,
    SourceFileNotFoundError,
    UnsupportedFileTypeError,
)
from upload.csv_reader import CSVReader
from upload.excel_reader import ExcelReader
from upload.json_reader import JSONReader


class UploadManager:
    """Handles file uploads and delegates reading to the appropriate reader."""

    def __init__(self) -> None:
        """Initialize the reader registry."""
        self._readers = {
            ".csv": CSVReader(),
            ".xlsx": ExcelReader(),
            ".json": JSONReader(),
        }

    def upload(self, file_path: str | Path) -> pd.DataFrame:
        """Upload and read a supported file into a Pandas DataFrame."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise SourceFileNotFoundError(
                f"File not found: {file_path}"
            )

        max_size_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if file_path.stat().st_size > max_size_bytes:
            raise FileTooLargeError(
                f"File exceeds the maximum allowed size "
                f"({MAX_UPLOAD_SIZE_MB} MB): {file_path}"
            )

        extension = file_path.suffix.lower()

        reader = self._readers.get(extension)

        if reader is None:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {extension}"
            )

        return reader.read(file_path)