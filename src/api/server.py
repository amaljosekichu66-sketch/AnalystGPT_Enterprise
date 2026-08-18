"""
FastAPI server configuration for AnalystGPT Enterprise.

Responsibilities
----------------
- Configure the FastAPI application.
- Register middleware.
- Register exception handlers.
- Register API routers.
- Configure application lifespan.

Sprint 11
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exceptions.exception_handlers import (
    register_exception_handlers,
)

from src.api.routes import (
    admin_router,
    ai_router,
    auth_router,
    health_router,
    pipeline_router,
    root_router,
    version_router,
)

from src.api.routes.dashboard import (
    router as dashboard_router,
)

from src.api.routes.powerbi import (
    router as powerbi_router,
)

from src.api.routes.reports import (
    router as reports_router,
)

from src.api.routes.governance import (
    router as governance_router,
)

from src.core.constants import (
    API_DOCS_URL,
    API_OPENAPI_URL,
    API_PREFIX,
    API_REDOC_URL,
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
)

from src.core.logger import logger


# ==========================================================
# Application Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Startup / Shutdown lifecycle.
    """

    logger.info(
        "Starting AnalystGPT Enterprise API..."
    )

    yield

    logger.info(
        "Stopping AnalystGPT Enterprise API..."
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
    lifespan=lifespan,
    contact={
        "name": "Amal Jose",
    },
    license_info={
        "name": "MIT",
    },
)


# ==========================================================
# Middleware
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# Exception Handlers
# ==========================================================

register_exception_handlers(
    app,
)


# ==========================================================
# Router Registration
# ==========================================================

def register_routes(
    application: FastAPI,
) -> None:
    """
    Register all API routers.
    """

    logger.info(
        "Registering API routers..."
    )

    application.include_router(
        root_router,
        tags=["Root"],
    )

    application.include_router(
        health_router,
        prefix=API_PREFIX,
        tags=["Health"],
    )

    application.include_router(
        version_router,
        prefix=API_PREFIX,
        tags=["Version"],
    )

    application.include_router(
        auth_router,
        prefix=API_PREFIX,
        tags=["Authentication"],
    )

    application.include_router(
        admin_router,
        prefix=API_PREFIX,
        tags=["Administration"],
    )

    application.include_router(
        pipeline_router,
        prefix=API_PREFIX,
        tags=["Pipeline"],
    )

    application.include_router(
        dashboard_router,
        tags=["Dashboard"],
    )

    application.include_router(
        reports_router,
        tags=["Reports"],
    )

    application.include_router(
        reports_router,
        prefix=API_PREFIX,
        tags=["Reports"],
    )

    application.include_router(
        powerbi_router,
        tags=["Power BI"],
    )

    application.include_router(
        ai_router,
        prefix=API_PREFIX,
        tags=["AI Insights"],
    )

    application.include_router(
        governance_router,
        prefix=API_PREFIX,
        tags=["Governance"],
    )


register_routes(app)


logger.info(
    "FastAPI server initialized successfully."
)