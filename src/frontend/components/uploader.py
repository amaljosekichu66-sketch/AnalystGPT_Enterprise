"""
Dataset uploader component for AnalystGPT Enterprise.

Sprint 11
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.core.config import MAX_FILE_SIZE_MB
from src.core.logger import logger
from src.frontend.services.session_manager import (
    DATASET_VERSION_ID_KEY,
)
from src.frontend.services.upload_service import UploadService
from src.upload.bounded_parse import read_csv_bounded, read_excel_bounded, read_json_bounded
from src.upload.upload_policy import UploadRejectedError, check_archive_safety, check_dataset_shape

SUPPORTED_FILE_TYPES = [
    "csv",
    "xlsx",
    "json",
]

MAX_UPLOAD_SIZE_MB = MAX_FILE_SIZE_MB


# ==========================================================
# Internal Helpers
# ==========================================================


def _upload_error_message(error: Exception) -> str:
    """A user-facing reason for a failed upload, without internal details."""
    text = str(error)
    for status_code, reason in (
        ("413", "The dataset is too large."),
        ("415", "This file type is not supported."),
        ("422", "The file could not be read as a dataset."),
        ("429", "You already have uploads or analyses in progress. Try again shortly."),
        ("403", "Your account cannot upload datasets. Ask an administrator for analyst access."),
    ):
        if f"HTTP {status_code}" in text:
            return reason
    if isinstance(error, RuntimeError) and not any(s in text.lower() for s in ("backend", "api client")):
        # The upload service's own validation message (type, size): safe to show.
        return text
    return "Unable to upload the dataset. Please try again."


# Bounded (M8): the cache is process-wide, and every entry is a full DataFrame.
@st.cache_data(show_spinner=False, max_entries=8, ttl=3600)
def load_dataframe(
    file_bytes: bytes,
    filename: str,
) -> pd.DataFrame:
    """
    Load an uploaded dataset into a DataFrame.

    Only called after the API has accepted the file, and with the same
    archive and shape limits the API applies (M8): the frontend used to parse
    first, with no guard at all. Cached to avoid re-parsing on reruns.
    """

    extension = Path(filename).suffix.lower()

    check_archive_safety(file_bytes, filename)

    buffer = BytesIO(
        file_bytes,
    )

    if extension == ".csv":
        frame = read_csv_bounded(buffer)
    elif extension == ".xlsx":
        frame = read_excel_bounded(buffer)
    elif extension == ".json":
        frame = read_json_bounded(buffer)
    else:
        raise ValueError(f"Unsupported file format: {extension}")

    check_dataset_shape(len(frame), len(frame.columns))
    return frame


def upload_to_backend(
    uploaded_file,
) -> str:
    """
    Upload the dataset bytes to the API and return the server-issued
    `dataset_version_id`.

    The frontend used to write a temp file and hand its path to the API,
    which only worked when both processes shared a filesystem and required
    the API to trust client-supplied paths. The API now accepts bytes only.
    """

    success, data, error = UploadService().upload_dataset(
        filename=uploaded_file.name,
        content=uploaded_file.getvalue(),
    )

    if not success or not data:
        raise RuntimeError(error or "Upload failed.")

    return data["dataset_version_id"]


# ==========================================================
# Public Component
# ==========================================================


def render_uploader():
    """
    Render the dataset uploader.

    Returns
    -------
    tuple
        (
            uploaded_file,
            dataframe,
        )
    """

    uploaded_file = st.file_uploader(
        label="Select a dataset",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=False,
    )

    if uploaded_file is None:

        st.info("Please select a CSV, Excel, or JSON dataset.")

        return (
            None,
            None,
        )

    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_size_mb > MAX_UPLOAD_SIZE_MB:

        st.error(f"Dataset exceeds the maximum supported size " f"({MAX_UPLOAD_SIZE_MB} MB).")

        return (
            None,
            None,
        )

    try:

        # The API validates first (size, type, archive, shape); only an
        # accepted file is parsed here (M8).
        dataset_version_id = upload_to_backend(
            uploaded_file,
        )

        st.session_state[DATASET_VERSION_ID_KEY] = dataset_version_id

        dataframe = load_dataframe(
            file_bytes=uploaded_file.getvalue(),
            filename=uploaded_file.name,
        )

    except UploadRejectedError as error:

        st.error(f"Unable to read dataset: {error}")

        return (
            None,
            None,
        )

    except Exception as error:

        # Details stay in the log (L7): they can quote server paths.
        logger.warning("Dataset upload failed: %s", error)
        st.error(_upload_error_message(error))

        return (
            None,
            None,
        )

    st.success("Dataset loaded successfully.")

    st.caption(f"Dataset ID: {dataset_version_id}")

    return (
        uploaded_file,
        dataframe,
    )
