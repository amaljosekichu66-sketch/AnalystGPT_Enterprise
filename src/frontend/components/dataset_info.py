"""
Dataset information component for AnalystGPT Enterprise.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def _calculate_dataset_info(
    dataframe: pd.DataFrame,
    file_size: int | None,
    file_extension: str,
) -> dict:
    """
    Calculate dataset information.

    Cached automatically by Streamlit.
    """

    rows = len(dataframe)

    columns = len(dataframe.columns)

    memory = (
        dataframe.memory_usage(
            deep=True,
        ).sum()
        / 1024
    )

    missing = int(
        dataframe.isna().sum().sum()
    )

    return {
        "rows": rows,
        "columns": columns,
        "file_size": (
            file_size / 1024
            if file_size
            else None
        ),
        "memory": memory,
        "missing": missing,
        "extension": file_extension.upper(),
    }


def render_dataset_info(
    uploaded_file,
    dataframe: pd.DataFrame,
) -> None:
    """
    Render dataset information.
    """

    st.subheader(
        "Dataset Information"
    )

    extension = (
        uploaded_file.name
        .split(".")[-1]
    )

    file_size = getattr(
        uploaded_file,
        "size",
        None,
    )

    info = _calculate_dataset_info(
        dataframe,
        file_size,
        extension,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Rows",
        f"{info['rows']:,}",
    )

    col2.metric(
        "Columns",
        info["columns"],
    )

    if info["file_size"] is not None:

        col3.metric(
            "File Size",
            f"{info['file_size']:.1f} KB",
        )

    else:

        col3.metric(
            "File Size",
            "Unknown",
        )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Type",
        f".{info['extension']}",
    )

    col2.metric(
        "Memory",
        f"{info['memory']:.1f} KB",
    )

    col3.metric(
        "Missing Values",
        f"{info['missing']:,}",
    )