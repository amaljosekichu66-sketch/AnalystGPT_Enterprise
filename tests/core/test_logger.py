"""
Unit tests for the centralized logging subsystem.

Tests cover:
- Default logger configuration
- Log severity levels
- Console stream handler behavior
- File logging enablement and disablement
- Automatic directory creation
- Log message formatting
- Size-based log rotation (RotatingFileHandler)
- Maximum backup file retention (backupCount)
- Handler duplication protection on repeated configuration
- Clean state restoration
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from src.core import config
from src.core import logger as logger_module
from src.core.constants import LOGGER_NAME
from src.core.logger import configure_logger, logger


@pytest.fixture(autouse=True)
def _restore_default_logger():
    """Ensure the global logger is restored to default configuration after each test."""
    yield
    configure_logger()


def _get_app_handlers(log: logging.Logger) -> list[logging.Handler]:
    """Filter out pytest internal log capture handlers."""
    return [h for h in log.handlers if not type(h).__name__.startswith(("_LiveLogging", "LogCapture", "_FileHandler"))]


# ==========================================================
# Default Configuration & Properties
# ==========================================================


def test_default_logger_properties() -> None:
    """Verify default logger instance properties and handler setup."""
    test_logger = configure_logger(log_to_file=False)
    assert test_logger.name == LOGGER_NAME
    assert test_logger.level == config.LOG_LEVEL
    assert test_logger.propagate is False

    app_handlers = _get_app_handlers(test_logger)
    assert len(app_handlers) == 1
    assert isinstance(app_handlers[0], logging.StreamHandler)
    assert not isinstance(app_handlers[0], RotatingFileHandler)


def test_logger_level_filtering() -> None:
    """Verify that logger respects configured severity thresholds."""
    test_logger = configure_logger(level=logging.WARNING, log_to_file=False)

    assert test_logger.isEnabledFor(logging.ERROR) is True
    assert test_logger.isEnabledFor(logging.WARNING) is True
    assert test_logger.isEnabledFor(logging.INFO) is False
    assert test_logger.isEnabledFor(logging.DEBUG) is False


# ==========================================================
# Handler Duplication Protection
# ==========================================================


def test_handler_duplication_protection() -> None:
    """Verify that multiple configure_logger calls do not duplicate handlers."""
    for _ in range(5):
        configured = configure_logger(log_to_file=False)

    app_handlers = _get_app_handlers(configured)
    assert len(app_handlers) == 1
    assert isinstance(app_handlers[0], logging.StreamHandler)


def test_handler_duplication_with_file_logging(tmp_path: Path) -> None:
    """Verify that repeated calls with file logging maintain exactly 2 handlers."""
    log_file = tmp_path / "test.log"

    for _ in range(3):
        configured = configure_logger(
            log_to_file=True,
            log_file_path=log_file,
        )

    app_handlers = _get_app_handlers(configured)
    assert len(app_handlers) == 2
    handler_types = [type(h) for h in app_handlers]
    assert logging.StreamHandler in handler_types
    assert RotatingFileHandler in handler_types


# ==========================================================
# File Logging & Directory Creation
# ==========================================================


def test_file_logging_disabled_by_default(tmp_path: Path) -> None:
    """Verify that disabled file logging does not create any files on disk."""
    log_file = tmp_path / "unused.log"
    test_logger = configure_logger(log_to_file=False, log_file_path=log_file)

    test_logger.info("This should not be written to file.")
    assert not log_file.exists()


def test_file_logging_enabled_writes_records(tmp_path: Path) -> None:
    """Verify that enabling file logging writes formatted log records to disk."""
    log_file = tmp_path / "app.log"
    test_logger = configure_logger(
        log_to_file=True,
        log_file_path=log_file,
    )

    test_message = "Enterprise pipeline initialized successfully."
    test_logger.info(test_message)

    # Flush handlers to ensure content is written
    for handler in test_logger.handlers:
        handler.flush()

    assert log_file.is_file()
    content = log_file.read_text(encoding="utf-8")
    assert test_message in content
    assert "INFO" in content
    assert LOGGER_NAME in content


def test_automatic_log_directory_creation(tmp_path: Path) -> None:
    """Verify that deeply nested log directories are created automatically."""
    nested_log_file = tmp_path / "nested" / "logs" / "production" / "app.log"
    assert not nested_log_file.parent.exists()

    test_logger = configure_logger(
        log_to_file=True,
        log_file_path=nested_log_file,
    )

    test_logger.info("Directory creation verification.")

    for handler in test_logger.handlers:
        handler.flush()

    assert nested_log_file.parent.is_dir()
    assert nested_log_file.is_file()


# ==========================================================
# Size-Based Log Rotation & Retention
# ==========================================================


def test_size_based_log_rotation(tmp_path: Path) -> None:
    """Verify that log files rotate when exceeding configured maxBytes."""
    log_file = tmp_path / "rotating.log"
    max_bytes = 150  # Small size to trigger fast rotation

    test_logger = configure_logger(
        log_to_file=True,
        log_file_path=log_file,
        max_bytes=max_bytes,
        backup_count=3,
    )

    # Write enough lines to exceed max_bytes and force rotation
    for i in range(15):
        test_logger.info(f"Log entry sequence number {i:04d} with padding data.")

    for handler in test_logger.handlers:
        handler.flush()

    assert log_file.is_file()
    rotated_file_1 = tmp_path / "rotating.log.1"
    assert rotated_file_1.is_file()


def test_backup_count_retention_limit(tmp_path: Path) -> None:
    """Verify that total rotated backup files do not exceed backupCount."""
    log_file = tmp_path / "bounded.log"
    max_bytes = 100
    backup_count = 2

    test_logger = configure_logger(
        log_to_file=True,
        log_file_path=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )

    for i in range(40):
        test_logger.info(f"High-frequency log record {i:04d} for capacity testing.")

    for handler in test_logger.handlers:
        handler.flush()

    # Active file and at most backup_count rotated files
    assert log_file.is_file()
    assert (tmp_path / "bounded.log.1").is_file()
    assert (tmp_path / "bounded.log.2").is_file()
    # Should NOT have created backup 3
    assert not (tmp_path / "bounded.log.3").exists()
