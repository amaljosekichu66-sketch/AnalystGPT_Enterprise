"""
Custom exceptions used throughout AnalystGPT Enterprise.

Each business module should derive its own exceptions
from AnalystGPTError.
"""


# ==========================================================
# Base Exception
# ==========================================================

class AnalystGPTError(Exception):
    """
    Base exception for AnalystGPT Enterprise.
    """
    pass


# ==========================================================
# Upload Exceptions
# ==========================================================

class UnsupportedFileTypeError(AnalystGPTError):
    """
    Raised when an unsupported file type is uploaded.
    """
    pass


class FileReadError(AnalystGPTError):
    """
    Raised when a supported file cannot be read.
    """
    pass


class SourceFileNotFoundError(AnalystGPTError):
    """
    Raised when the specified source file does not exist.
    """
    pass


class FileTooLargeError(AnalystGPTError):
    """
    Raised when the uploaded file exceeds the configured size limit.
    """
    pass


# ==========================================================
# Identity & Security Exceptions (Sprint 13)
# ==========================================================

class IdentityError(AnalystGPTError):
    """Base exception for all identity, authentication, and authorization errors."""
    pass


class AuthenticationError(IdentityError):
    """Raised when user authentication fails."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when an authentication token is malformed, expired, or invalid."""
    pass


class UserDisabledError(AuthenticationError):
    """Raised when an inactive or suspended user attempts to authenticate."""
    pass


class UserNotFoundError(IdentityError):
    """Raised when a requested user entity does not exist."""
    pass


class UserAlreadyExistsError(IdentityError):
    """Raised when attempting to create a user with an existing username or email."""
    pass


class AuthorizationError(IdentityError):
    """Raised when an authenticated user lacks permission to perform an action."""
    pass


class PermissionDeniedError(AuthorizationError):
    """Raised when a user lacks a specific required permission or role."""
    pass