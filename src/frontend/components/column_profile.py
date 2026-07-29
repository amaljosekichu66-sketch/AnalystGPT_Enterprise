"""
Column profile component for AnalystGPT Enterprise.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.core.config import (
    MAX_PROFILE_ROWS,
)


def _prepare_profile_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare a sampled dataframe for profiling.

    Very large datasets are sampled to improve
    rendering performance.
    """

    if len(dataframe) <= MAX_PROFILE_ROWS:
        return dataframe

    return dataframe.sample(
        n=MAX_PROFILE_ROWS,
        random_state=42,
    )


def render_column_profile(
    dataframe: pd.DataFrame,
) -> None:
    """
    Render column profile.
    """

    st.subheader("Column Profile")

    profile_df = _prepare_profile_dataframe(
        dataframe,
    )

    if len(profile_df) != len(dataframe):

        st.caption(
            f"Profile generated from "
            f"{len(profile_df):,} sampled rows "
            f"out of {len(dataframe):,}."
        )

    profile_rows = []

    for column in profile_df.columns:

        series = profile_df[column]

        profile_rows.append(
            {
                "Column": column,
                "Data Type": str(series.dtype),
                "Non-Null": int(series.notna().sum()),
                "Missing": int(series.isna().sum()),
                "Unique": int(series.nunique(dropna=True)),
            }
        )

    profile = pd.DataFrame(
        profile_rows,
    )

    st.dataframe(
        profile,
        hide_index=True,
        width="stretch",  # changed from use_container_width=True
    )