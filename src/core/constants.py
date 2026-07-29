"""
Application-wide constants for AnalystGPT Enterprise.
"""

from __future__ import annotations

# ==========================================================
# Application Information
# ==========================================================

APP_NAME = "AnalystGPT Enterprise"

APP_VERSION = "11.0.0"

APP_AUTHOR = "Amal Jose"

APP_DESCRIPTION = (
    "Enterprise-grade analytics platform providing "
    "data upload, cleaning, quality assessment, "
    "analytics, reporting, AI-powered business "
    "insights, Power BI integration, REST APIs, "
    "and Streamlit dashboard visualisation."
)

# ==========================================================
# Reporting
# ==========================================================

REPORT_TITLE = f"{APP_NAME} Report"

DEFAULT_TEXT_ENCODING = "utf-8"

# ==========================================================
# Logging
# ==========================================================

LOGGER_NAME = APP_NAME

# ==========================================================
# Formatting
# ==========================================================

DEFAULT_DECIMAL_PRECISION = 4

# ==========================================================
# Application Status
# ==========================================================

APP_STATUS = "running"

HEALTH_STATUS = "healthy"

# ==========================================================
# REST API
# ==========================================================

API_PREFIX = "/api"

API_DOCS_URL = "/docs"

API_REDOC_URL = "/redoc"

API_OPENAPI_URL = "/openapi.json"

# ==========================================================
# AI
# ==========================================================

AI_SECTION_EXECUTIVE_SUMMARY = (
    "EXECUTIVE SUMMARY"
)

AI_SECTION_RECOMMENDATIONS = (
    "RECOMMENDATIONS"
)

AI_SECTION_EXPLANATIONS = (
    "EXPLANATIONS"
)

AI_SECTION_NARRATIVE = (
    "NARRATIVE"
)

AI_STOP_SEQUENCE = "END RESPONSE"

# ==========================================================
# Frontend
# ==========================================================

FRONTEND_TITLE = APP_NAME

FRONTEND_PAGE_ICON = "📊"

FRONTEND_LAYOUT = "wide"

FRONTEND_SIDEBAR_STATE = "expanded"