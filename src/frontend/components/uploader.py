"""
Dataset uploader component for AnalystGPT Enterprise.

Sprint 11
"""

from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.frontend.services.session_manager import (
    DATASET_PATH_KEY,
)

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


def save_uploaded_file(
    uploaded_file,
) -> str:
    """
    Save the uploaded dataset to a temporary file.

    A fresh temporary file is created for every upload.

    Returns
    -------
    str
        Absolute filesystem path of the temporary dataset.
    """

    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.NamedTemporaryFile(
        mode="wb",
        delete=False,
        suffix=suffix,
    ) as temp_file:

        temp_file.write(uploaded_file.getbuffer())

        temp_path = Path(
            temp_file.name,
        ).resolve()

    return str(
        temp_path,
    )


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

        dataset_path = save_uploaded_file(
            uploaded_file,
        )

        st.session_state[DATASET_PATH_KEY] = dataset_path

    except Exception as error:

        st.error(f"Unable to read dataset.\n\n{error}")

        return (
            None,
            None,
        )

    st.success("Dataset loaded successfully.")

    st.caption(f"Temporary Dataset: {dataset_path}")

    return (
        uploaded_file,
        dataframe,
    )
