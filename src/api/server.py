"""
FastAPI server configuration for AnalystGPT Enterprise.

Responsibilities
----------------
- Create and configure the FastAPI application.
- Register API routers.
- Expose the FastAPI application instance.

Design Principles
-----------------
- Single Responsibility Principle (SRP)
- Loose Coupling
- High Cohesion
- Dependency Inversion

This module intentionally contains NO business logic.
Business operations are delegated to the Application Layer
through the API route modules.
"""

from fastapi import FastAPI

from src.api.exceptions.exception_handlers import (
    register_exception_handlers,
)
from src.api.routes import (
    health_router,
    pipeline_router,
    root_router,
    version_router,
)
from src.api.routes.powerbi import router as powerbi_router  # <-- NEW
from src.core.constants import (
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    API_DOCS_URL,
    API_OPENAPI_URL,
    API_PREFIX,
    API_REDOC_URL,
)

# ==========================================================
# FastAPI Application
# ==========================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url=API_DOCS_URL,
    redoc_url=API_REDOC_URL,
    openapi_url=API_OPENAPI_URL,
)

# ==========================================================
# Exception Handlers
# ==========================================================

register_exception_handlers(app)

# ==========================================================
# Router Registration
# ==========================================================

app.include_router(root_router)

app.include_router(
    health_router,
    prefix=API_PREFIX,
)

app.include_router(
    version_router,
    prefix=API_PREFIX,
)

app.include_router(
    pipeline_router,
    prefix=API_PREFIX,
)

app.include_router(powerbi_router)  # <-- NEW (with or without prefix)