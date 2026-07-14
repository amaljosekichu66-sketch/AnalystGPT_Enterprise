"""
JSON Reader Module
"""

from pathlib import Path

import pandas as pd

from src.core.exceptions import FileReadError
from src.core.logger import logger


class JSONReader:
    """Reads JSON files and returns a Pandas DataFrame."""

    def read(self, file_path: str | Path) -> pd.DataFrame:
        """
        Read a JSON file and return its contents as a Pandas DataFrame.
        """
        try:
            logger.info(f"Reading JSON file: {file_path}")
            return pd.read_json(file_path)

        except Exception as error:
            logger.error(f"Failed to read JSON file: {error}")
            raise FileReadError(
                f"Unable to read JSON file: {file_path}"
            ) from error