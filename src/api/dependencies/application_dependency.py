"""
Application dependency providers for AnalystGPT Enterprise.

Responsibilities
----------------
- Provide shared dependencies for API routes.
- Create and return the Application instance.

This module intentionally contains no endpoint logic.
"""

from src.application.app import Application


def get_application() -> Application:
    """
    Return the application instance.

    This dependency is injected into API routes using
    FastAPI's dependency injection system.
    """
    return Application()