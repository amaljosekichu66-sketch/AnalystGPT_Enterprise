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
#
# Development mode must be chosen EXPLICITLY. An unset APP_ENVIRONMENT used to
# mean "development", so a deployment that simply forgot the variable (Docker
# Compose did) ran with the published signing key. Unset now fails closed.

APP_ENVIRONMENT = (
    os.getenv(
        "APP_ENVIRONMENT",
        "production",
    )
    .strip()
    .lower()
) or "production"

IS_DEVELOPMENT = APP_ENVIRONMENT == "development"

#: Interactive API docs (/docs, /redoc) and the /openapi.json schema. Off
#: outside development unless explicitly enabled (SEC-17): they hand an
#: attacker a map of every endpoint and model.
API_DOCS_ENABLED = _env_flag("API_DOCS_ENABLED", default=IS_DEVELOPMENT)

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

# Loopback by default (SEC-17). Containers bind 0.0.0.0 explicitly in the
# Dockerfile CMD; a bare-metal deployment should sit behind a reverse proxy.
API_HOST = os.getenv(
    "API_HOST",
    "127.0.0.1",
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

# Host header allow-list (L14). "*" disables the check; development defaults
# to it. Deployed environments default to the compose topology: the API is
# reached as `api` by the frontend and as localhost by health checks. Add
# your public hostname when the API sits behind a reverse proxy.
API_ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("API_ALLOWED_HOSTS", "*" if IS_DEVELOPMENT else "api,localhost,127.0.0.1").split(",")
    if host.strip()
]

# Strict-Transport-Security on API responses (L14). Enable only when the API
# is served over HTTPS on a stable hostname.
API_HSTS_ENABLED = _env_flag("API_HSTS_ENABLED", default=False)

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

# Enforced server-side by `src/upload/upload_policy.py` on POST /api/datasets,
# before the payload is persisted or parsed.
# 100 MB, matching the Streamlit uploader (M5): 500 MB CSV and JSON files
# were parsed fully in memory.
MAX_FILE_SIZE_MB = int(
    os.getenv(
        "MAX_FILE_SIZE_MB",
        "100",
    )
)

# pandas has no streaming JSON reader, so JSON gets its own, smaller cap (M5).
MAX_JSON_FILE_SIZE_MB = int(os.getenv("MAX_JSON_FILE_SIZE_MB", "50"))

# Expensive-operation quotas (M6, M7). AI insight jobs are queued per user;
# the pipeline refuses to start another while this many are unfinished.
MAX_ACTIVE_AI_JOBS_PER_USER = int(os.getenv("MAX_ACTIVE_AI_JOBS_PER_USER", "2"))
#: Jobs waiting for an AI worker, across all users. Beyond it a job stays
#: PENDING and is picked up when capacity frees.
AI_MAX_QUEUED_JOBS = int(os.getenv("AI_MAX_QUEUED_JOBS", "32"))
#: Per-client limits ("<requests>/<seconds>").
PIPELINE_RATE_LIMIT = os.getenv("PIPELINE_RATE_LIMIT", "10/60").strip()
AI_RETRY_RATE_LIMIT = os.getenv("AI_RETRY_RATE_LIMIT", "10/60").strip()
GOVERNANCE_PREVIEW_RATE_LIMIT = os.getenv("GOVERNANCE_PREVIEW_RATE_LIMIT", "30/60").strip()

# AI job leases (L12), in seconds. A GENERATING job's lease is one attempt
# (AI_TIMEOUT) plus this margin; a PENDING job's covers its wait for a worker.
# Only jobs whose lease has expired are treated as interrupted, so one API
# process starting up no longer resets another process's in-flight jobs.
# At API startup, treat every unfinished AI job as interrupted (P2-02). Correct
# for one API worker; with several, set false so only expired leases count.
AI_RECOVER_ALL_ON_STARTUP = _env_flag("AI_RECOVER_ALL_ON_STARTUP", default=True)
AI_JOB_LEASE_MARGIN_SECONDS = int(os.getenv("AI_JOB_LEASE_MARGIN_SECONDS", "120"))
AI_JOB_PENDING_TTL_SECONDS = int(os.getenv("AI_JOB_PENDING_TTL_SECONDS", "7200"))

