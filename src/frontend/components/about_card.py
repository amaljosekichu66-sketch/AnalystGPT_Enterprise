"""
About card component for AnalystGPT Enterprise.
"""

import streamlit as st


def render_about_card() -> None:
    """
    Render project information.
    """

    st.subheader("📘 Project Overview")

    st.markdown(
        """
**AnalystGPT Enterprise** is an enterprise-grade analytics platform
designed with a modular architecture.

The application provides an end-to-end analytics workflow including:

- Dataset Upload
- Data Cleaning
- Data Quality Assessment
- Analytics
- Reporting
- Dashboard
- REST API
- Power BI Integration
- AI Insights (Sprint 11)
"""
    )

    st.divider()

    st.subheader("🏗 Architecture")

    st.code(
        """
Frontend (Streamlit)
        │
        ▼
Frontend Services
        │
        ▼
REST API
        │
        ▼
Application Layer
        │
        ▼
Managers
        │
        ▼
Database
""",
        language="text",
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Version**")

        st.write("v10.0.0-dev")

        st.write("**License**")

        st.write("MIT")

    with col2:

        st.write("**Backend**")

        st.write("FastAPI")

        st.write("**Frontend**")

        st.write("Streamlit")

    st.divider()

    st.subheader("🛠 Technologies")

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
"""
    )

    st.divider()

    st.subheader("📂 Repository")

    st.info(
        "GitHub repository configured for AnalystGPT Enterprise."
    )