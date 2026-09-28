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
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.governance import router as governance_router
from src.api.routes.powerbi import router as powerbi_router
from src.api.routes.reports import router as reports_router
from src.core import config
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

    Shutdown drains the AI subsystem. `AIJobExecutor` wraps a
    `ThreadPoolExecutor` whose workers are NON-daemon, and `concurrent.futures`
    installs an atexit hook that joins them at interpreter shutdown. Without an
    explicit drain the server process blocks on exit until every in-flight AI
    job finishes - up to `AI_TIMEOUT` each, which is minutes on CPU inference -
    and outstanding retry timers can still resubmit work into a pool that is
    supposed to be closing.

    `Application.shutdown()` deliberately passes `wait=False`: a job already
    talking to the model is left to finish rather than being abandoned
    mid-generation with its row stuck in GENERATING. What it stops is *new*
    work - further submissions and pending retries.
    """

    logger.info("Starting AnalystGPT Enterprise API...")

    yield

    logger.info("Stopping AnalystGPT Enterprise API...")

    # Imported here rather than at module scope: importing the dependency
    # module constructs the Application singleton as a side effect, and that
    # must stay owned by the dependency layer.
    from src.api.dependencies.application_dependency import get_application

    try:
        get_application().shutdown()
        logger.info("AI subsystem drained.")
    except Exception:
        # A failure to drain must not mask the real reason the server is
        # stopping, but it must not be silent either.
        logger.exception("Failed to drain the AI subsystem during API shutdown.")


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

# `allow_origins=["*"]` with `allow_credentials=True` is not a wildcard policy.
# Starlette cannot emit `Access-Control-Allow-Origin: *` alongside credentials,
# so it reflects the caller's Origin instead - turning every website into a
# credentialed origin. The allow-list is explicit and configurable via
# CORS_ALLOWED_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
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

    logger.info("Registering API routers...")

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
        prefix=API_PREFIX,
        tags=["Dashboard"],
    )

    # Every functional router is mounted under API_PREFIX.
    #
    # `/reports/*`, `/powerbi/*` and the dashboard router used to answer on
    # unprefixed paths as well - `/reports/*` on both. Those aliases were
    # deprecated once the frontend moved onto `/api`, and are now removed.
    # This is a BREAKING change for any external caller still using them;
    # every path has an identical `/api`-prefixed equivalent.
    application.include_router(
        reports_router,
        prefix=API_PREFIX,
        tags=["Reports"],
    )

    application.include_router(
        powerbi_router,
        prefix=API_PREFIX,
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


logger.info("FastAPI server initialized successfully.")
