"""
Export button component for AnalystGPT Enterprise.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def render_export_buttons(
    export_result: dict,
    key_prefix: str = "export",
) -> None:
    """
    Render download buttons after a report has been generated successfully.
    """
    if not export_result.get("success"):
        return

    export_path = export_result.get("export_path") or export_result.get("path")
    raw_data = export_result.get("data") or export_result.get("bytes")

    if not export_path and raw_data is None:
        return

    data: bytes
    filename = export_result.get("filename")
    mime = export_result.get("mime_type")

    if raw_data is not None:
        data = raw_data if isinstance(raw_data, bytes) else str(raw_data).encode("utf-8")
        if not mime:
            mime = "application/pdf" if data.startswith(b"%PDF-") else "text/plain"
        if not filename:
            filename = "analystgpt_report.pdf" if mime == "application/pdf" else "analystgpt_report.txt"
    else:
        path = Path(export_path)
        if not path.exists():
            st.warning("Generated report file could not be found on disk.")
            return
        data = path.read_bytes()
        if not filename:
            filename = path.name
        if not mime:
            mime = "application/pdf" if path.suffix.lower() == ".pdf" else "text/plain"

    is_pdf = mime == "application/pdf" or filename.lower().endswith(".pdf")
    label = "⬇ Download PDF Report" if is_pdf else "⬇ Download Text Report"

    btn_key = f"dl_btn_{key_prefix}_{filename}"

    st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime=mime,
        width="stretch",
        key=btn_key,
    )
