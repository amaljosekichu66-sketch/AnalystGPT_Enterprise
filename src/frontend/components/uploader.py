"""
Dataset uploader component for AnalystGPT Enterprise.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


SUPPORTED_FILE_TYPES = [
    "csv",
    "xlsx",
    "json",
]


def load_dataframe(uploaded_file):
    """
    Load the uploaded dataset into a pandas DataFrame.
    """

    extension = Path(uploaded_file.name).suffix.lower()

    if extension == ".csv":
        return pd.read_csv(uploaded_file)

    if extension == ".xlsx":
        return pd.read_excel(uploaded_file)

    if extension == ".json":
        return pd.read_json(uploaded_file)

    raise ValueError("Unsupported file format.")


def render_uploader():
    """
    Render the dataset uploader.
    """

    uploaded_file = st.file_uploader(
        label="Select a dataset",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.info(
            "Please select a CSV, Excel, or JSON dataset."
        )
        return None, None

    try:

        df = load_dataframe(uploaded_file)

    except Exception as error:

        st.error(
            f"Unable to read dataset.\n\n{error}"
        )

        return None, None

    st.success("Dataset loaded successfully.")

    return uploaded_file, df