"""
Application-wide constants for AnalystGPT Enterprise.
"""

# ==========================================================
# Application Information
# ==========================================================

APP_NAME = "AnalystGPT Enterprise"

APP_VERSION = "8.0.0"

APP_AUTHOR = "Amal Jose"

APP_DESCRIPTION = (
    "Enterprise-grade analytics platform providing REST APIs for "
    "data upload, cleaning, quality assessment, analytics, "
    "reporting, and persistence."
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
# Date & Formatting
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