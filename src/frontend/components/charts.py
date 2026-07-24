"""
Chart component for AnalystGPT Enterprise.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.core.config import (
    MAX_CHART_ROWS,
)


def _prepare_chart_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare a sampled dataframe for chart rendering.

    Large datasets are sampled to improve rendering
    performance while preserving representative trends.
    """

    if len(dataframe) <= MAX_CHART_ROWS:
        return dataframe

    return dataframe.sample(
        n=MAX_CHART_ROWS,
        random_state=42,
    )


def render_charts(
    dataframe: pd.DataFrame,
) -> None:
    """
    Render dataset charts.
    """

    st.subheader("📊 Charts")

    chart_df = _prepare_chart_dataframe(
        dataframe,
    )

    if len(dataframe) > len(chart_df):

        st.caption(
            f"Charts are generated using a "
            f"random sample of "
            f"{len(chart_df):,} rows "
            f"from {len(dataframe):,} total rows."
        )

    # ==========================================================
    # Numeric Distributions
    # ==========================================================

    st.markdown("### Numeric Distributions")

    numeric_columns = chart_df.select_dtypes(
        include="number",
    ).columns

    if len(numeric_columns) == 0:

        st.info(
            "No numeric columns available."
        )

    else:

        for column in numeric_columns:

            # Skip identifier columns
            if column.lower().endswith("_id") or column.lower() == "id":
                continue

            fig, ax = plt.subplots(
                figsize=(8, 4),
            )

            chart_df[column].dropna().hist(
                bins=30,
                ax=ax,
            )

            ax.set_title(column)

            st.pyplot(fig)

            plt.close(fig)

    # ==========================================================
    # Categorical Columns
    # ==========================================================

    st.markdown("### Categorical Columns")

    categorical_columns = chart_df.select_dtypes(
        exclude="number",
    ).columns

    if len(categorical_columns) == 0:

        st.info(
            "No categorical columns available."
        )

    else:

        for column in categorical_columns:

            value_counts = (
                chart_df[column]
                .fillna("Missing")
                .value_counts()
                .head(10)
            )

            fig, ax = plt.subplots(
                figsize=(8, 4),
            )

            value_counts.plot.bar(
                ax=ax,
            )

            ax.set_title(column)

            st.pyplot(fig)

            plt.close(fig)

    # ==========================================================
    # Missing Values
    # ==========================================================

    st.markdown("### Missing Values")

    missing = (
        chart_df
        .isna()
        .sum()
    )

    missing = missing[
        missing > 0
    ]

    if missing.empty:

        st.success(
            "No missing values detected."
        )

    else:

        fig, ax = plt.subplots(
            figsize=(8, 4),
        )

        missing.plot.bar(
            ax=ax,
        )

        ax.set_title(
            "Missing Values by Column"
        )

        st.pyplot(fig)

        plt.close(fig)

    # ==========================================================
    # Correlation Matrix
    # ==========================================================

    st.markdown("### Correlation Matrix")

    numeric_df = chart_df.select_dtypes(
        include="number",
    )

    if numeric_df.shape[1] < 2:

        st.info(
            "Not enough numeric columns."
        )

    else:

        corr = numeric_df.corr(
            numeric_only=True,
        )

        fig, ax = plt.subplots(
            figsize=(7, 6),
        )

        image = ax.imshow(
            corr,
        )

        ax.set_xticks(
            range(len(corr.columns))
        )

        ax.set_yticks(
            range(len(corr.columns))
        )

        ax.set_xticklabels(
            corr.columns,
            rotation=90,
        )

        ax.set_yticklabels(
            corr.columns,
        )

        plt.colorbar(
            image,
        )

        st.pyplot(fig)

        plt.close(fig)