"""
Application configuration for AnalystGPT Enterprise.
"""

from __future__ import annotations

import logging
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ==========================================================
# Project Configuration
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ==========================================================
# Logging Configuration
# ==========================================================

LOG_LEVEL_NAME = os.getenv(
    "LOG_LEVEL",
    "INFO",
).strip().upper()

LOG_LEVEL = getattr(
    logging,
    LOG_LEVEL_NAME,
    logging.INFO,
)

LOG_TO_FILE = os.getenv(
    "LOG_TO_FILE",
    "false",
).strip().lower() in ("true", "1", "yes")

LOG_DIRECTORY = (
    PROJECT_ROOT / "logs"
)

LOG_FILE_PATH = Path(
    os.getenv(
        "LOG_FILE_PATH",
        str(LOG_DIRECTORY / "analystgpt.log"),
    )
)

LOG_MAX_BYTES = int(
    os.getenv(
        "LOG_MAX_BYTES",
        str(10 * 1024 * 1024),
    )
)

LOG_BACKUP_COUNT = int(
    os.getenv(
        "LOG_BACKUP_COUNT",
        "5",
    )
)

LOG_FORMAT = (
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# ==========================================================
# Web API & Networking Configuration
# ==========================================================

API_HOST = os.getenv(
    "API_HOST",
    "0.0.0.0",
).strip()

API_PORT = int(
    os.getenv(
        "API_PORT",
        "8000",
    )
)

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).strip()

FRONTEND_PORT = int(
    os.getenv(
        "FRONTEND_PORT",
        "8501",
    )
)

# ==========================================================
# Upload Configuration
# ==========================================================

MAX_FILE_SIZE_MB = 500

# ==========================================================
# Cleaning Configuration
# ==========================================================

RESET_INDEX_AFTER_CLEANING = True

DEFAULT_DATATYPE_MAP: dict[str, str] = {
    # Example:
    # "joining_date": "datetime64[ns]",
    # "age": "int64",
    # "salary": "float64",
}

# ==========================================================
# Reporting Configuration
# ==========================================================

REPORT_OUTPUT_DIRECTORY = (
    PROJECT_ROOT / "reports"
)

DEFAULT_REPORT_FILENAME = (
    "analystgpt_report.txt"
)

# ==========================================================
# Database Configuration
# ==========================================================

DATABASE_ENGINE = os.getenv(
    "DATABASE_ENGINE",
    "sqlite",
).strip().lower()

# ----------------------------------------------------------
# SQLite
# ----------------------------------------------------------

SQLITE_DATABASE_PATH = (
    PROJECT_ROOT / "analystgpt.db"
)

# ----------------------------------------------------------
# PostgreSQL
# ----------------------------------------------------------

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost",
)

POSTGRES_PORT = int(
    os.getenv(
        "POSTGRES_PORT",
        "5433",
    )
)

POSTGRES_DATABASE = os.getenv(
    "POSTGRES_DATABASE",
    "analystgpt",
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "postgres",
)

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
# Frontend Configuration
# ==========================================================

DATAFRAME_PREVIEW_ROWS = 100

MAX_CHART_ROWS = 100_000

MAX_PROFILE_ROWS = 100_000

MAX_CORRELATION_ROWS = 100_000

# ==========================================================
# AI Configuration
# ==========================================================

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "ollama",
).strip().lower()

# ----------------------------------------------------------
# Ollama
# ----------------------------------------------------------

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma3:4b",
)

OLLAMA_KEEP_ALIVE = os.getenv(
    "OLLAMA_KEEP_ALIVE",
    "30m",
)

# ==========================================================
# Generation Parameters
# ==========================================================

AI_TEMPERATURE = float(
    os.getenv(
        "AI_TEMPERATURE",
        "0.2",
    )
)

AI_TOP_P = float(
    os.getenv(
        "AI_TOP_P",
        "0.90",
    )
)

AI_MAX_TOKENS = int(
    os.getenv(
        "AI_MAX_TOKENS",
        "1024",
    )
)

AI_CONTEXT_WINDOW = int(
    os.getenv(
        "AI_CONTEXT_WINDOW",
        "4096",
    )
)

AI_TIMEOUT = float(
    os.getenv(
        "AI_TIMEOUT",
        "120",
    )
)

AI_MAX_RETRIES = int(
    os.getenv(
        "AI_MAX_RETRIES",
        "3",
    )
)

# ==========================================================
# Future Providers (Sprint 12+)
# ==========================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
)

CLAUDE_API_KEY = os.getenv(
    "CLAUDE_API_KEY",
)

# ==========================================================
# Enterprise Identity & Security (Sprint 13)
# ==========================================================

AUTH_SECRET_KEY = os.getenv(
    "AUTH_SECRET_KEY",
    "analystgpt-enterprise-insecure-dev-secret-key-change-in-production",
).strip()

AUTH_ALGORITHM = os.getenv(
    "AUTH_ALGORITHM",
    "HS256",
).strip()

AUTH_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)

AUTH_PASSWORD_MIN_LENGTH = int(
    os.getenv(
        "AUTH_PASSWORD_MIN_LENGTH",
        "8",
    )
)

AUTH_DEFAULT_ADMIN_USERNAME = os.getenv(
    "AUTH_DEFAULT_ADMIN_USERNAME",
    "admin",
).strip()

AUTH_DEFAULT_ADMIN_EMAIL = os.getenv(
    "AUTH_DEFAULT_ADMIN_EMAIL",
    "admin@analystgpt.enterprise",
).strip()