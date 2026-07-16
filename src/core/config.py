"""
Application configuration for AnalystGPT Enterprise.
"""

from pathlib import Path
import logging

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
# Future Configuration
# ==========================================================

# DATABASE_URL = ""

# API_TIMEOUT = 30

# DEBUG = False