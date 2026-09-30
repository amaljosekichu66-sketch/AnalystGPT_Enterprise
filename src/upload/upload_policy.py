"""
Server-side acceptance policy for client-uploaded datasets.

Clients never name a server file. They upload bytes, the server stores them
under the managed artifact store, and every later request refers to the
dataset by the server-issued `dataset_version_id`. This module holds the
checks that run BEFORE anything is persisted or parsed:

- the client-supplied filename is reduced to a bare, safe display name;
- the extension must be one the ingestion layer can actually parse;
- the payload must not exceed the configured size limit.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import PurePosixPath, PureWindowsPath
from typing import BinaryIO

from src.core import config

#: Extensions `UploadManager` can parse. Anything else is refused up front.
#: No `.xls` (M4): xlrd is not installed, so pandas parsed a renamed .xlsx
#: with openpyxl while the zip-bomb check only ran for the `.xlsx` suffix.
ALLOWED_UPLOAD_EXTENSIONS: frozenset[str] = frozenset({".csv", ".xlsx", ".json"})

#: Local file header of a zip archive (every .xlsx starts with it).
ZIP_SIGNATURE = b"PK\x03\x04"

_MAX_FILENAME_LENGTH = 255
_UNSAFE_FILENAME_CHARS = re.compile(r"[\x00-\x1f<>:\"|?*]")


class UploadRejectedError(ValueError):
    """Base class for an upload refused by policy. `status_code` maps to HTTP."""

    status_code = 400


class UnsupportedUploadTypeError(UploadRejectedError):
    status_code = 415


class UploadTooLargeError(UploadRejectedError):
    status_code = 413


class UnparseableUploadError(UploadRejectedError):
    status_code = 422


class UploadLengthRequiredError(UploadRejectedError):
    status_code = 411


def max_upload_bytes() -> int:
    """Configured upload ceiling in bytes (read at call time so it is overridable)."""
    return int(config.MAX_FILE_SIZE_MB) * 1024 * 1024


def safe_upload_filename(filename: str | None) -> str:
    """
    Reduce a client-supplied filename to a bare display name.

    Both separator conventions are stripped regardless of the server OS, so
    `..\\..\\x.csv`, `/etc/x.csv` and `\\\\host\\share\\x.csv` all become `x.csv`.
    The result is used only as a label; storage location is decided by the
    artifact store.
    """
    raw = (filename or "").strip()
    name = PurePosixPath(PureWindowsPath(raw).name).name
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip(" .")

    if not name or name in {".", ".."}:
        raise UploadRejectedError("Uploaded file must have a filename.")

    if len(name) > _MAX_FILENAME_LENGTH:
        raise UploadRejectedError("Uploaded filename is too long.")

    return name


def validate_upload_filename(filename: str | None) -> str:
    """Return the safe filename, or raise if its type is not accepted."""
    name = safe_upload_filename(filename)
    extension = PurePosixPath(name).suffix.lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise UnsupportedUploadTypeError(f"Unsupported file type '{extension or '(none)'}'. Allowed: {allowed}.")

    return name


def require_declared_length(content_length: str | None) -> None:
    """
    Refuse an upload without a numeric `Content-Length` (M3).

    Chunked uploads skipped the size pre-check entirely. The body-limit
    middleware still counts the bytes of every request.
    """
    if content_length is None or not content_length.strip().isdigit():
        raise UploadLengthRequiredError("Uploads must declare their size with a Content-Length header.")


def check_declared_size(size_bytes: int | None) -> None:
    """Reject a payload whose declared size already exceeds the limit."""
    if size_bytes is not None and size_bytes > max_upload_bytes():
        raise UploadTooLargeError(f"Upload exceeds the maximum size of {config.MAX_FILE_SIZE_MB} MB.")


def read_bounded(stream: BinaryIO) -> bytes:
    """
    Read an upload stream, refusing it if it exceeds the limit.

    The declared size is not trusted on its own: this counts the bytes that
    actually arrive. One bounded read into one buffer - collecting chunks and
    joining them held every upload in memory twice (M3).
    """
    limit = max_upload_bytes()
    content = stream.read(limit + 1)

    if len(content) > limit:
        raise UploadTooLargeError(f"Upload exceeds the maximum size of {config.MAX_FILE_SIZE_MB} MB.")

    if not content:
        raise UploadRejectedError("Uploaded file is empty.")

    return content


def check_archive_safety(content: bytes, filename: str) -> None:
    """
    Refuse zip-bomb workbooks by inspecting the archive directory only.

    Nothing is decompressed: the central directory already records every
    entry's compressed and uncompressed size. Runs on the content, not the
    name (M4): any zip archive is checked, whatever it is called.
    """
    if PurePosixPath(filename).suffix.lower() != ".xlsx" and not content.startswith(ZIP_SIGNATURE):
        return

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
    except zipfile.BadZipFile as exc:
        raise UnparseableUploadError("Uploaded .xlsx file is not a valid workbook.") from exc

    if len(entries) > config.MAX_XLSX_ENTRIES:
        raise UploadTooLargeError("Workbook contains too many archive entries.")

    uncompressed = sum(entry.file_size for entry in entries)
    compressed = max(1, sum(entry.compress_size for entry in entries))
    if uncompressed > config.MAX_XLSX_UNCOMPRESSED_MB * 1024 * 1024:
        raise UploadTooLargeError(f"Workbook expands beyond {config.MAX_XLSX_UNCOMPRESSED_MB} MB.")

    worst_entry_ratio = max((e.file_size / max(1, e.compress_size) for e in entries), default=0)
    if uncompressed / compressed > config.MAX_XLSX_COMPRESSION_RATIO or (
        worst_entry_ratio > config.MAX_XLSX_COMPRESSION_RATIO
    ):
        raise UploadTooLargeError("Workbook compression ratio is too high to be processed safely.")


def check_dataset_shape(rows: int, columns: int) -> None:
    """Refuse parsed datasets beyond the configured row / column limits."""
    if rows > config.MAX_UPLOAD_ROWS:
        raise UploadTooLargeError(f"Dataset has {rows:,} rows; the limit is {config.MAX_UPLOAD_ROWS:,}.")
    if columns > config.MAX_UPLOAD_COLUMNS:
        raise UploadTooLargeError(f"Dataset has {columns:,} columns; the limit is {config.MAX_UPLOAD_COLUMNS:,}.")
