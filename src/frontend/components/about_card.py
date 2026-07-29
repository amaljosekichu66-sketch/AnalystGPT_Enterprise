"""
About card component for AnalystGPT Enterprise.
"""

from __future__ import annotations

import streamlit as st

from src.core.constants import (
    APP_NAME,
    APP_VERSION,
)


def render_about_card() -> None:
    """
    Render project information.
    """

    st.subheader("📘 Project Overview")

    st.markdown(
        f"""
**{APP_NAME}** is an enterprise-grade analytics platform
designed using a modular, production-oriented architecture.

The platform provides a complete analytics workflow including:

- Dataset Upload
- Data Cleaning
- Data Quality Assessment
- Analytics
- Reporting
- Enterprise Dashboard
- REST API
- Power BI Integration
- AI Insight Engine
"""
    )

    st.divider()

    st.subheader("🏗 Architecture")

    st.code(
        """
Streamlit Frontend
        │
        ▼
Frontend Service Layer
        │
        ▼
FastAPI REST API
        │
        ▼
Application Layer
        │
        ▼
Domain Managers
        │
        ▼
Persistence Layer
        │
        ▼
SQLite / PostgreSQL
""",
        language="text",
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Version**")
        st.write(APP_VERSION)

        st.write("**License**")
        st.write("MIT")

        st.write("**Architecture**")
        st.write("Modular")

    with col2:

        st.write("**Backend**")
        st.write("FastAPI")

        st.write("**Frontend**")
        st.write("Streamlit")

        st.write("**AI Engine**")
        st.write("Ollama")

    st.divider()

    st.subheader("🛠 Technology Stack")

    st.markdown(
        """
- Python
- Pandas
- Streamlit
- FastAPI
- PostgreSQL
- SQLite
- Plotly
- Power BI
- Ollama
- REST APIs
"""
    )

    st.divider()

    st.subheader("🚀 Current Capabilities")

    st.success("✅ Enterprise Analytics Pipeline")
    st.success("✅ AI Insight Engine")
    st.success("✅ Power BI Integration")
    st.success("✅ REST API")
    st.success("✅ Streamlit Frontend")
    st.success("✅ PostgreSQL Persistence")

    st.divider()

    st.subheader("📂 Repository")

    st.info(
        "AnalystGPT Enterprise is developed using a "
        "modular architecture following enterprise "
        "software engineering practices."
    )