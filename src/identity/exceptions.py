"""
Identity and security exceptions for AnalystGPT Enterprise.

These exceptions represent domain-level authentication and authorization
failures within the enterprise identity subsystem.
"""

from __future__ import annotations

from src.core.exceptions import AnalystGPTError

# ==========================================================
# Base Identity Exception
# ==========================================================


class IdentityError(AnalystGPTError):
    """
    Base exception for all identity, authentication, and authorization errors.
    """

    pass


# ==========================================================
# Authentication Exceptions
# ==========================================================


class AuthenticationError(IdentityError):
    """
    Raised when user authentication fails.
    """

    pass


class InvalidCredentialsError(AuthenticationError):
    """
    Raised when provided login credentials (username/password) are invalid.
    """

    pass


class InvalidTokenError(AuthenticationError):
    """
    Raised when an authentication token is malformed, expired, or invalid.
    """

    pass


class UserDisabledError(AuthenticationError):
    """
    Raised when an inactive or suspended user attempts to authenticate.
    """

    pass


# ==========================================================
# User Lifecycle & Domain Exceptions
# ==========================================================


class UserNotFoundError(IdentityError):
    """
    Raised when a requested user entity does not exist.
    """

    pass


class UserAlreadyExistsError(IdentityError):
    """
    Raised when attempting to create a user with an existing username or email.
    """

    pass


# ==========================================================
# Authorization Exceptions
# ==========================================================


class AuthorizationError(IdentityError):
    """
    Raised when an authenticated user lacks permission to perform an action.
    """

    pass


class PermissionDeniedError(AuthorizationError):
    """
    Raised when a user lacks a specific required permission or role.
    """

    pass


class AdminOperationError(IdentityError):
    """
    Raised when an administrative operation violates safety guards (e.g. last admin protection).
    """

    pass
