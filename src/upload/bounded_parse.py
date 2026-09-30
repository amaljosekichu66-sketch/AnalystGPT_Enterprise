"""
Parsing with the dataset shape limits applied DURING the parse (M5).

`check_dataset_shape` used to run only after the whole file had been parsed:
a 200,000-column CSV took 19 s before it was refused, and a 500 MB CSV or
JSON file was materialised in memory in full. These readers stop early:

- CSV: the header is read first and a too-wide file is refused before any
  row is parsed; then at most `MAX_UPLOAD_ROWS + 1` rows are read, which is
  enough for `check_dataset_shape` to refuse an over-long file.
- XLSX: pandas' openpyxl reader streams rows and honours `nrows`; the
  archive itself is bounded beforehand by `check_archive_safety`.
- JSON: has no streaming reader, so the file size is capped separately
  (`MAX_JSON_FILE_SIZE_MB`).

Used by the API's readers and by the Streamlit uploader alike.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import IO

import pandas as pd

from src.core import config
from src.upload.upload_policy import UploadTooLargeError

Source = str | Path | IO[bytes]


def _rewind(source: Source) -> None:
    if hasattr(source, "seek"):
        source.seek(0)


def _size_bytes(source: Source) -> int:
    if isinstance(source, (str, Path)):
        return os.path.getsize(source)
    if isinstance(source, io.BytesIO):
        return len(source.getbuffer())
    position = source.tell()
    source.seek(0, os.SEEK_END)
    size = source.tell()
    source.seek(position)
    return size


def _check_width(columns: int) -> None:
    if columns > config.MAX_UPLOAD_COLUMNS:
        raise UploadTooLargeError(f"Dataset has {columns:,} columns; the limit is {config.MAX_UPLOAD_COLUMNS:,}.")


def read_csv_bounded(source: Source) -> pd.DataFrame:
    header = pd.read_csv(source, nrows=0)
    _check_width(len(header.columns))
    _rewind(source)
    return pd.read_csv(source, nrows=int(config.MAX_UPLOAD_ROWS) + 1)


def read_excel_bounded(source: Source) -> pd.DataFrame:
    frame = pd.read_excel(source, engine="openpyxl", nrows=int(config.MAX_UPLOAD_ROWS) + 1)
    _check_width(len(frame.columns))
    return frame


def read_json_bounded(source: Source) -> pd.DataFrame:
    limit_mb = int(config.MAX_JSON_FILE_SIZE_MB)
    if _size_bytes(source) > limit_mb * 1024 * 1024:
        raise UploadTooLargeError(f"JSON datasets are limited to {limit_mb} MB; use CSV for larger files.")
    frame = pd.read_json(source)
    _check_width(len(frame.columns))
    return frame
