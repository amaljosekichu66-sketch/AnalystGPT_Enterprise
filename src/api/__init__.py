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
