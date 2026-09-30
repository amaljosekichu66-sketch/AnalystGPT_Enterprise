"""
JSON Reader Module
"""

from pathlib import Path

import pandas as pd

from src.core.exceptions import FileReadError
from src.core.logger import logger
from src.upload.bounded_parse import read_json_bounded
from src.upload.upload_policy import UploadRejectedError


class JSONReader:
    """Reads JSON files and returns a Pandas DataFrame."""

    def read(self, file_path: str | Path) -> pd.DataFrame:
        """
        Read a JSON file and return its contents as a Pandas DataFrame.
        """
        try:
            logger.info(f"Reading JSON file: {file_path}")
            return read_json_bounded(file_path)

        except UploadRejectedError:
            # Shape and size limits (M5) keep their own status codes.
            raise

        except Exception as error:
            logger.error(f"Failed to read JSON file: {error}")
            raise FileReadError(f"Unable to read JSON file: {file_path}") from error
