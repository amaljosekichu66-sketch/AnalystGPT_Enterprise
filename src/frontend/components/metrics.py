"""
Reusable metric components for AnalystGPT Enterprise.
"""

import streamlit as st


def render_metric_card(
    label: str,
    value,
    delta: str | None = None,
) -> None:
    """
    Render a single KPI metric.
    """

    st.metric(
        label=label,
        value=value,
        delta=delta,
    )


def render_metric_grid(
    metrics: list[dict],
) -> None:
    """
    Render KPI metrics in a responsive grid.

    Parameters
    ----------
    metrics
        Example:

        [
            {"label":"Rows","value":"500"},
            {"label":"Columns","value":"8"},
        ]
    """

    if not metrics:
        return

    columns = st.columns(len(metrics))

    for column, metric in zip(columns, metrics):

        with column:

            render_metric_card(
                label=metric["label"],
                value=metric["value"],
                delta=metric.get("delta"),
            )