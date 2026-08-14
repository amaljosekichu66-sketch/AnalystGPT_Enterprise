"""
Unit tests for application configuration management.

Tests cover:
- Default configuration values and types
- Environment variable loading and parsing
- Type conversion (int, float, path, string)
- Validation errors on invalid PostgreSQL configuration
- .env.example completeness and safety
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
import pytest

from src.core import config


@pytest.fixture(autouse=True)
def _restore_config():
    """Ensure config is reloaded in clean state after tests modify environment."""
    yield
    importlib.reload(config)


# ==========================================================
# Default Values & Types
# ==========================================================


def test_config_project_root_exists() -> None:
    """Verify that PROJECT_ROOT is resolved to a valid existing directory."""
    assert config.PROJECT_ROOT.is_dir()
    assert (config.PROJECT_ROOT / "src").is_dir()


def test_config_default_types() -> None:
    """Verify default types of critical configuration constants."""
    assert isinstance(config.MAX_FILE_SIZE_MB, int)
    assert isinstance(config.RESET_INDEX_AFTER_CLEANING, bool)
    assert isinstance(config.DEFAULT_DATATYPE_MAP, dict)
    assert isinstance(config.REPORT_OUTPUT_DIRECTORY, Path)
    assert isinstance(config.DEFAULT_REPORT_FILENAME, str)
    assert isinstance(config.SQLITE_DATABASE_PATH, Path)
    assert isinstance(config.AI_TEMPERATURE, float)
    assert isinstance(config.AI_TOP_P, float)
    assert isinstance(config.AI_MAX_TOKENS, int)
    assert isinstance(config.AI_CONTEXT_WINDOW, int)
    assert isinstance(config.AI_TIMEOUT, float)
    assert isinstance(config.AI_MAX_RETRIES, int)
    assert isinstance(config.API_PORT, int)
    assert isinstance(config.FRONTEND_PORT, int)
    assert isinstance(config.API_HOST, str)
    assert isinstance(config.API_BASE_URL, str)


def test_config_ai_hyperparameter_bounds() -> None:
    """Verify default AI parameters fall within valid operating bounds."""
    assert 0.0 <= config.AI_TEMPERATURE <= 1.0
    assert 0.0 <= config.AI_TOP_P <= 1.0
    assert config.AI_MAX_TOKENS > 0
    assert config.AI_CONTEXT_WINDOW > 0
    assert config.AI_TIMEOUT > 0
    assert config.AI_MAX_RETRIES >= 0


# ==========================================================
# Dynamic Environment Variable Loading
# ==========================================================


def test_config_logging_defaults() -> None:
    """Verify logging default configuration values and types."""
    assert isinstance(config.LOG_LEVEL, int)
    assert isinstance(config.LOG_TO_FILE, bool)
    assert isinstance(config.LOG_FILE_PATH, Path)
    assert isinstance(config.LOG_MAX_BYTES, int)
    assert isinstance(config.LOG_BACKUP_COUNT, int)
    assert config.LOG_MAX_BYTES > 0
    assert config.LOG_BACKUP_COUNT >= 0


def test_config_logging_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that logging environment variables parse correctly."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_TO_FILE", "true")
    monkeypatch.setenv("LOG_FILE_PATH", "/tmp/custom.log")
    monkeypatch.setenv("LOG_MAX_BYTES", "5242880")
    monkeypatch.setenv("LOG_BACKUP_COUNT", "10")

    reloaded = importlib.reload(config)
    assert reloaded.LOG_LEVEL == logging.DEBUG
    assert reloaded.LOG_TO_FILE is True
    assert reloaded.LOG_FILE_PATH == Path("/tmp/custom.log")
    assert reloaded.LOG_MAX_BYTES == 5242880
    assert reloaded.LOG_BACKUP_COUNT == 10


def test_config_networking_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that networking parameters parse custom environment values."""
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("API_BASE_URL", "http://backend:9000")
    monkeypatch.setenv("FRONTEND_PORT", "9501")

    reloaded = importlib.reload(config)
    assert reloaded.API_HOST == "127.0.0.1"
    assert reloaded.API_PORT == 9000
    assert reloaded.API_BASE_URL == "http://backend:9000"
    assert reloaded.FRONTEND_PORT == 9501


def test_config_postgres_missing_password_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that PostgreSQL engine without password raises RuntimeError."""
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("DATABASE_ENGINE", "postgresql")
    monkeypatch.setenv("POSTGRES_PASSWORD", "")

    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        importlib.reload(config)


def test_config_postgres_with_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that PostgreSQL engine with password reloads successfully."""
    monkeypatch.setenv("DATABASE_ENGINE", "postgresql")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_mock_password")

    reloaded = importlib.reload(config)
    assert reloaded.DATABASE_ENGINE == "postgresql"
    assert reloaded.POSTGRES_PASSWORD == "test_mock_password"


def test_config_sqlite_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that SQLite engine operates without requiring PostgreSQL credentials."""
    monkeypatch.setenv("DATABASE_ENGINE", "sqlite")
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    reloaded = importlib.reload(config)
    assert reloaded.DATABASE_ENGINE == "sqlite"


# ==========================================================
# .env.example Validation
# ==========================================================


def test_env_example_file_exists() -> None:
    """Verify that .env.example exists in the project root."""
    example_path = config.PROJECT_ROOT / ".env.example"
    assert example_path.is_file()


def test_env_example_contains_all_variables() -> None:
    """Verify that .env.example documents all expected configuration keys."""
    example_path = config.PROJECT_ROOT / ".env.example"
    content = example_path.read_text(encoding="utf-8")

    expected_keys = [
        "LOG_LEVEL",
        "LOG_TO_FILE",
        "LOG_FILE_PATH",
        "LOG_MAX_BYTES",
        "LOG_BACKUP_COUNT",
        "API_HOST",
        "API_PORT",
        "API_BASE_URL",
        "FRONTEND_PORT",
        "DATABASE_ENGINE",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DATABASE",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "LLM_PROVIDER",
        "OLLAMA_HOST",
        "OLLAMA_MODEL",
        "OLLAMA_KEEP_ALIVE",
        "AI_TEMPERATURE",
        "AI_TOP_P",
        "AI_MAX_TOKENS",
        "AI_CONTEXT_WINDOW",
        "AI_TIMEOUT",
        "AI_MAX_RETRIES",
    ]

    for key in expected_keys:
        assert f"{key}=" in content, f"Key '{key}' missing from .env.example"


def test_env_example_has_no_secrets() -> None:
    """Verify that .env.example contains placeholder values rather than real credentials."""
    example_path = config.PROJECT_ROOT / ".env.example"
    content = example_path.read_text(encoding="utf-8")

    # Check for placeholder password
    assert "your_secure_password_here" in content