# Cleaning policy approval (P2-04): when true, a proposer cannot approve their
# own policy, so only an administrator approves.
GOVERNANCE_REQUIRE_SEPARATE_APPROVER = _env_flag("GOVERNANCE_REQUIRE_SEPARATE_APPROVER", default=False)

# Audit rows older than this many days are deleted at startup (P2-14).
# 0 keeps them forever.
AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "365"))

# Uploaded datasets older than this many days are deleted at startup (I7).
# 0 keeps them until the owner deletes them or the account is purged.
DATASET_RETENTION_DAYS = int(os.getenv("DATASET_RETENTION_DAYS", "0"))

# In-memory pipeline result caches (L10): bounded LRU with a time-to-live.
RESULT_CACHE_MAX_ENTRIES = int(os.getenv("RESULT_CACHE_MAX_ENTRIES", "256"))
RESULT_CACHE_TTL_SECONDS = int(os.getenv("RESULT_CACHE_TTL_SECONDS", str(6 * 3600)))

# Every other API request body (JSON) is capped at this size (M3, L14),
# enforced as bytes arrive by `src/api/body_limit.py`.
MAX_REQUEST_BODY_KB = int(os.getenv("MAX_REQUEST_BODY_KB", "1024"))

# Parsed-shape limits (SEC-10), checked after parsing and before the dataset is
# registered. 1,000,000 rows admits the repository's stress-test dataset.
MAX_UPLOAD_ROWS = int(os.getenv("MAX_UPLOAD_ROWS", "1000000"))
MAX_UPLOAD_COLUMNS = int(os.getenv("MAX_UPLOAD_COLUMNS", "1000"))

# .xlsx is a zip archive; these are checked on the archive directory BEFORE any
# decompression (SEC-10). A 94 KB workbook expanding 406:1 to 37 MB of sheet
# XML used to cost ~57 s of parsing per request. Normal workbooks compress
# roughly 3-10:1.
MAX_XLSX_UNCOMPRESSED_MB = int(os.getenv("MAX_XLSX_UNCOMPRESSED_MB", "256"))
MAX_XLSX_COMPRESSION_RATIO = int(os.getenv("MAX_XLSX_COMPRESSION_RATIO", "100"))
MAX_XLSX_ENTRIES = int(os.getenv("MAX_XLSX_ENTRIES", "1000"))

# Concurrent heavy jobs (uploads being parsed + pipeline runs) per user
# (SEC-10). Further requests get 429 until one finishes.
MAX_CONCURRENT_JOBS_PER_USER = int(os.getenv("MAX_CONCURRENT_JOBS_PER_USER", "2"))

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

# TLS to PostgreSQL (L11). libpq's default, "prefer", encrypts when it can but
# never verifies the server. Use "verify-full" (with POSTGRES_SSLROOTCERT) when
# the database is not on the same host or compose network.
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE", "prefer").strip()
POSTGRES_SSLROOTCERT = os.getenv("POSTGRES_SSLROOTCERT", "").strip() or None
POSTGRES_CONNECT_TIMEOUT = int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "10"))

# ==========================================================
# Frontend Configuration
# ==========================================================

DATAFRAME_PREVIEW_ROWS = 100

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

# Ollama has no authentication of its own and plain HTTP carries every prompt
# (dataset values) in clear (L11). A non-local OLLAMA_HOST must be https -
# typically an authenticating reverse proxy; set OLLAMA_API_KEY and the client
# sends it as a bearer token - unless this is explicitly acknowledged.
OLLAMA_ALLOW_INSECURE = _env_flag("OLLAMA_ALLOW_INSECURE", default=False)

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
# Enterprise Identity & Security (Sprint 13)
# ==========================================================

#: The built-in signing key. It is published in this repository, so anyone
#: can forge a token for any user and role with it. Usable ONLY when
#: APP_ENVIRONMENT=development is set explicitly.
INSECURE_DEFAULT_AUTH_SECRET_KEY = "analystgpt-enterprise-insecure-dev-secret-key-change-in-production"

