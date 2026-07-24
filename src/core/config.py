"""
Application configuration for AnalystGPT Enterprise.
"""

from pathlib import Path
import logging
import os

# ==========================================================
# Logging Configuration
# ==========================================================

LOG_LEVEL = logging.INFO

# ==========================================================
# Upload Configuration
# ==========================================================

# Maximum supported upload size.
#
# NOTE:
# Streamlit also enforces its own upload limit.
# Set the same value in:
#
# .streamlit/config.toml
#
# server.maxUploadSize = 500
#
MAX_FILE_SIZE_MB = 500

# ==========================================================
# Cleaning Configuration
# ==========================================================

RESET_INDEX_AFTER_CLEANING = True

DEFAULT_DATATYPE_MAP = {
    # Example:
    # "joining_date": "datetime",
    # "age": "int64",
    # "salary": "float64",
}

# ==========================================================
# Reporting Configuration
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_OUTPUT_DIRECTORY = PROJECT_ROOT / "reports"

DEFAULT_REPORT_FILENAME = "analystgpt_report.txt"

# ==========================================================
# Database Configuration
# ==========================================================

DATABASE_ENGINE = os.getenv(
    "DATABASE_ENGINE",
    "sqlite",
).lower()

# ---------------- SQLite ----------------

SQLITE_DATABASE_PATH = "analystgpt.db"

# ---------------- PostgreSQL ----------------

POSTGRES_HOST = "localhost"

POSTGRES_PORT = 5433

POSTGRES_DATABASE = "analystgpt"

POSTGRES_USER = "postgres"

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
)

if (
    DATABASE_ENGINE == "postgresql"
    and not POSTGRES_PASSWORD
):
    raise RuntimeError(
        "POSTGRES_PASSWORD environment variable is not set."
    )

# ==========================================================
# Future Configuration
# ==========================================================

# API_TIMEOUT = 30

# DEBUG = False
# ==========================================================
# Frontend Performance Configuration
# ==========================================================

# Maximum rows displayed in preview tables.
DATAFRAME_PREVIEW_ROWS = 100

# Maximum rows sampled for charts.
MAX_CHART_ROWS = 100_000

# Maximum rows sampled for column profiling.
MAX_PROFILE_ROWS = 100_000

# Maximum rows sampled for correlation analysis.
MAX_CORRELATION_ROWS = 100_000