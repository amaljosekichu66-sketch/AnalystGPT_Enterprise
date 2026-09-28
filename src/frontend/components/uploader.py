"""
Dataset uploader component for AnalystGPT Enterprise.

Sprint 11
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.frontend.services.session_manager import (
    DATASET_VERSION_ID_KEY,
)
from src.frontend.services.upload_service import UploadService

SUPPORTED_FILE_TYPES = [
    "csv",
    "xlsx",
    "json",
]

MAX_UPLOAD_SIZE_MB = 100


# ==========================================================
# Internal Helpers
# ==========================================================


@st.cache_data(show_spinner=False)
def load_dataframe(
    file_bytes: bytes,
    filename: str,
) -> pd.DataFrame:
    """
    Load an uploaded dataset into a DataFrame.

    Cached to avoid repeatedly parsing the same file during
    Streamlit reruns.
    """

    extension = Path(filename).suffix.lower()

    buffer = BytesIO(
        file_bytes,
    )

    if extension == ".csv":

        return pd.read_csv(
            buffer,
        )

    if extension == ".xlsx":

        return pd.read_excel(
            buffer,
        )

    if extension == ".json":

        return pd.read_json(
            buffer,
        )

    raise ValueError(f"Unsupported file format: {extension}")


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

        file_bytes = uploaded_file.getvalue()

        dataframe = load_dataframe(
            file_bytes=file_bytes,
            filename=uploaded_file.name,
        )

        dataset_version_id = upload_to_backend(
            uploaded_file,
        )

        st.session_state[DATASET_VERSION_ID_KEY] = dataset_version_id

    except Exception as error:

        st.error(f"Unable to read dataset.\n\n{error}")

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
