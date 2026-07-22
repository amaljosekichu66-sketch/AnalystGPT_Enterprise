"""
API route package.

Responsibilities
----------------
- Expose all API routers.
- Provide a single public interface for route imports.

This module intentionally contains no endpoint logic.
"""

from .health import router as health_router
from .pipeline import router as pipeline_router
from .root import router as root_router
from .version import router as version_router

__all__ = [
    "root_router",
    "health_router",
    "version_router",
    "pipeline_router",
]