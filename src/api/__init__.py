"""
API package.

Responsibilities
----------------
- Expose the FastAPI application package.
- Export all API routers.

This module intentionally contains no business logic.
"""

from src.core import config as _config

# Refuse to start the API with a missing, empty, short or published signing
# key. This runs before any router (and the Application singleton) loads.
_config.require_auth_secret_key()

if _config.AUTH_SECRET_KEY == _config.INSECURE_DEFAULT_AUTH_SECRET_KEY:
    # Allowed only in development on loopback (L4), but never silently.
    from src.core.logger import logger as _logger

    _logger.warning(
        "SECURITY_ALERT | Access tokens are signed with the PUBLISHED development key. "
        "Anyone who can reach this API can forge an ADMIN token. Set AUTH_SECRET_KEY."
    )

from .routes import (  # noqa: E402
    health_router,
    pipeline_router,
    root_router,
    version_router,
)

__all__ = [
    "root_router",
    "health_router",
    "version_router",
    "pipeline_router",
]
