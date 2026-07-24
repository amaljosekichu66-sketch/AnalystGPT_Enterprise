"""
Session management for AnalystGPT Enterprise.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


# ==========================================================
# Session Keys
# ==========================================================

DATAFRAME_KEY = "dataframe"

UPLOADED_FILE_KEY = "uploaded_file"


# ==========================================================
# Store
# ==========================================================


def store_dataset(
    uploaded_file,
    dataframe: pd.DataFrame,
) -> None:
    """
    Store the uploaded dataset in the Streamlit session.
    """

    st.session_state[UPLOADED_FILE_KEY] = uploaded_file

    st.session_state[DATAFRAME_KEY] = dataframe


# ==========================================================
# Getters
# ==========================================================


def get_dataframe():
    """
    Return the stored dataframe.
    """

    return st.session_state.get(
        DATAFRAME_KEY,
    )


def get_uploaded_file():
    """
    Return the stored uploaded file.
    """

    return st.session_state.get(
        UPLOADED_FILE_KEY,
    )


def get_dataset():
    """
    Return the uploaded file and dataframe.

    Returns
    -------
    tuple
        (uploaded_file, dataframe)
    """

    return (
        get_uploaded_file(),
        get_dataframe(),
    )


# ==========================================================
# Status
# ==========================================================


def has_dataset() -> bool:
    """
    Return True if a dataset exists in the session.
    """

    return (
        DATAFRAME_KEY
        in st.session_state
    )


# ==========================================================
# Clear
# ==========================================================


def clear_dataset() -> None:
    """
    Remove the current dataset from the session.
    """

    st.session_state.pop(
        DATAFRAME_KEY,
        None,
    )

    st.session_state.pop(
        UPLOADED_FILE_KEY,
        None,
    )