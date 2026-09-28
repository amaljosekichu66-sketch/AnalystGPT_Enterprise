"""
Application configuration for AnalystGPT Enterprise.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# Project Configuration
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env_flag(name: str, default: bool) -> bool:
    """
    Read a boolean environment variable.

    Accepts the usual truthy spellings; anything unrecognised falls back to
    `default` rather than silently becoming False, so a typo in a security
    flag cannot quietly disable a protection.
    """
    raw = os.getenv(name)

    if raw is None:
        return default

    value = raw.strip().lower()

    if value in ("true", "1", "yes", "on"):
        return True

    if value in ("false", "0", "no", "off"):
        return False

    return default


# ==========================================================
# Deployment Environment
# ==========================================================
#
# Drives the security posture. Anything other than "development" is treated as
# a deployed environment, where insecure developer conveniences (forgeable
# identity headers, the built-in signing key) must not be available.

APP_ENVIRONMENT = (
    os.getenv(
        "APP_ENVIRONMENT",
        "development",
    )
    .strip()
    .lower()
)

IS_DEVELOPMENT = APP_ENVIRONMENT == "development"

# ==========================================================
# Logging Configuration
# ==========================================================

LOG_LEVEL_NAME = (
    os.getenv(
        "LOG_LEVEL",
        "INFO",
    )
    .strip()
    .upper()
)

LOG_LEVEL = getattr(
    logging,
    LOG_LEVEL_NAME,
    logging.INFO,
)

LOG_TO_FILE = os.getenv(
    "LOG_TO_FILE",
    "false",
).strip().lower() in ("true", "1", "yes")

LOG_DIRECTORY = PROJECT_ROOT / "logs"

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

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

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

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------
#
# A wildcard origin list combined with allow_credentials=True does NOT produce
# `Access-Control-Allow-Origin: *`. Starlette cannot send a wildcard alongside
# credentials, so it reflects the caller's Origin header instead - which makes
# every origin a trusted, credentialed origin. The allow-list below is
# therefore explicit. Set CORS_ALLOWED_ORIGINS to a comma-separated list to
# override it.

_DEFAULT_CORS_ORIGINS = f"http://localhost:{FRONTEND_PORT}," f"http://127.0.0.1:{FRONTEND_PORT}," f"{API_BASE_URL}"

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        _DEFAULT_CORS_ORIGINS,
    ).split(",")
    if origin.strip()
]

# ==========================================================
# Upload Configuration
# ==========================================================

MAX_FILE_SIZE_MB = 500

# ==========================================================
# Artifact Storage
# ==========================================================
#
# Immutable store for raw uploads and cleaned dataset versions. Overridable for
# the same reason as the database and report paths: a test run must not deposit
# dataset artifacts into the developer's working store.

ARTIFACT_STORE_DIRECTORY = Path(
    os.getenv(
        "ARTIFACT_STORE_DIRECTORY",
        str(PROJECT_ROOT / "data" / "artifacts"),
    )
)

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

# Overridable so a test session can redirect generated artifacts away from the
# developer's real `reports/` directory. Without this, a plain `pytest -q`
# wrote 19 new report files per run and overwrote analystgpt_report.txt/.pdf.
REPORT_OUTPUT_DIRECTORY = Path(
    os.getenv(
        "REPORT_OUTPUT_DIRECTORY",
        str(PROJECT_ROOT / "reports"),
    )
)

DEFAULT_REPORT_FILENAME = "analystgpt_report.txt"

DEFAULT_PDF_REPORT_FILENAME = "analystgpt_report.pdf"

# ==========================================================
# Database Configuration
# ==========================================================

DATABASE_ENGINE = (
    os.getenv(
        "DATABASE_ENGINE",
        "sqlite",
    )
    .strip()
    .lower()
)

# ----------------------------------------------------------
# SQLite
# ----------------------------------------------------------

# Overridable so a test session never opens the developer's live database.
# Without this, a plain `pytest -q` inserted 11 users, 19 AI jobs, 20 pipeline
# runs and 38 dataset versions into analystgpt.db on every run.
SQLITE_DATABASE_PATH = Path(
    os.getenv(
        "SQLITE_DATABASE_PATH",
        str(PROJECT_ROOT / "analystgpt.db"),
    )
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

if DATABASE_ENGINE == "postgresql" and not POSTGRES_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD environment variable is not set.")

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

LLM_PROVIDER = (
    os.getenv(
        "LLM_PROVIDER",
        "ollama",
    )
    .strip()
    .lower()
)

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

# The context window must hold the prompt AND the generated response.
#
# Measured against this deployment with the model's own tokenizer, using the
# real 21-column dataset:
#
#     production prompt      4,653 tokens
#     AI_MAX_TOKENS          1,024 tokens
#     required               5,677 tokens
#     previous default       4,096 tokens   -> short by 1,581
#
# The prompt alone overflowed the window by 557 tokens. llama.cpp responds by
# discarding the OLDEST tokens - which is the head of the prompt: the ROLE,
# the OBJECTIVE and the ANALYTICAL INTEGRITY RULES. The anti-hallucination
# constraints were being silently evicted before the model ever saw them, and
# what little room remained was not enough to finish the response, which is
# why generated reports lost their NARRATIVE section.
#
# Nothing surfaced this: the overflow is silent, and the resulting "Missing
# required AI sections" error pointed at the model rather than the budget.
AI_CONTEXT_WINDOW = int(
    os.getenv(
        "AI_CONTEXT_WINDOW",
        "8192",
    )
)

# ----------------------------------------------------------
# Timeout policy
# ----------------------------------------------------------
#
# Three budgets, deliberately distinct:
#
#   production   AI_TIMEOUT (this value)
#   integration  the same AI_TIMEOUT - live tests must feel what production
#                feels, otherwise a green suite proves nothing about it
#   unit tests   clamped by tests/conftest.py to 15s, because ordinary tests
#                must never block on real inference
#
# Measured against this deployment: gemma3:4b Q4_K_M on CPU, `size_vram: 0`.
#
# A full report generation, timed end to end through the production path:
#
#   cold prompt (3,849 tokens) + 658 generated    340.2 s   <- worst observed
#   live integration generation                   302.0 s   (ReadTimeout at 300)
#   live integration generation                   178.2 s
#   real AI job (ai_reports.id=49)                217.7 s
#   warm prefix cache, 600-token budget            73.8 s
#
# Prompt evaluation dominates and its throughput is not stable: 24.5 tok/s on
# an idle machine, 15.1 tok/s after sustained load. That 1.6x spread is why the
# budget needs real margin rather than a tight fit to the median.
#
# 120s (the original default) timed out on routine reports. 300s still did -
# twice, measured above. 600s covers the worst observation with roughly 1.75x
# headroom for the throughput variance.
#
# Margin matters more than it used to: `AIJobExecutor` now treats a timeout
# that consumed the whole budget as a capacity limit and fails it permanently
# WITHOUT retrying, so a budget set too tight turns a slow report into a hard
# failure rather than a retry.
#
# This is a hardware-shaped default, not a universal one. A GPU deployment
# should lower it substantially.
AI_TIMEOUT = float(
    os.getenv(
        "AI_TIMEOUT",
        "600",
    )
)

AI_MAX_RETRIES = int(
    os.getenv(
        "AI_MAX_RETRIES",
        "3",
    )
)

AI_RETRY_BASE_DELAY = float(
    os.getenv(
        "AI_RETRY_BASE_DELAY",
        "2.0",
    )
)

# ==========================================================
# Future Providers - not implemented
# ==========================================================
#
# Read here so a deployment can supply them ahead of time, but no provider
# consumes them yet: `LLMFactory._PROVIDERS` registers only "ollama" and
# raises `ValueError: Unsupported LLM Provider` for anything else. Setting one
# of these keys does NOT enable the corresponding provider.

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

#: The built-in signing key. Usable for local development only; a deployed
#: environment must supply its own, and startup fails if it does not.
INSECURE_DEFAULT_AUTH_SECRET_KEY = "analystgpt-enterprise-insecure-dev-secret-key-change-in-production"

AUTH_SECRET_KEY = os.getenv(
    "AUTH_SECRET_KEY",
    INSECURE_DEFAULT_AUTH_SECRET_KEY,
).strip()

if not IS_DEVELOPMENT and AUTH_SECRET_KEY == INSECURE_DEFAULT_AUTH_SECRET_KEY:
    raise RuntimeError(
        "AUTH_SECRET_KEY is still the built-in development key while "
        f"APP_ENVIRONMENT='{APP_ENVIRONMENT}'. Access tokens signed with a "
        "publicly known key can be forged for any user and role. Set "
        "AUTH_SECRET_KEY to a private random value."
    )

# ----------------------------------------------------------
# Unauthenticated identity headers (development only)
# ----------------------------------------------------------
#
# `X-User-Id` / `X-User-Name` / `X-User-Role` let a caller assert an identity,
# including ADMIN, with no token and no verification. That is a complete
# authentication bypass, so it is OFF unless a developer opts in explicitly.
#
# The flag cannot be enabled outside development: the guard below refuses the
# combination rather than honouring it.

AUTH_ALLOW_HEADER_IDENTITY = _env_flag(
    "AUTH_ALLOW_HEADER_IDENTITY",
    default=False,
)

if AUTH_ALLOW_HEADER_IDENTITY and not IS_DEVELOPMENT:
    raise RuntimeError(
        "AUTH_ALLOW_HEADER_IDENTITY is enabled while "
        f"APP_ENVIRONMENT='{APP_ENVIRONMENT}'. Unauthenticated identity "
        "headers are a development-only convenience and must never be "
        "enabled in a deployed environment."
    )

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
