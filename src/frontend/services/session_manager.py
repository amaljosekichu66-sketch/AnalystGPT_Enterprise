"""
Session management for AnalystGPT Enterprise.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.application.pipeline_result import PipelineResult

# ==========================================================
# Session Keys
# ==========================================================

DATAFRAME_KEY = "dataframe"

UPLOADED_FILE_KEY = "uploaded_file"

DATASET_PATH_KEY = "dataset_path"

PIPELINE_RESULT_KEY = "pipeline_result"


# ==========================================================
# Store
# ==========================================================

def store_dataset(
    uploaded_file,
    dataframe: pd.DataFrame,
    dataset_path: str | None = None,
) -> None:
    """
    Store the uploaded dataset in the Streamlit session.

    Parameters
    ----------
    uploaded_file
        Original Streamlit UploadedFile.

    dataframe
        Parsed dataframe.

    dataset_path
        Absolute path of the temporary dataset file created
        by the uploader.

    Notes
    -----
    The backend pipeline requires a real filesystem path.
    Therefore only the uploader should create and supply this
    value. This method never attempts to reconstruct it from
    the uploaded filename.
    """

    st.session_state[
        UPLOADED_FILE_KEY
    ] = uploaded_file

    st.session_state[
        DATAFRAME_KEY
    ] = dataframe

    st.session_state[
        DATASET_PATH_KEY
    ] = dataset_path


def store_pipeline_result(
    pipeline_result: PipelineResult,
) -> None:
    """
    Store the latest backend pipeline result.
    """

    st.session_state[
        PIPELINE_RESULT_KEY
    ] = pipeline_result


# ==========================================================
# Getters
# ==========================================================

def get_dataframe() -> pd.DataFrame | None:
    """
    Return the stored dataframe.
    """

    return st.session_state.get(
        DATAFRAME_KEY,
    )


def get_uploaded_file():
    """
    Return the uploaded file.
    """

    return st.session_state.get(
        UPLOADED_FILE_KEY,
    )


def get_dataset_path() -> str | None:
    """
    Return the temporary dataset path.

    Returns
    -------
    str | None
        Filesystem path used by the backend pipeline.
    """

    return st.session_state.get(
        DATASET_PATH_KEY,
    )


def get_dataset():
    """
    Return the uploaded file and dataframe.

    IMPORTANT
    ---------
    This function intentionally returns ONLY TWO values
    for backward compatibility with Sprint 10.

    Dataset path is available separately through
    get_dataset_path().
    """

    return (
        get_uploaded_file(),
        get_dataframe(),
    )


def get_pipeline_result() -> PipelineResult | None:
    """
    Return the cached backend pipeline result.
    """

    if not has_pipeline_result():
        return None

    return st.session_state[
        PIPELINE_RESULT_KEY
    ]


# ==========================================================
# Status
# ==========================================================

def has_dataset() -> bool:
    """
    Return True if a dataset exists.
    """

    return (
        DATAFRAME_KEY
        in st.session_state
    )


def has_pipeline_result() -> bool:
    """
    Return True if a completed pipeline result
    exists.
    """

    return (
        PIPELINE_RESULT_KEY
        in st.session_state
    )


# ==========================================================
# Clear
# ==========================================================

def clear_dataset() -> None:
    """
    Remove all dataset-related session state.
    """

    for key in (
        DATAFRAME_KEY,
        UPLOADED_FILE_KEY,
        DATASET_PATH_KEY,
        PIPELINE_RESULT_KEY,
    ):
        st.session_state.pop(
            key,
            None,
        )