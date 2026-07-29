"""
Application dependency providers for AnalystGPT Enterprise.

Responsibilities
----------------
- Provide shared dependencies for API routes.
- Expose a singleton Application instance.

This module intentionally contains no endpoint logic.
"""

from src.application.app import Application
from src.core.logger import logger

# ==========================================================
# Shared Application Instance
# ==========================================================

_application = Application()

logger.info("=" * 80)
logger.info("APPLICATION SINGLETON CREATED")
logger.info("Application ID : %s", id(_application))
logger.info("=" * 80)


def get_application() -> Application:
    """
    Return the shared Application instance.

    A singleton instance is used so that all API routes,
    orchestrators and frontend consumers access the same
    in-memory pipeline state.
    """

    logger.debug(
        "Returning shared Application instance (id=%s)",
        id(_application),
    )

    return _application