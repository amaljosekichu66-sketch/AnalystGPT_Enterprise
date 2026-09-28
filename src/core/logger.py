"""
Centralized logging configuration for AnalystGPT Enterprise.

Responsibilities:
- Provide unified, structured logging across all system components.
- Configure console (stdout) and optional rotating file handlers.
- Support configurable log levels, rotation size, and backup retention.
- Prevent handler duplication across reloads and multi-module imports.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core import config
from src.core.constants import LOGGER_NAME


def configure_logger(
    name: str = LOGGER_NAME,
    level: int | None = None,
    log_to_file: bool | None = None,
    log_file_path: Path | str | None = None,
    max_bytes: int | None = None,
    backup_count: int | None = None,
    log_format: str | None = None,
) -> logging.Logger:
    """
    Configure and return a centralized logger instance.

    Parameters
    ----------
    name : str
        The logger hierarchy name.
    level : int | None
        Logging severity level (defaults to config.LOG_LEVEL).
    log_to_file : bool | None
        Whether to attach a RotatingFileHandler (defaults to config.LOG_TO_FILE).
    log_file_path : Path | str | None
        Destination log file path (defaults to config.LOG_FILE_PATH).
    max_bytes : int | None
        Maximum file size before rotation in bytes (defaults to config.LOG_MAX_BYTES).
    backup_count : int | None
        Number of rotated backup files to retain (defaults to config.LOG_BACKUP_COUNT).
    log_format : str | None
        Message format string (defaults to config.LOG_FORMAT).

    Returns
    -------
    logging.Logger
        Configured logger instance with single-instance handlers.
    """
    active_logger = logging.getLogger(name)

    target_level = level if level is not None else getattr(config, "LOG_LEVEL", logging.INFO)
    active_logger.setLevel(target_level)
    active_logger.propagate = False

    target_format = log_format or getattr(
        config,
        "LOG_FORMAT",
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    formatter = logging.Formatter(target_format)

    # Remove existing handlers to prevent duplicate logging on re-configuration
    for existing_handler in list(active_logger.handlers):
        existing_handler.close()
        active_logger.removeHandler(existing_handler)

    # 1. Console / Stream Handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(target_level)
    console_handler.setFormatter(formatter)
    active_logger.addHandler(console_handler)

    # 2. Rotating File Handler (optional)
    should_log_to_file = log_to_file if log_to_file is not None else getattr(config, "LOG_TO_FILE", False)

    if should_log_to_file:
        target_path = Path(
            log_file_path
            if log_file_path is not None
            else getattr(
                config,
                "LOG_FILE_PATH",
                config.PROJECT_ROOT / "logs" / "analystgpt.log",
            )
        )
        target_max_bytes = (
            max_bytes
            if max_bytes is not None
            else getattr(
                config,
                "LOG_MAX_BYTES",
                10 * 1024 * 1024,
            )
        )
        target_backup_count = (
            backup_count
            if backup_count is not None
            else getattr(
                config,
                "LOG_BACKUP_COUNT",
                5,
            )
        )

        target_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=str(target_path),
            maxBytes=target_max_bytes,
            backupCount=target_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(target_level)
        file_handler.setFormatter(formatter)
        active_logger.addHandler(file_handler)

    return active_logger


# Default module-level singleton instance for immediate import
logger = configure_logger()
