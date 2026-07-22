"""
API package.

Responsibilities
----------------
- Expose the FastAPI application package.
- Export all API routers.

This module intentionally contains no business logic.
"""

from .routes import (
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