#: The value `.env.example` ships (P2-18). It is long enough to pass the
#: length check, so it is refused explicitly, in every environment: a copied
#: template must never start an API.
AUTH_SECRET_KEY_PLACEHOLDER_MARKER = "CHANGE_ME"

#: Minimum signing-key length in bytes. Tokens are HMAC-SHA256 (HS256), and
#: RFC 7518 section 3.2 requires an HS256 key of at least the hash output size:
#: 256 bits = 32 bytes. `secrets.token_urlsafe(48)` yields 64 characters.
AUTH_SECRET_KEY_MIN_LENGTH = 32


_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_auth_secret_key(environment: str, raw_key: str | None, api_host: str = "127.0.0.1") -> str:
    """
    Return the signing key to use, or raise `RuntimeError` if it is unsafe.

    Outside development the key must be present, non-empty, not the
    published default, and at least `AUTH_SECRET_KEY_MIN_LENGTH` bytes.
    Explicit development mode may fall back to the built-in key, but only
    while the API binds a loopback address (L4): a development API reachable
    from the network with a published key lets anyone forge an ADMIN token.
    """
    is_development = environment == "development"
    key = (raw_key or "").strip()

    if AUTH_SECRET_KEY_PLACEHOLDER_MARKER in key:
        raise RuntimeError(
            "AUTH_SECRET_KEY is still the .env.example placeholder. Generate a private key with: "
            'python -c "import secrets; print(secrets.token_urlsafe(48))" '
            "(local development: see .env.development.example)."
        )

    if is_development and key in ("", INSECURE_DEFAULT_AUTH_SECRET_KEY) and api_host not in _LOOPBACK_HOSTS:
        raise RuntimeError(
            f"API_HOST='{api_host}' is not a loopback address, and the API would sign tokens with the "
            "published development key. Set AUTH_SECRET_KEY to a private random value, or bind "
            "API_HOST=127.0.0.1."
        )

    if not key:
        if is_development:
            return INSECURE_DEFAULT_AUTH_SECRET_KEY
        state = "missing" if raw_key is None else "empty"
        raise RuntimeError(
            f"AUTH_SECRET_KEY is {state} while APP_ENVIRONMENT='{environment}'. "
            "The API refuses to start without a private signing key. Generate one with: "
            'python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )

    if is_development:
        return key

    if key == INSECURE_DEFAULT_AUTH_SECRET_KEY:
        raise RuntimeError(
            "AUTH_SECRET_KEY is the built-in development key while "
            f"APP_ENVIRONMENT='{environment}'. Access tokens signed with a "
            "publicly known key can be forged for any user and role. Set "
            "AUTH_SECRET_KEY to a private random value."
        )

    if len(key.encode("utf-8")) < AUTH_SECRET_KEY_MIN_LENGTH:
        raise RuntimeError(
            f"AUTH_SECRET_KEY is shorter than {AUTH_SECRET_KEY_MIN_LENGTH} bytes while "
            f"APP_ENVIRONMENT='{environment}'. HS256 requires a key of at least 256 bits."
        )

    return key


# Resolved at import WITHOUT raising: the Streamlit frontend imports this
# module too, but it never signs or verifies tokens and must not need the key.
# Enforcement happens where the key is used - `require_auth_secret_key()` is
# called when the API package loads and when a TokenService is built from
# configuration - so the API refuses to start while other processes do not.
try:
    AUTH_SECRET_KEY = validate_auth_secret_key(APP_ENVIRONMENT, os.getenv("AUTH_SECRET_KEY"), API_HOST)
    AUTH_SECRET_KEY_ERROR: str | None = None
except RuntimeError as _auth_secret_error:
    AUTH_SECRET_KEY = ""
    AUTH_SECRET_KEY_ERROR = str(_auth_secret_error)


def require_auth_secret_key() -> str:
    """Return the configured signing key, or raise if it is unsafe for this environment."""
    if AUTH_SECRET_KEY_ERROR is not None:
        raise RuntimeError(AUTH_SECRET_KEY_ERROR)
    return AUTH_SECRET_KEY


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

#: Issuer / audience claims stamped on and required of every access token.
AUTH_TOKEN_ISSUER = os.getenv("AUTH_TOKEN_ISSUER", "analystgpt-enterprise").strip()
AUTH_TOKEN_AUDIENCE = os.getenv("AUTH_TOKEN_AUDIENCE", "analystgpt-api").strip()

# ----------------------------------------------------------
# Brute-force protection (SEC-08)
# ----------------------------------------------------------
#
# Per-account lockout: after AUTH_LOGIN_MAX_FAILURES consecutive failed logins
# for one identifier, further attempts are refused (HTTP 429) for
# AUTH_LOGIN_LOCKOUT_BASE_SECONDS, doubling with each additional failure up to
# AUTH_LOGIN_LOCKOUT_MAX_SECONDS. Unknown identifiers are throttled the same
# way, so a lockout does not reveal whether an account exists.
#
# Per-client rate limits ("<requests>/<seconds>") on login and registration.
#
# Lockout state is stored in the database (shared by workers). The per-client
# rate limits are in-process: run a single API worker, or each keeps its own.

AUTH_LOGIN_MAX_FAILURES = int(os.getenv("AUTH_LOGIN_MAX_FAILURES", "5"))
AUTH_LOGIN_LOCKOUT_BASE_SECONDS = int(os.getenv("AUTH_LOGIN_LOCKOUT_BASE_SECONDS", "60"))
AUTH_LOGIN_LOCKOUT_MAX_SECONDS = int(os.getenv("AUTH_LOGIN_LOCKOUT_MAX_SECONDS", "900"))

# The per-failure lockout above applies to one account from one client
# address (M12). Across every address, an account only gets a short,
# non-escalating back-off, so nobody can keep its owner locked out. Across
# every account, one address is locked progressively after
# AUTH_LOGIN_SOURCE_MAX_FAILURES failures (password spraying, L5).
AUTH_LOGIN_ACCOUNT_MAX_FAILURES = int(os.getenv("AUTH_LOGIN_ACCOUNT_MAX_FAILURES", "20"))
AUTH_LOGIN_ACCOUNT_LOCKOUT_SECONDS = int(os.getenv("AUTH_LOGIN_ACCOUNT_LOCKOUT_SECONDS", "30"))
AUTH_LOGIN_SOURCE_MAX_FAILURES = int(os.getenv("AUTH_LOGIN_SOURCE_MAX_FAILURES", "30"))

# Peers whose X-Forwarded-For header is believed (M11): comma-separated IPs or
# CIDRs of the Streamlit frontend and any reverse proxy. Everything else is
# identified by its socket address. Without this, every frontend user shared
# the frontend container's address - one rate-limit bucket for everybody.
TRUSTED_PROXY_IPS = os.getenv("TRUSTED_PROXY_IPS", "").strip()

# Public self-registration (M10). Self-registered accounts get the read-only
# VIEWER role; an administrator promotes them with PATCH /api/admin/users/{id}.
# Set to false to accept only accounts created by an administrator.
AUTH_SELF_REGISTRATION_ENABLED = _env_flag("AUTH_SELF_REGISTRATION_ENABLED", default=True)

AUTH_RATE_LIMIT_ENABLED = _env_flag("AUTH_RATE_LIMIT_ENABLED", default=True)
AUTH_LOGIN_RATE_LIMIT = os.getenv("AUTH_LOGIN_RATE_LIMIT", "20/60").strip()
AUTH_REGISTER_RATE_LIMIT = os.getenv("AUTH_REGISTER_RATE_LIMIT", "5/600").strip()

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

# Raw LLM responses in the log (L9). Off: they can repeat dataset values.
# When on, they are logged at DEBUG with newlines escaped.
LOG_LLM_RESPONSES = _env_flag("LOG_LLM_RESPONSES", default=False)

# Upper bound on any access token's lifetime (I2). Tokens are stateless, so
# this caps how long a leaked token stays usable; AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
# above it is clamped.
AUTH_TOKEN_MAX_LIFETIME_MINUTES = int(os.getenv("AUTH_TOKEN_MAX_LIFETIME_MINUTES", "720"))

AUTH_PASSWORD_MIN_LENGTH = int(
    os.getenv(
        "AUTH_PASSWORD_MIN_LENGTH",
        "8",
    )
)
