"""
Dataset quality component for AnalystGPT Enterprise.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def _calculate_quality_metrics(
    dataframe: pd.DataFrame,
) -> dict:
    """
    Calculate dataset quality metrics.

    Cached automatically by Streamlit.
    """

    rows = len(dataframe)

    columns = len(dataframe.columns)

    total_cells = rows * columns

    missing = int(
        dataframe.isna().sum().sum()
    )

    duplicates = int(
        dataframe.duplicated().sum()
    )

    completeness = (
        (
            total_cells - missing
        )
        / total_cells
        * 100
        if total_cells
        else 100
    )

    numeric_columns = (
        dataframe.select_dtypes(
            include="number",
        ).shape[1]
    )

    categorical_columns = (
        dataframe.select_dtypes(
            exclude="number",
        ).shape[1]
    )

    return {
        "completeness": completeness,
        "missing": missing,
        "duplicates": duplicates,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "total_cells": total_cells,
    }


def render_dataset_quality(
    dataframe: pd.DataFrame,
) -> None:
    """
    Render dataset quality summary.
    """

    st.subheader(
        "Dataset Quality"
    )

    metrics = _calculate_quality_metrics(
        dataframe,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Completeness",
        f"{metrics['completeness']:.2f}%",
    )

    col2.metric(
        "Missing Values",
        f"{metrics['missing']:,}",
    )

    col3.metric(
        "Duplicate Rows",
        f"{metrics['duplicates']:,}",
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Numeric Columns",
        metrics["numeric_columns"],
    )

    col2.metric(
        "Categorical Columns",
        metrics["categorical_columns"],
    )

    col3.metric(
        "Total Cells",
        f"{metrics['total_cells']:,}",
    )

    if (
        metrics["missing"] > 0
        or metrics["duplicates"] > 0
    ):

        st.warning(
            "Dataset contains quality issues that "
            "should be cleaned before analysis."
        )

    else:

        st.success(
            "Dataset quality looks excellent."
        )