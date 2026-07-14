"""
Centralized logging configuration for AnalystGPT Enterprise.
"""

import logging

from core.config import LOG_LEVEL

logger = logging.getLogger("AnalystGPT")
logger.setLevel(LOG_LEVEL)

handler = logging.StreamHandler()

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)

logger.propagate = False