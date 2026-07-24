"""
Export button component for AnalystGPT Enterprise.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def render_export_buttons(
    export_result: dict,
) -> None:
    """
    Render download buttons after a report
    has been generated successfully.
    """

    if not export_result.get("success"):
        return

    export_path = export_result.get("export_path")

    if not export_path:
        return

    path = Path(export_path)

    if not path.exists():

        st.warning("Generated report could not be found.")

        return

    with open(
        path,
        "rb",
    ) as file:

        st.download_button(
            label="⬇ Download Report",
            data=file,
            file_name=path.name,
            mime="text/plain",
            use_container_width=True,
        )