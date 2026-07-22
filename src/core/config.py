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

MAX_FILE_SIZE_MB = 100

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

# Supported values:
#   "sqlite"
#   "postgresql"
#
# Default:
#   SQLite (recommended for local development)
#
# Override using the DATABASE_ENGINE environment variable:
#
# Windows PowerShell:
#   $env:DATABASE_ENGINE = "postgresql"
#
# Linux/macOS:
#   export DATABASE_ENGINE=postgresql
#
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

# Read password from the environment.
# Required only when PostgreSQL is selected.

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if DATABASE_ENGINE == "postgresql" and not POSTGRES_PASSWORD:
    raise RuntimeError(
        "POSTGRES_PASSWORD environment variable is not set."
    )

# ==========================================================
# Future Configuration
# ==========================================================

# API_TIMEOUT = 30

# DEBUG = False